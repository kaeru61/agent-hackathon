from typing import Dict, Any, Tuple
from dataclasses import dataclass
import geopandas as gpd
import math
from fractions import Fraction
import numpy as np
from shapely.ops import voronoi_diagram
from shapely.geometry import MultiPolygon, Polygon
import pandas as pd
from sklearn.cluster import DBSCAN
from scipy.spatial import KDTree
from functions.cost_analyzer import AnalysisResult, run_analysis ##################



@dataclass
class Scenario:
    """シナリオを定義するデータクラス"""
    ta_farmer_N: int
    hata_farmer_N: int
    ta_exfarmer_ids_and_rates: Dict[str, float]
    hata_exfarmer_ids_and_rates: Dict[str, float]

def reorganize(
    geojson_data: Dict[str, Any],
    scenario: Scenario
) -> Tuple[Dict[str, Any], AnalysisResult]:
    """農地データを再編成する

    Args:
        geojson_data (Dict): 再編成対象のGeoJSONデータ
        scenario (Scenario): 再編成のシナリオ

    Returns:
        Tuple[Dict[str, Any], AnalysisResult]: 再編成後のGeoJSONデータ、コスト分析結果
    """
    # 新規農家の数
    print(scenario.ta_farmer_N)
    print(scenario.hata_farmer_N)
    print(scenario.ta_exfarmer_ids_and_rates)
    print(scenario.hata_exfarmer_ids_and_rates)

    ta_newfarmer_N = scenario.ta_farmer_N - len(scenario.ta_exfarmer_ids_and_rates.keys())
    hata_newfarmer_N = scenario.hata_farmer_N - len(scenario.hata_exfarmer_ids_and_rates.keys())
    print("田の新規農家数："+str(ta_newfarmer_N)+"畑の新規農家数："+str(hata_newfarmer_N))

    # 新規農家は固定で0.1
    ta_arearates = _scale_ratios([r for r in scenario.ta_exfarmer_ids_and_rates.values()], 1-ta_newfarmer_N*0.1)
    ta_arearates.extend([0.1]*ta_newfarmer_N)
    hata_arearates = _scale_ratios([r for r in scenario.hata_exfarmer_ids_and_rates.values()], 1-hata_newfarmer_N*0.1)
    hata_arearates.extend([0.1]*hata_newfarmer_N)
    print("田：",ta_arearates)
    print("畑：",hata_arearates)

    # GeoDataFrameを作成
    gdf = gpd.GeoDataFrame.from_features(geojson_data)

    # projectionを設定
    gdf = gdf.set_crs(epsg=4326)

    # 田畑ごとのGeoJSONデータを作成
    ta_gdf, hata_gdf = _create_tahata_gdf(gdf, distance=30)

    # CRSを設定
    ta_gdf.set_crs(epsg=4326, inplace=True)  # WGS84座標系を設定
    hata_gdf.set_crs(epsg=4326, inplace=True)  # WGS84座標系を設定

    # 田畑ごとに農家のbasepointをexfarmer_ids_and_ratesから取得
    ta_ex_basepoint = {ID: _getbasepoint(ta_gdf, ID) for ID in scenario.ta_exfarmer_ids_and_rates.keys()}
    hata_ex_basepoint = {ID: _getbasepoint(hata_gdf, ID) for ID in scenario.hata_exfarmer_ids_and_rates.keys()}

    # 区画数を取得
    ta_area_n = _find_partition_count(ta_arearates)
    hata_area_n = _find_partition_count(hata_arearates)
    print("田の区画数："+str(ta_area_n)+"畑の区画数："+str(hata_area_n))

    # 田畑ごとに区画化
    ta_gdf_poly, ta_gdf_multipoly = _partition(ta_gdf, ta_area_n)
    hata_gdf_poly, hata_gdf_multipoly = _partition(hata_gdf, hata_area_n)

    ta_area_nums = {ID: math.ceil(r * ta_area_n) for ID, r in zip(scenario.ta_exfarmer_ids_and_rates.keys(), ta_arearates)}
    hata_area_nums = {ID: math.ceil(r * hata_area_n) for ID, r in zip(scenario.hata_exfarmer_ids_and_rates.keys(), hata_arearates)}

    # 現農家の配置
    ta_gdf_poly, ta_gdf_multipoly = _put_existing_farmers(ta_gdf_poly, ta_gdf_multipoly, ta_ex_basepoint, ta_area_nums)
    hata_gdf_poly, hata_gdf_multipoly = _put_existing_farmers(hata_gdf_poly, hata_gdf_multipoly, hata_ex_basepoint, hata_area_nums)

    # 新規農家の配置
    ta_gdf_poly, ta_gdf_multipoly = _put_new_farmers(ta_gdf_poly, ta_gdf_multipoly, scenario.ta_farmer_N - len(scenario.ta_exfarmer_ids_and_rates))
    hata_gdf_poly, hata_gdf_multipoly = _put_new_farmers(hata_gdf_poly, hata_gdf_multipoly, scenario.hata_farmer_N - len(scenario.hata_exfarmer_ids_and_rates))

    # CRS84に変換
    ta_gdf_poly = ta_gdf_poly.to_crs(epsg=4326)
    ta_gdf_multipoly = ta_gdf_multipoly.to_crs(epsg=4326)
    hata_gdf_poly = hata_gdf_poly.to_crs(epsg=4326)
    hata_gdf_multipoly = hata_gdf_multipoly.to_crs(epsg=4326)

    # コスト分析結果をgdfに格納(現在はpolyのみ)
    all_exfarmer_ids = list(set(scenario.ta_exfarmer_ids_and_rates.keys()).union(set(scenario.hata_exfarmer_ids_and_rates.keys())))
    result, ta_gdf_poly, hata_gdf_poly = _excute_analysis(gdf, ta_gdf_poly, hata_gdf_poly, all_exfarmer_ids)

    # GeoJSONデータに変換
    # geojson_data = {
    #     "type": "FeatureCollection",
    #     "features": list(ta_gdf_poly.__geo_interface__["features"]) + list(ta_gdf_multipoly.__geo_interface__["features"]) + list(hata_gdf_poly.__geo_interface__["features"]) + list(hata_gdf_multipoly.__geo_interface__["features"])
    # }
    # polyのみのGeoJSONデータ
    poly_geojson_data = {
        "type": "FeatureCollection",
        "features": list(ta_gdf_poly.__geo_interface__["features"]) + list(hata_gdf_poly.__geo_interface__["features"])
    }
    return poly_geojson_data, result

