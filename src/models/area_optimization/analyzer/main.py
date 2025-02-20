import json
import geopandas as gpd
from shapely.geometry import shape
from geopy.distance import geodesic
from pyproj import Geod
import tqdm

class ResourceAnalyzer:
    def __init__(self, geojson_path):
        self.geojson_path = geojson_path
        self.farmlands = self.load_data()

    def load_data(self):
        """GeoJSONデータを読み込み、FarmerIndicationNumberHashごとに農地をまとめる"""
        gdf = gpd.read_file(self.geojson_path)
        farms = {}
        for _, row in gdf.iterrows():
            farmer_id = row['FarmerIndicationNumberHash'] if row['FarmerIndicationNumberHash'] is not None else 'unknown'
            geometry = row['geometry']

            if farmer_id not in farms:
                farms[farmer_id] = []
            farms[farmer_id].append(geometry)
        print(f"Loaded {len(farms)} farmers' farmlands")
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

    def estimate_human_resources(self, stats, period_months=12):
        """人的リソースの見積もりを計算する"""
        base_rate = 0.1  # 基本レート（仮定）
        total_area = stats.get("total_area", 0)
        yearly_person_months = total_area * base_rate
        period_person_months = yearly_person_months * (period_months / 12)
        return period_person_months

    def run_analysis(self, farmer_id):
        """特定の農家に対して全体の分析を実行する"""
        stats = self.calculate_farm_statistics(farmer_id)
        resources = self.estimate_human_resources(stats)
        return stats, resources

    def run_total_analysis(self):
        """地域全体のリソースシミュレーションを実行する"""
        total_stats = {"total_area": 0, "num_plots": 0, "num_large_plots": 0}
        total_resources = 0
        for farmer_id in tqdm.tqdm(self.farmlands.keys()):
            stats, resources = self.run_analysis(farmer_id)
            total_stats["num_plots"] += stats.get("num_plots", 0)
            total_stats["total_area"] += stats.get("total_area", 0)
            total_stats["num_large_plots"] += stats.get("num_large_plots", 0)
            total_resources += resources
        return total_stats, total_resources

if __name__ == "__main__":
    analyzer = ResourceAnalyzer("../data/processed/merged_geojson/filtered_merged_polygon_with_farm_pin.geojson")

    # 個々の農家のリソースシミュレーション
    farmer_id = list(analyzer.farmlands.keys())[0]  # 1つ目の農家のIDを取得
    farm_stats, resource_requirements = analyzer.run_analysis(farmer_id)
    print(f"農家ID: {farmer_id}, 農地数: {farm_stats.get('num_plots', 0)}")
    print("農地統計情報:")
    print(json.dumps(farm_stats, indent=2, ensure_ascii=False))
    print("\n必要な人的リソース:")
    print(json.dumps(resource_requirements, indent=2, ensure_ascii=False))

    # 地域全体のリソースシミュレーション
    total_stats, total_resources = analyzer.run_total_analysis()
    print("\n地域全体の農地統計情報:")
    print(json.dumps(total_stats, indent=2, ensure_ascii=False))
    print("\n地域全体の必要な人的リソース:")
    print(json.dumps(total_resources, indent=2, ensure_ascii=False))
