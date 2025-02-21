import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from folium.plugins import MarkerCluster

class MapComponent:
    def __init__(self, map_location=[36.3418, 140.4468], zoom_start=10):
        """
        地図コンポーネントの初期化
        
        Args:
            map_location (list): 初期の地図中心座標 [緯度, 経度]
            zoom_start (int): 初期のズームレベル
        """
        self.map = folium.Map(location=map_location, zoom_start=zoom_start)
        
    def load_geojson(self, geojson_data):
        """
        GeoJSONデータを読み込む
        
        Args:
            geojson_data: GeoJSONデータ（文字列パスまたは辞書）
        Returns:
            dict: 読み込んだGeoJSONデータ
        """
        if isinstance(geojson_data, str):
            try:
                with open(geojson_data, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"GeoJSONファイルの読み込みエラー: {e}")
                return None
        return geojson_data

    def add_geojson_layer(self, geojson_data, style_function=None):
        """
        GeoJSONレイヤーを地図に追加
        
        Args:
            geojson_data: GeoJSONデータ
            style_function: スタイル設定用の関数
        """
        if style_function is None:
            style_function = lambda x: {
                'fillColor': 'red',
                'color': 'red',
                'weight': 2,
                'fillOpacity': 0.6
            }
            
        folium.GeoJson(
            geojson_data,
            name="geojson",
            style_function=style_function
        ).add_to(self.map)

    def render_map(self):
        """
        Streamlit上に地図を描画
        """
        return st_folium(
            self.map,
            width=800,
            height=600,
        )

def create_map_container():
    """
    Streamlitの右カラムに地図コンテナを作成
    """
    # 2カラムレイアウトを作成
    left_col, right_col = st.columns([3, 7])
    
    with right_col:
        st.markdown("### 地図表示エリア")
        map_component = MapComponent()
        
        # GeoJSONファイルのアップロードを許可
        uploaded_file = st.file_uploader("GeoJSONファイルをアップロード", type=['geojson'])
        
        if uploaded_file is not None:
            geojson_data = json.load(uploaded_file)
            map_component.add_geojson_layer(geojson_data)
        
        # 地図を表示
        map_data = map_component.render_map()
        
        # クリックイベントの処理
        if map_data['last_clicked']:
            st.write("クリックされた座標:", map_data['last_clicked'])
    
    return left_col
