import json
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from pyproj import Geod
import tqdm
from dataclasses import dataclass
from typing import Dict
import random
from geopy.distance import geodesic


@dataclass
class AnalysisResult:
    """最適化による1ヶ月分の削減コスト
    Attributes:
        total_distance_reduced (float): 移動距離の削減量（km）
        total_co2_reduced (float): CO2排出量の削減量（kg）
        farmers_worktime_reduced (Dict[str, float]): 農家ごとの労働時間の削減量（h）
        farmers_fuel_cost_reduced (Dict[str, float]): 農家ごとの燃料費の削減量（円）
    """
    total_distance_reduced: float
    total_co2_reduced: float
    farmers_worktime_reduced: Dict[str, float]
    farmers_fuel_cost_reduced: Dict[str, float]

def run_analysis(geojson_path: str, existing_farmer_ids: list[str]) -> AnalysisResult:
    analyzer = ResourceAnalyzer(geojson_path)
    total_stats, total_distance = analyzer.run_total_analysis()
    total_co2_reduced = total_distance * 0.28  # 軽トラのCO2排出量は1kmあたり0.28kg

    farmers_worktime_reduced = {}
    farmers_fuel_cost_reduced = {}
    for farmer_id in existing_farmer_ids:
        stats, travel_distance = analyzer.run_analysis(farmer_id)
        worktime_reduced = travel_distance / 20 # 時速20kmで走行
        fuel_cost_reduced = travel_distance * 12.3 # 1kmあたり12.3円の燃料費
        farmers_worktime_reduced[farmer_id] = worktime_reduced
        farmers_fuel_cost_reduced[farmer_id] = fuel_cost_reduced

    return AnalysisResult(
        total_distance_reduced=total_distance,
        total_co2_reduced=total_co2_reduced,
        farmers_worktime_reduced=farmers_worktime_reduced,
        farmers_fuel_cost_reduced=farmers_fuel_cost_reduced
    )



class ResourceAnalyzer:
    def __init__(self, geojson_path):
        self.geojson_path = geojson_path
        self.farmlands = self.load_data()

    def load_data(self) -> dict[str, list[gpd.GeoSeries]]:
        """GeoJSONデータを読み込み、FarmerIndicationNumberHashごとに農地をまとめる
        Returns:
            dict: FarmerIndicationNumberHashをキーとし、その農地のリストを値とする辞書
        """
        gdf = gpd.read_file(self.geojson_path)
        farms = {}
        for _, row in gdf.iterrows():
            farmer_id = row['FarmerIndicationNumberHash'] if row['FarmerIndicationNumberHash'] is not None else 'unknown'
            geometry = row['geometry']

            if farmer_id not in farms:
                farms[farmer_id] = []
            farms[farmer_id].append(geometry)
        return farms

    def calculate_area(self, polygon):
        """ポリゴンの面積を計算する（球面積分を使用）"""
        geod = Geod(ellps="WGS84")
        lon, lat = polygon.exterior.coords.xy
        return abs(geod.polygon_area_perimeter(lon, lat)[0]) # 単位は平方メートル


    def calculate_farm_statistics(self, farmer_id):
        """特定の農家の農地の統計情報を計算する"""
        if farmer_id not in self.farmlands:
            print(f"Farmer ID {farmer_id} not found in dataset.")
            return {}
        plots = self.farmlands[farmer_id]
        # 統計情報の計算ロジックをここに追加
        areas = [self.calculate_area(plot) for plot in plots]
        stats = {
            "num_plots": len(plots), # 農地数
            "total_area": sum(areas), # 総面積(m^2)
            "num_large_plots": len([a for a in areas if a > 1000]), # 1000m^2以上の農地数
        }
        return stats

    def distance_matrix(self, farms):
        """農地間の距離行列を計算する"""
        num = len(farms)
        dist_matrix = np.zeros((num, num))
        centroids = [farm.centroid for farm in farms]
        for i in range(num):
            for j in range(num):
                if i != j:
                    dist_matrix[i, j] = geodesic((centroids[i].y, centroids[i].x), (centroids[j].y, centroids[j].x)).meters
        return dist_matrix

    def greedy_tsp(self, dist_matrix: np.ndarray) -> list[int]:
        """グリーディ法で初期経路を生成"""
        num = len(dist_matrix)
        visited = [False] * num
        path = [0]
        visited[0] = True
        for _ in range(num - 1):
            last = path[-1]
            next_city = np.argmin([dist_matrix[last, j] if not visited[j] else np.inf for j in range(num)])
            path.append(next_city)
            visited[next_city] = True
        return path

    def simulated_annealing(self, dist_matrix, initial_path, temp=1000.0, cooling_rate=0.995, max_iter=1000):
        """焼きなまし法で経路を最適化"""
        def calculate_total_distance(path):
            return sum(dist_matrix[path[i], path[i + 1]] for i in range(len(path) - 1)) + dist_matrix[path[-1], path[0]]

        current_path = initial_path
        current_distance = calculate_total_distance(current_path)
        best_path = list(current_path)
        best_distance = current_distance

        for _ in range(max_iter):
            temp *= cooling_rate
            if temp <= 0.1:
                break

            # 2-opt swap
            if len(current_path) > 2:
                i, j = sorted(random.sample(range(1, len(current_path)), 2))
                new_path = current_path[:i] + current_path[i:j][::-1] + current_path[j:]
                new_distance = calculate_total_distance(new_path)

                if new_distance < current_distance or random.random() < np.exp((current_distance - new_distance) / temp):
                    current_path = new_path
                    current_distance = new_distance

                    if current_distance < best_distance:
                        best_path = list(current_path)
                        best_distance = current_distance
        # print(best_path)

        return best_path, best_distance

    def calculate_travel_distance(self, farms):
        """農地間の移動距離を計算する"""
        dist_matrix = self.distance_matrix(farms)
        initial_path = self.greedy_tsp(dist_matrix)
        best_path, best_distance = self.simulated_annealing(dist_matrix, initial_path)
        return best_distance/1000  # km


    def run_analysis(self, farmer_id):
        """特定の農家に対して全体の分析を実行する"""
        stats = self.calculate_farm_statistics(farmer_id)
        farms = self.farmlands[farmer_id]
        travel_distance = self.calculate_travel_distance(farms)
        travel_distance *= 2.5 # 1日に農地を平均2.5周する
        travel_distance *= 30 # 1ヶ月分の移動距離
        return stats, travel_distance

    def run_total_analysis(self):
        """地域全体のリソースシミュレーションを実行する"""
        total_stats = {"total_area": 0, "num_plots": 0, "num_large_plots": 0}
        total_travel_distance = 0
        for farmer_id in tqdm.tqdm(self.farmlands.keys()):
            stats, travel_distance = self.run_analysis(farmer_id)
            total_stats["num_plots"] += stats.get("num_plots", 0)
            total_stats["total_area"] += stats.get("total_area", 0)
            total_stats["num_large_plots"] += stats.get("num_large_plots", 0)
            total_travel_distance += travel_distance
        return total_stats, total_travel_distance


if __name__ == "__main__":
    # 最適化前のリソースシミュレーション
    test_geojson_path = "../../notebooks/data/geojson_filtered_by_settlement/筑地.geojson"
    existing_farmer_ids = ["2dacba93d45b0f46a25b29b985bd90e2", "10aad9b486abee43973bb555cc3362c2", "7db8af145bda49552f855ba395906a2f"]
    result = run_analysis(test_geojson_path, existing_farmer_ids)
    print("最適化前のリソースシミュレーション結果:")
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
    print("\n")
