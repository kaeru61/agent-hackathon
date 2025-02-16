import folium
import json
from folium.plugins import MarkerCluster

class GeoJsonVisualizer:
    def __init__(self, geojson_data, map_location=[0, 0], zoom_start=2):
        """
        geojson_data: GeoJSONから解析された辞書またはファイルパス文字列。
        map_location: [緯度, 経度] 初期の地図の中心。
        zoom_start: 初期のズームレベル。
        """
        self.geojson_data = self.load_geojson(geojson_data)
        # デバッグ: 読み込んだGeoJSONのキーを出力
        if isinstance(self.geojson_data, dict):
            print("Loaded GeoJSON keys:", list(self.geojson_data.keys()))
        self.map = folium.Map(location=map_location, zoom_start=zoom_start)

    def load_geojson(self, geojson_data):
        if isinstance(geojson_data, str):
            try:
                with open(geojson_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"GeoJSON loaded successfully from {geojson_data}")
                    return data
            except Exception as e:
                print("Error loading GeoJSON file:", e)
                raise
        elif isinstance(geojson_data, dict):
            print("GeoJSON data provided as dictionary.")
            return geojson_data
        else:
            raise ValueError("Invalid GeoJSON data type. It should be a dict or a file path string.")

    def visualize(self, output_file='map.html'):
        """
        GeoJSONデータを地図上に可視化し、HTMLファイルとして保存します。
        """
        print("Visualizing GeoJSON data on map...")
        folium.GeoJson(
            self.geojson_data,
            name="geojson",
            style_function=lambda feature: {
                'fillColor': 'red',
                'color': 'red',
                'weight': 2,
                'fillOpacity': 0.6
            }
        ).add_to(self.map)
        folium.LayerControl().add_to(self.map)
        self.map.save(output_file)
        print(f"Map saved as {output_file}")

    def add_marker_cluster(self):
        """
        GeoJSONデータ内のすべてのPointおよびPolygonフィーチャーに対して
        マーカークラスターを追加します。
        Polygonの場合は、外周の座標平均をcentroidとして利用します。
        """
        marker_cluster = MarkerCluster().add_to(self.map)
        for feature in self.geojson_data.get('features', []):
            geom = feature.get('geometry', {})
            coordinates = geom.get('coordinates')
            if not coordinates:
                continue
            if geom.get('type') == 'Point':
                # GeoJSONでは[lon, lat]が指定されているので変換
                lon, lat = coordinates[0], coordinates[1]
            elif geom.get('type') == 'Polygon':
                # 外側リングの座標を利用し、簡易的にcenterを算出
                ring = coordinates[0]
                lon = sum(pt[0] for pt in ring) / len(ring)
                lat = sum(pt[1] for pt in ring) / len(ring)
            else:
                # その他のジオメトリタイプはスキップ
                continue
            folium.Marker(
                location=[lat, lon],
                popup=str(feature.get('properties', {}))
            ).add_to(marker_cluster)

    def visualize_with_clusters(self, output_file='map_with_clusters.html'):
        """
        Pointフィーチャーのマーカークラスターを含むGeoJSONデータを可視化し、HTMLファイルとして保存します。
        """
        print("Visualizing GeoJSON data with marker clusters...")
        self.add_marker_cluster()
        folium.GeoJson(
            self.geojson_data,
            name="geojson",
            style_function=lambda feature: {
                'fillColor': 'red',
                'color': 'red',
                'weight': 2,
                'fillOpacity': 0.6
            }
        ).add_to(self.map)
        folium.LayerControl().add_to(self.map)
        self.map.save(output_file)
        print(f"Map saved as {output_file}")

    def visualize_empty_map(self, output_file='empty_map.html'):
        """
        何も追加していない空の地図をそのままHTMLファイルとして保存します。
        """
        print("Saving empty map...")
        self.map.save(output_file)
        print(f"Empty map saved as {output_file}")

if __name__ == "__main__":
    geojson_file = "../data/processed/fude_polygon/processed_fude_polygon.geojson"
    output_path = "../visualizer/output/"
    visualizer = GeoJsonVisualizer(geojson_file, map_location=[36.3418, 140.4468], zoom_start=10)

    # GeoJSONの内容を反映した地図を表示（基本の可視化）
    visualizer.visualize(output_path+"my_map.html")

    # マーカークラスターを含む地図の可視化
    visualizer.visualize_with_clusters(output_path+"my_map_with_clusters.html")

    # 何も加えていない空の地図を表示
    visualizer.visualize_empty_map(output_path+"empty_map.html")
