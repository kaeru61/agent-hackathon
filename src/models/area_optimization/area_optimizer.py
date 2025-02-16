import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union

class FudePolygonProcessor:
    def __init__(self, input_file: str, output_file: str):
        """
        筆ポリゴンの前処理クラス

        Args:
            input_file (str): 入力ShapefileまたはGeoJSONのパス
            output_file (str): 出力ファイル（GeoJSON）
        """
        self.input_file = input_file
        self.output_file = output_file
        self.gdf = None

    def load_data(self):
        """データを読み込む"""
        print("📥 データを読み込み中...")
        self.gdf = gpd.read_file(self.input_file)

    def filter_land_use(self):
        """田・畑以外の地目データを削除"""
        print("🧹 非農地データを削除...")
        if 'land_use' in self.gdf.columns:
            self.gdf = self.gdf[self.gdf['land_use'].isin(['田', '畑'])]

    def remove_small_polygons(self, min_area=1):
        """極小ポリゴンを削除（デフォルトは1㎡未満）"""
        print("⚖️ 極小ポリゴンを削除...")
        self.gdf = self.gdf[self.gdf.geometry.area > min_area]

    def merge_adjacent_polygons(self):
        """同じ所有者の隣接ポリゴンを統合"""
        print("🔗 隣接ポリゴンを統合...")
        if 'owner_id' in self.gdf.columns:
            merged_polygons = []
            owners = self.gdf['owner_id'].unique()

            for owner in owners:
                owner_polygons = self.gdf[self.gdf['owner_id'] == owner]
                merged_geom = unary_union(owner_polygons.geometry)  # 隣接ポリゴンを統合
                merged_polygons.append({'owner_id': owner, 'geometry': merged_geom})

            self.gdf = gpd.GeoDataFrame(merged_polygons, crs=self.gdf.crs)

    def normalize_shape(self):
        """形状を正規化（長方形近似）"""
        print("📏 形状の正規化（長方形近似）...")
        self.gdf['geometry'] = self.gdf['geometry'].apply(lambda geom: geom.minimum_rotated_rectangle)

    def save_data(self):
        """処理後データを保存"""
        print("💾 データを保存中...")
        self.gdf.to_file(self.output_file, driver="GeoJSON")
        print("✅ 前処理完了！ファイルを保存しました:", self.output_file)

    def process(self):
        """一連の処理を実行"""
        self.load_data()
        self.filter_land_use()
        self.remove_small_polygons()
        self.merge_adjacent_polygons()
        self.normalize_shape()
        self.save_data()

# 実行例
processor = FudePolygonProcessor("fudepolygon.shp", "processed_fudepolygon.geojson")
processor.process()
