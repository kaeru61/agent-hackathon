import geopandas as gpd
from shapely.geometry import Point, shape

def merge_farm_properties(farm_features):
    """
    複数の農地ピンのプロパティをマージします。
    geometry キー以外の情報を対象とし、同じキーについて複数値がある場合は
    カンマ区切りの文字列として統合します。
    """
    merged = {}
    # 農地ピンの属性は同一のキーがあることを前提（geometry は除外）
    for col in farm_features.columns:
        if col == 'geometry':
            continue
        # 農地ピンごとの値をリストにする
        values = farm_features[col].tolist()
        # 重複除去し、空でない値のみ取得
        unique_vals = list({str(v) for v in values if v not in [None, ""]})
        if unique_vals:
            # 値が１個ならそのまま、複数なら文字列として結合
            merged[col] = unique_vals[0] if len(unique_vals) == 1 else ", ".join(unique_vals)
    return merged

def merge_farm_polygon(farm_filepath, polygon_filepath, output_filepath):
    """
    農地ピン（Point）と筆ポリゴン（Polygon）を読み込み、
    各筆ポリゴン内に含まれる農地ピンの属性をすべて統合して結合しGeoJSONとして出力します。
    1:1 の対応となるよう、農地ピンが複数の場合はその属性情報をマージします。
    """
    # 農地ピンのGeoJSONを読み込む
    farm_gdf = gpd.read_file(farm_filepath)
    
    # 筆ポリゴンのGeoJSONを読み込む
    polygon_gdf = gpd.read_file(polygon_filepath)
    
    # 座標参照系（CRS）の統一（EPSG:4326）
    if farm_gdf.crs != 'EPSG:4326':
        farm_gdf = farm_gdf.to_crs('EPSG:4326')
    if polygon_gdf.crs != 'EPSG:4326':
        polygon_gdf = polygon_gdf.to_crs('EPSG:4326')
    
    merged_features = []
    
    for _, poly in polygon_gdf.iterrows():
        # 筆ポリゴン内にある農地ピンを抽出
        within_poly = farm_gdf[farm_gdf.within(poly.geometry)]
        poly_properties = poly.copy()
    
        if not within_poly.empty:
            # 農地ピンの件数を追加
            poly_properties['num_farm_pins'] = len(within_poly)
            # 農地ピンの属性をすべてマージ（geometry は除外）
            merged_farm_props = merge_farm_properties(within_poly)
            # マージした農地ピンの属性を筆ポリゴンの属性に結合
            for key, value in merged_farm_props.items():
                poly_properties[key] = value
        else:
            poly_properties['num_farm_pins'] = 0

        merged_features.append(poly_properties)
    
    # 結合結果を GeoDataFrame に変換
    merged_gdf = gpd.GeoDataFrame(merged_features, crs='EPSG:4326')
    
    # GeoJSON として出力
    merged_gdf.to_file(output_filepath, driver='GeoJSON')
    print("データの結合と出力が完了しました。")

def main():
    farm_filepath = '../../data/raw/eMAFF/農地ピン_20250220013122.geojson'          # 農地ピンデータのパス
    polygon_filepath = '../../data/processed/fude_polygon/processed_fude_polygon.geojson'     # 筆ポリゴンのデータのパス
    output_filepath = '../../data/processed/merged_polygon_with_farm_pin.geojson'
    
    merge_farm_polygon(farm_filepath, polygon_filepath, output_filepath)

if __name__ == '__main__':
    main()
