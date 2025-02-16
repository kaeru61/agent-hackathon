import os
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

class FudePolygonProcessor:
    def __init__(self, input_file: str, output_file: str):
        """
        筆ポリゴンの前処理クラス（JSON形式対応）

        Args:
            input_file (str): 入力JSON（GeoJSONまたは通常のJSON）
            output_file (str): 処理後の出力ファイル（GeoJSON）
        """
        self.input_file = input_file
        self.output_file = output_file
        self.gdf = None

    def load_data(self):
        """JSONデータをGeoDataFrameに変換"""
        print("📥 データを読み込み中...")

        try:
            # GeoJSONとして直接読み込む
            self.gdf = gpd.read_file(self.input_file)
            print("✅ GeoJSONデータを読み込みました")
        except:
            # 通常のJSONの場合
            with open(self.input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # GeoJSON形式の場合
            if "features" in data:
                features = data["features"]
                df = pd.DataFrame([{
                    "polygon_uuid": feature["properties"].get("polygon_uuid"),
                    "land_type": feature["properties"].get("land_type"),
                    "issue_year": feature["properties"].get("issue_year"),
                    "edit_year": feature["properties"].get("edit_year"),
                    "history": feature["properties"].get("history"),
                    "last_polygon_uuid": feature["properties"].get("last_polygon_uuid"),
                    "prev_last_polygon_uuid": feature["properties"].get("prev_last_polygon_uuid"),
                    "local_government_cd": feature["properties"].get("local_government_cd"),
                    "point_lng": feature["properties"].get("point_lng"),
                    "point_lat": feature["properties"].get("point_lat"),
                    "geometry": shape(feature["geometry"])  # ShapelyのPolygonに変換
                } for feature in features])

                self.gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:6668")
                print("✅ 通常JSON（GeoJSON構造）を変換しました")
            else:
                raise ValueError("❌ 不明なJSONフォーマットです")

    def filter_land_use(self):
        """田・畑以外の地目データを削除"""
        print("🧹 非農地データを削除...")
        if 'land_type' in self.gdf.columns:
            self.gdf = self.gdf[self.gdf['land_type'].isin([100, 200])]

    def remove_small_polygons(self, min_area=1):
        """極小ポリゴンを削除（デフォルトは1㎡未満）"""
        print("⚖️ 極小ポリゴンを削除...")
        self.gdf = self.gdf.to_crs(epsg=3857)  # Re-project to a projected CRS
        self.gdf = self.gdf[self.gdf.geometry.area > min_area]

    def merge_adjacent_polygons(self):
        """同じ所有者の隣接ポリゴンを統合"""
        print("🔗 隣接ポリゴンを統合...")
        if 'polygon_uuid' in self.gdf.columns:
            merged_polygons = []
            polygons = self.gdf['polygon_uuid'].unique()

            for polygon in polygons:
                polygon_data = self.gdf[self.gdf['polygon_uuid'] == polygon]
                merged_geom = unary_union(polygon_data.geometry)  # 隣接ポリゴンを統合
                merged_polygons.append({'polygon_uuid': polygon, 'geometry': merged_geom})

            self.gdf = gpd.GeoDataFrame(merged_polygons, geometry='geometry', crs=self.gdf.crs)

    def normalize_shape(self):
        """形状を正規化（長方形近似）"""
        print("📏 形状の正規化（長方形近似）...")
        self.gdf['geometry'] = self.gdf['geometry'].apply(lambda geom: geom.minimum_rotated_rectangle)

    def save_data(self):
        """処理後データを保存"""
        print("💾 データを保存中...")
        output_dir = os.path.dirname(self.output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
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
input_path = "../../data/raw/fude_polygon/2024_08/2024_082015.json"
output_path = "../../data/processed/fude_polygon/processed_fude_polygon.geojson"
processor = FudePolygonProcessor(input_path, output_path)
processor.process()