def _scale_ratios(ratios: Tuple[int], total: float) -> list[float]:
    """
    整数比 ratios を 0.1 刻みの比にスケーリングし、合計を total にする
    """
    step = 10  # 0.1刻みで扱うために10倍する
    total_int = int(total * step)  # 合計を整数値で処理

    # 整数比の合計
    ratio_sum = sum(ratios)

    # 各比率をスケーリング（total に合計がなるように変換）
    scaled_ratios = [round(r / ratio_sum * total_int) for r in ratios]

    # 合計が total_int になっているか調整（四捨五入の誤差補正）
    diff = total_int - sum(scaled_ratios)
    for i in range(abs(diff)):
        scaled_ratios[i % len(scaled_ratios)] += 1 if diff > 0 else -1

    # 0.1刻みの比に戻す
    return [r / step for r in scaled_ratios]

def _create_tahata_gdf(
    gdf: gpd.GeoDataFrame,
    distance: float = 30
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """田畑ごとのGeoJSONデータを作成する。孤立している田畑を周りの田畑の分類に基づいて再分類する。

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame
        distance (float, optional): 一定の距離. Defaults to 30.

    Returns:
        Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: 田畑ごとのGeoDataFrame
    """

    # 空間インデックスを作成
    sindex = gdf.sindex

    # 各ポリゴンの新しい分類を格納するリスト
    new_classifications = gdf["ClassificationOfLand"].copy()

    for i, geom in enumerate(gdf.geometry):
        # print(str(i) + "番目のポリゴン")
        # 一定の距離内のポリゴンを検索
        buffer = geom.buffer(distance/1000/100)
        nearby = gdf[gdf.geometry.intersects(buffer)]

        # 一定の距離内のポリゴンの分類を取得
        neighbor_classifications = nearby["ClassificationOfLand"]

        # 一定の距離内のポリゴンの分類のカウント
        counts = neighbor_classifications.value_counts()

        # 現在の分類
        current_classification = gdf.loc[i, "ClassificationOfLand"]
        # print("現在："+current_classification)
        # print("隣接するポリゴンの分類："+str(counts))

        # 隣接するポリゴンの分類に基づいて変更
        if current_classification == "2" and counts.get("1", 0) > counts.get("2", 0):
            # print("畑を田に変更")
            new_classifications[i] = "1"
        elif current_classification == "1" and counts.get("2", 0) > counts.get("1", 0):
            new_classifications[i] = "2"
            # print("田を畑に変更")
        elif current_classification == "1, 2" and counts.get("1", 0) > counts.get("2", 0):
            new_classifications[i] = "1"
            # print("田畑を田に変更")
        elif current_classification == "1, 2" and counts.get("2", 0) >= counts.get("1", 0):
            new_classifications[i] = "2"
            # print("田畑を畑に変更")
        elif current_classification == "2, 1" and counts.get("1", 0) > counts.get("2", 0):
            new_classifications[i] = "1"
            # print("畑田を田に変更")
        elif current_classification == "2, 1" and counts.get("2", 0) >= counts.get("1", 0):
            new_classifications[i] = "2"
            # print("畑田を畑に変更")

    # print(new_classifications.unique())
    # 新しい分類を適用
    gdf["ClassificationOfLand"] = new_classifications

    ta_gdf = gdf[gdf["ClassificationOfLand"] == "1"]
    hata_gdf = gdf[gdf["ClassificationOfLand"] == "2"]

    # print(ta_gdf['ClassificationOfLand'].value_counts())
    # print(hata_gdf)

    return ta_gdf, hata_gdf

def _find_partition_count(arearates: list[float]) -> int:
    """区画数を計算する

    Args:
        arearates (list[float]): 面積割合のリスト

    Returns:
        int: 区画数
    """
    fractions_list = [Fraction(r).limit_denominator() for r in arearates]
    denominators = [f.denominator for f in fractions_list]
    partition_count = math.lcm(*denominators)
    return partition_count

def _partition(
    gdf: gpd.GeoDataFrame,
    partition_count: int
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """GeoDataFrameを区画化する

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame
        partition_count (int): 区画数

    Returns:
        Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: 区画化後のGeoDataFrame"""
    Model = _PartitionModel(gdf, partition_count)
    result_poly, result_multipoly = Model.run()
    return result_poly, result_multipoly

def _getbasepoint(
    gdf: gpd.GeoDataFrame,
    ID: int
    ) ->Tuple[float, float]:
    """1km範囲での自分の農地の面積が広い農地を中心農地として設定する

    Args:
        gdf (gpd.GeoDataFrame): geoPandasのGeoDataFrame
        ID (int): 農家のID

    Returns:
        Tuple[float, float]: 中心農地の座標
    """

    farms = gdf[gdf['FarmerIndicationNumberHash'] == ID]
    max_area = 0
    central_farm = None

    # 農地を持っていない場合は、gdfの座標の範囲の中でランダムに選択
    if len(farms) == 0:
        if len(gdf) == 0:
            raise ValueError("GeoDataFrame is empty. Cannot select a random farm.")
        # ランダム選択
        random_farm = gdf.sample()
        # projected CRSに変換
        random_farm = random_farm.to_crs(epsg=32654)
        return random_farm.geometry.centroid.iloc[0].coords[0]

    # 一つ一つの農地に対して、1km範囲での自分の農地の面積が広い農地を中心農地として設定する
    for farm in farms.geometry:
        # 1kmのバッファを作成
        buffer = farm.buffer(1/440)
        # バッファと交差する農地を取得
        intersecting_farms = farms[farms.geometry.intersects(buffer)]
        # print(len(intersecting_farms))
        total_area = intersecting_farms.to_crs(epsg=32654).geometry.area.sum()
        # print('Farmer ID:', ID, 'Total Area:', total_area)

        if total_area > max_area:
            max_area = total_area
            central_farm = farm

        # print('Farmer ID:', ID, 'central_farm:', central_farm)
        # print(max_area)

    return central_farm.centroid.coords[0]

def _put_existing_farmers(
    gdf_poly: gpd.GeoDataFrame,
    gdf_multipoly: gpd.GeoDataFrame,
    ex_basepoint: Dict[str, Tuple[float, float]],
    area_nums: Dict[str, int]
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:

    # EPSG:4326 (緯度経度) に変換
    if gdf_multipoly.crs and gdf_multipoly.crs.to_epsg() != 4326:
        gdf_multipoly = gdf_multipoly.to_crs(epsg=4326)

    # 各クラスターの重心を計算
    gdf_multipoly["centroid"] = gdf_multipoly.geometry.centroid
    centroids = gpd.GeoDataFrame(geometry=gdf_multipoly["centroid"], crs=gdf_multipoly.crs)


    # KDTreeを作成して最近傍探索を効率化
    tree = KDTree(centroids.geometry.apply(lambda p: (p.x, p.y)).tolist())

    # 各農家の最近傍クラスターを決定（被りなしを優先）
    cluster_assignment = {}
    assigned_clusters = set()
    remaining_farmers = set(ex_basepoint.keys())
    conflicted_farmers = []

    for farmer_id, (lon, lat) in ex_basepoint.items():
        _, idx = tree.query((lon, lat))
        cluster_idx = gdf_multipoly.index[idx]

        if cluster_idx not in assigned_clusters:
            cluster_assignment[farmer_id] = [cluster_idx]
            assigned_clusters.add(cluster_idx)
            remaining_farmers.remove(farmer_id)
        else:
            conflicted_farmers.append((farmer_id, cluster_idx))

    # クラスターを増やす処理（最近傍ベースで拡張）
    def expand_farmer_clusters(farmer_id, required_area):
        while len(cluster_assignment[farmer_id]) < required_area:
            current_clusters = cluster_assignment[farmer_id]
            candidate_clusters = list(set(gdf_multipoly.index) - assigned_clusters)

            if not candidate_clusters:
                break

            if not current_clusters:
                # 最初のクラスターをbasepointからの距離で決める（すでに割り当てられたクラスターは除外）
                base_lon, base_lat = ex_basepoint[farmer_id]
                distances, indices = tree.query((base_lon, base_lat), k=len(gdf_multipoly))
                first_cluster = next((gdf_multipoly.index[i] for i in indices if gdf_multipoly.index[i] not in assigned_clusters), None)
                if first_cluster is None:
                    break
                cluster_assignment[farmer_id] = [first_cluster]
                assigned_clusters.add(first_cluster)
                current_clusters = [first_cluster]

            new_cluster = min(
                (c for c in candidate_clusters if c not in assigned_clusters),
                key=lambda c: min(
                    (gdf_multipoly.loc[c, "centroid"].distance(gdf_multipoly.loc[cc, "centroid"])
                     for cc in current_clusters),
                    default=float("inf")
                ),
                default=None
            )

            if new_cluster is not None:
                cluster_assignment[farmer_id].append(new_cluster)
                assigned_clusters.add(new_cluster)

    # まず被ってない農家に対してクラスターを拡張
    for farmer_id in list(cluster_assignment.keys()):
        expand_farmer_clusters(farmer_id, area_nums[farmer_id])

    # 被った農家のうちクラスターに近い方を優先
    conflicted_farmers.sort(key=lambda x: tree.query(ex_basepoint[x[0]])[0])

    for farmer_id, _ in conflicted_farmers:
        if farmer_id not in cluster_assignment:
            cluster_assignment[farmer_id] = []
        expand_farmer_clusters(farmer_id, area_nums[farmer_id])

    # 結果をGeoDataFrameに反映
    assignment_series = pd.Series({c: f for f, clusters in cluster_assignment.items() for c in clusters})
    gdf_multipoly["FarmerIndicationNumberHash"] = gdf_multipoly.index.map(assignment_series.get)
    # reorganizedというカラムを作り、FarmerIndicationNumberHashが更新されたもののみTrueにする
    gdf_multipoly["reorganized"] = gdf_multipoly.index.isin(assignment_series.index)

    # polyの方で、"cluster"キーの値がassignment_series.indexに一致するものの"FarmerIndicationNumberHash"を更新
    gdf_poly.loc[gdf_poly["cluster"].isin(assignment_series.index), "FarmerIndicationNumberHash"] = gdf_poly["cluster"].map(assignment_series)
    gdf_poly.loc[gdf_poly["cluster"].isin(assignment_series.index), "reorganized"] = True

    # gdf_multipolyからcentroidを削除
    gdf_multipoly = gdf_multipoly.drop(columns=["centroid"])

    return gdf_poly, gdf_multipoly

def _put_new_farmers(
    gdf_poly: gpd.GeoDataFrame,
    gdf_multipoly: gpd.GeoDataFrame,
    farmer_N: int
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """新規農家を配置する

    Args:
        gdf_poly (gpd.GeoDataFrame): 単一のポリゴンを持つGeoDataFrame
        gdf_multipoly (gpd.GeoDataFrame): 複数のポリゴンを持つGeoDataFrame
        farmer_N (int): 新規農家の数

    Returns:
        Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: 新規農家を配置後のGeoDataFrame
    """
    # reorganizedがFalseのインデックスを取得
    unassigned_indices = gdf_multipoly.index[~gdf_multipoly["reorganized"]]
    i=0
    for unassigned_index in unassigned_indices:
        gdf_multipoly.loc[unassigned_index, "FarmerIndicationNumberHash"] = f"newfarmer{str(i)}"
        gdf_multipoly.loc[unassigned_index, "reorganized"] = True
        # polyの方で、"cluster"キーの値がunassigned_indexに一致するものの"FarmerIndicationNumberHash"を更新
        gdf_poly.loc[gdf_poly["cluster"] == unassigned_index, "FarmerIndicationNumberHash"] = f"newfarmer{str(i)}"
        gdf_poly.loc[gdf_poly["cluster"] == unassigned_index, "reorganized"] = True
        i+=1

    return gdf_poly, gdf_multipoly

def _excute_analysis(
    gdf: gpd.GeoDataFrame,
    reorg_ta_gdf: gpd.GeoDataFrame,
    reorg_hata_gdf: gpd.GeoDataFrame,
    existing_farmer_ids: list[str]
) -> Tuple[AnalysisResult, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """コスト分析を実行する

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame
        reorg_ta_gdf (gpd.GeoDataFrame): 最適化後の田のGeoDataFrame
        reorg_hata_gdf (gpd.GeoDataFrame): 最適化後畑のGeoDataFrame
        existing_farmer_ids (list[str]): 既存農家のIDリスト

    Returns:
        Tuple[AnalysisResult, gpd.GeoDataFrame, gpd.GeoDataFrame]: コスト分析結果、最適化後の田のGeoDataFrame、最適化後の畑のGeoDataFrame

    """
    # コスト分析を実行
    result = run_analysis(gdf, existing_farmer_ids)
    # existing_farmer_idsに記載されている農家のコスト分析結果を反映
    for farmer_id in existing_farmer_ids:
        reorg_ta_gdf.loc[reorg_ta_gdf["FarmerIndicationNumberHash"] == farmer_id, "worktime_reduced"] = result.farmers_worktime_reduced[farmer_id]
        reorg_ta_gdf.loc[reorg_ta_gdf["FarmerIndicationNumberHash"] == farmer_id, "fuel_cost_reduced"] = result.farmers_fuel_cost_reduced[farmer_id]
        reorg_hata_gdf.loc[reorg_hata_gdf["FarmerIndicationNumberHash"] == farmer_id, "worktime_reduced"] = result.farmers_worktime_reduced[farmer_id]
        reorg_hata_gdf.loc[reorg_hata_gdf["FarmerIndicationNumberHash"] == farmer_id, "fuel_cost_reduced"] = result.farmers_fuel_cost_reduced[farmer_id]

    return result, reorg_ta_gdf, reorg_hata_gdf


class _PartitionModel:
    def __init__(self, gdf: gpd.GeoDataFrame, partition_count: int):
        self.gdf = gdf
        self.partition_count = partition_count

    def estimate_eps(self, farmland):
        """適切な eps を推定する（農地の距離分布から計算）"""
        centroids = np.array([geom.centroid.coords[0] for geom in farmland.geometry])
        from scipy.spatial import distance_matrix
        dist_matrix = distance_matrix(centroids, centroids)
        np.fill_diagonal(dist_matrix, np.inf)  # 自分自身を除外
        min_dists = np.min(dist_matrix, axis=1)
        return np.percentile(min_dists, 75)  # 75パーセンタイルの距離を eps にする

    def split_largest_cluster(grouped, target_n):
        """クラスタ数が target_n より少ない場合、大きなクラスタを分割"""
        while len(grouped) < target_n:
            largest_idx = grouped.area.idxmax()
            largest_poly = grouped.loc[largest_idx].geometry

            # 重心を基に Voronoi 分割
            points = [largest_poly.centroid]
            for _ in range(2):  # 2分割する
                new_point = largest_poly.representative_point()
                points.append(new_point)

            voronoi_regions = voronoi_diagram(MultiPolygon([largest_poly]), [p for p in points])
            new_polys = [r.intersection(largest_poly) for r in voronoi_regions.geoms]

            # 分割後のポリゴンを追加
            new_geos = [p for p in new_polys if isinstance(p, Polygon)]
            grouped = grouped.drop(largest_idx)
            new_df = gpd.GeoDataFrame(geometry=new_geos)
            grouped = pd.concat([grouped, new_df]).reset_index(drop=True)
        return grouped

    def run(self) -> gpd.GeoDataFrame:
        """クラスタリングを実行する

        Returns:
            gpd.GeoDataFrame: クラスタリング結果
        """
        farmland = self.gdf
        target_n = self.partition_count
        # 重心を基にクラスタリング
        farmland = farmland.to_crs(epsg=6674)  # 座標系を投影に
        centroids = np.array([geom.centroid.coords[0] for geom in farmland.geometry])
        eps_value = self.estimate_eps(farmland)  # 自動的に eps を決定

        # DBSCAN を使用して隣接する農地をクラスタリング
        clustering = DBSCAN(eps=eps_value, min_samples=1).fit(centroids)
        farmland["cluster"] = clustering.labels_ # クラスタリング結果を追加

        grouped = farmland.dissolve(by="cluster") # dissolve: クラスタごとにまとめる
        # 座標系を投影に

        # クラスタid変更履歴
        change_cluster_id = {}
        # クラスタ数が target_n より多い場合 → 統合
        while len(grouped) > target_n:
            # print(len(grouped))
            smallest_idx = grouped.area.idxmin()
            smallest_poly = grouped.loc[smallest_idx]
            remaining = grouped.drop(smallest_idx)
            nearest_idx = remaining.distance(smallest_poly.geometry).idxmin()
            grouped.loc[nearest_idx, "geometry"] = remaining.loc[nearest_idx].geometry.union(smallest_poly.geometry)
            grouped = grouped.drop(smallest_idx)
            change_cluster_id[smallest_idx] = nearest_idx
        # print(change_cluster_id)

        # クラスタ数が target_n より少ない場合 → 分割
        # grouped = split_largest_cluster(grouped, target_n)
        # groupedのタイプはGeoDataFrame

        # クラスタid変更履歴を適用
        for k, v in change_cluster_id.items():
            farmland.loc[farmland["cluster"] == k, "cluster"] = v

        # クラスタidを振り直す
        cluster_id_map = {k: i for i, k in enumerate(farmland["cluster"].unique())}
        farmland["cluster"] = farmland["cluster"].map(cluster_id_map)
        grouped = grouped.reset_index(drop=True)
        return farmland, grouped

# 直接実行された時は、テストデータを使って動作確認
if __name__ == "__main__":
    import json
    with open("../../notebooks/data/geojson_filtered_by_settlement/筑地.geojson") as f:
        geojson_data = json.load(f)
    scenario = Scenario(
        ta_farmer_N=6,
        hata_farmer_N=3,
        ta_exfarmer_ids_and_rates={
            "2dacba93d45b0f46a25b29b985bd90e2": 3,
            "10aad9b486abee43973bb555cc3362c2": 2,
            "7db8af145bda49552f855ba395906a2f": 2
        },
        hata_exfarmer_ids_and_rates={
            "2dacba93d45b0f46a25b29b985bd90e2": 1
        }
    )
    test_reorganized_geojson, result = reorganize(geojson_data, scenario)
    # 新しいGeoJSONを保存
    new_geojson_data = {
        "type": "FeatureCollection",
        "name": "reorganized_geojson",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": test_reorganized_geojson["features"]
    }

    with open("test_reorganized.geojson", "w") as f:
        json.dump(new_geojson_data, f, ensure_ascii=False)

    print("最適化前のリソースシミュレーション結果:")
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
    print("\n")
