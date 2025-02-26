import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
import random
from collections import defaultdict
from typing import Dict, Any, Callable

usage_dict = {
    '1': '遊休農地',
    '3': '遊休農地ではない',
    '9': '調査中'
}

land_type_dict = {
    '1': '田',
    '2': '畑'
}

class ColorReorgMapComponent:
    def __init__(self):
        self.map = folium.Map(location=[36.377328516, 140.375387545], zoom_start=14)
        
        # 色分けパラメータの定義
        self.color_params = {
            'owner': {
                'name': '所有者',
                'key': 'FarmerIndicationNumberHash',
                'color_scheme': self._owner_color_scheme
            },
            'usage': {
                'name': '利用状況',
                'key': 'UsageSituationInvestigationResult',
                'color_scheme': {
                    '1': '#DC143C',  # 遊休農地: クリムゾン
                    '3': '#228B22',  # 遊休農地ではない: フォレストグリーン
                    '9': '#808080',  # 調査中: グレー
                }
            },
            'land_type': {
                'name': '農地区分',
                'key': 'ClassificationOfLand',
                'color_scheme': {
                    '1': '#90EE90',  # 田: ライトグリーン
                    '2': '#FFD700',  # 畑: ゴールド
                }
            }
        }

        # セッション状態の初期化
        if 'color_map' not in st.session_state:
            st.session_state.color_map = {}
        if 'owner_count' not in st.session_state:
            st.session_state.owner_count = defaultdict(int)

    def _owner_color_scheme(self, value: str) -> str:
        """所有者ごとの色分けロジック"""
        if st.session_state.owner_count[value] == 1:
            return '#808080'  # 灰色
        if value not in st.session_state.color_map:
            st.session_state.color_map[value] = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
        return st.session_state.color_map[value]

    def count_owner_properties(self, geojson_data):
        """所有者ごとの農地数をカウント"""
        owner_count = defaultdict(int)
        for feature in geojson_data['features']:
            owner_id = feature['properties'].get('FarmerIndicationNumberHash', '')
            owner_count[owner_id] += 1
        st.session_state.owner_count = owner_count

    def style_function(self, feature: Dict[str, Any], color_param: str) -> Dict[str, Any]:
        """スタイル関数"""
        properties = feature['properties']
        value = properties.get(self.color_params[color_param]['key'], '')
        
        # 色分けスキームの取得
        color_scheme = self.color_params[color_param]['color_scheme']
        if callable(color_scheme):
            color = color_scheme(value)
        else:
            color = color_scheme.get(str(value), '#808080')  # デフォルト色

        return {
            'fillColor': color,
            'color': color,
            'fillOpacity': 0.7
        }

    def render_map(self, color_param: str = 'owner'):
        """マップの描画"""
        # パラメータの選択UI
        selected_param = st.selectbox(
            '色分けの基準を選択',
            options=list(self.color_params.keys()),
            format_func=lambda x: self.color_params[x]['name'],
            key="color_reorg_param"
        )

        geojson_file = 'src/app/ref/map-reorg.geojson'
        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # 所有者による色分けの場合はカウントを更新
        if selected_param == 'owner':
            self.count_owner_properties(geojson_data)

        # 凡例の表示
        self._render_legend(selected_param)

        # GeoJSONレイヤーの追加
        folium.GeoJson(
            geojson_data,
            style_function=lambda x: self.style_function(x, selected_param),
            tooltip=folium.GeoJsonTooltip(
                fields=['Address', self.color_params[selected_param]['key'], 'worktime_reduced', 'fuel_cost_reduced'],
                aliases=['住所', self.color_params[selected_param]['name'], '作業時間削減', '燃料費削減'],
                localize=True
            )
        ).add_to(self.map)

        st_folium(self.map, width=700, height=500, key="map_reorg_colored")

    def _render_legend(self, color_param: str):
        """凡例の表示"""
        st.write('### 凡例')
        color_scheme = self.color_params[color_param]['color_scheme']
        
        if not callable(color_scheme):
            cols = st.columns(len(color_scheme))
            for i, (value, color) in enumerate(color_scheme.items()):
                with cols[i]:
                    if color_param == 'usage':
                        label = usage_dict.get(value, value)
                    elif color_param == 'land_type':
                        label = land_type_dict.get(value, value)
                    else:
                        label = value
                    st.markdown(
                    f'<div style="background-color: {color}; padding: 10px; '
                    f'border: 1px solid black; text-align: center;">{label}</div>',
                    unsafe_allow_html=True
                    )
