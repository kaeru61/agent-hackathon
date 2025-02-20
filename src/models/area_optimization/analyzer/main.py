import json
import geopandas as gpd
from shapely.geometry import shape
from geopy.distance import geodesic

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

    def calculate_farm_statistics(self, farmer_id):
        """特定の農家の農地の統計情報を計算する"""
        if farmer_id not in self.farmlands:
            return {}
        plots = self.farmlands[farmer_id]
        # 統計情報の計算ロジックをここに追加
        stats = {
            "total_area": sum(plot.area for plot in plots),
            "num_plots": len(plots)
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

if __name__ == "__main__":
    analyzer = ResourceAnalyzer("../data/processed/merged_geojson/merged_polygon_with_farm_pin.geojson")
    farmer_id = list(analyzer.farmlands.keys())[0] # 1つ目の農家のIDを取得
    farm_stats, resource_requirements = analyzer.run_analysis(farmer_id)

    print("農地統計情報:")
    print(json.dumps(farm_stats, indent=2, ensure_ascii=False))

    print("\n必要な人的リソース:")
    print(json.dumps(resource_requirements, indent=2, ensure_ascii=False))
