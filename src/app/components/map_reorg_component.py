import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os

class MapReorgComponent:
    def __init__(self):
        self.map = folium.Map(location=[36.377328516, 140.375387545], zoom_start=14)

    def render_map(self):
        # GeoJSONファイルの読み込み
        geojson_file = 'src/app/ref/map-reorg.geojson'
        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # GeoJSONデータを地図に追加
        folium.GeoJson(geojson_data).add_to(self.map)

        # 地図をStreamlitに表示
        st_folium(self.map, width=700, height=500, key="map_reorg")

if __name__ == "__main__":
    map_reorg_component = MapReorgComponent()
    map_reorg_component.render_map()
