import json
from typing import Dict, Any, List, Union, Callable
from dataclasses import dataclass
from functions.filiter import FieldSearchCriteria, search_fields
import shutil
from datetime import datetime
import os
import geopandas as gpd
import math
from functions.reorganize import Scenario, reorganize
import random as rand
from functions.cropsimulation import run_simulation

def reorganize_farmland(params_json: str) -> dict:
    """
    農地再編成関数

    Args:
        params_json (str): JSON形式の再編成条件

    Returns:
        dict: 再編成結果
    """
    try:
        # JSONパース
        params = json.loads(params_json)
        print(params)

        # GeoJSONデータの読み込み
        with open('src/app/ref/map.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        print("GeoJSONデータを読み込みました")

        # バックアップ作成
        src_path = 'src/app/ref/map-reorg.geojson'
        if os.path.exists(src_path):
            time = datetime.now().strftime('%Y%m%d%H%M%S')
            dest_path = f'src/app/ref/backup/map-reorg-{time}.geojson'
        print(f"バックアップを作成します: {src_path} -> {dest_path}")

        shutil.copy(src_path, dest_path)
        print(f"ファイルをコピーしました: {src_path} -> {dest_path}")

        # Scenarioデータクラスへの変換
        scenario = Scenario(
            ta_farmer_N=params.get("ta_farmer_N", 0),
            hata_farmer_N=params.get("hata_farmer_N", 0),
            ta_exfarmer_ids_and_rates=params.get("ta_exfarmer_ids_and_rates", {}),
            hata_exfarmer_ids_and_rates=params.get("hata_exfarmer_ids_and_rates", {})
        )

        # 農地再編成の実行
        reorganized_geojson, analysis_result = reorganize(geojson_data, scenario)
        print("再編成完了")

        # 再編成結果をファイルに保存
        with open('src/app/ref/map-reorg.geojson', 'w', encoding='utf-8') as f:
            json.dump(reorganized_geojson, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "scenario_applied": {
                "ta_farmer_N": scenario.ta_farmer_N,
                "hata_farmer_N": scenario.hata_farmer_N,
                "ta_exfarmer_ids_and_rates": scenario.ta_exfarmer_ids_and_rates,
                "hata_exfarmer_ids_and_rates": scenario.hata_exfarmer_ids_and_rates
            },
            "result_geojson": reorganized_geojson,
            "analysis_result": analysis_result
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"JSONパースエラー: {str(e)}",
            "scenario_applied": None,
            "results": []
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": f"パラメータ変換エラー: {str(e)}",
            "scenario_applied": None,
            "results": []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"再編成処理エラー: {str(e)}",
            "scenario_applied": None,
            "results": []
        }

def filter_farmland(params_json: str) -> dict:
    """
    農地フィルタリング関数

    Args:
        params_json (str): JSON形式の検索条件

    Returns:
        dict: フィルタリング結果
    """
    try:
        # JSONパース
        params = json.loads(params_json)
        print(params)

        # 検索条件の構築
        search_criteria = FieldSearchCriteria(
            farmer_id=params.get("farmer_id"),
            land_type=params.get("land_type"),
            issue_year=params.get("issue_year"),
            area_min=float(params.get("area_min", 0)) if params.get("area_min") else None,
            area_max=float(params.get("area_max", 0)) if params.get("area_max") else None,
            prefecture_code=params.get("prefecture_code"),
            city_code=params.get("city_code"),
            usage_situation=params.get("usage_situation"),
            classification=params.get("classification"),
            settlement=params.get("settlement")
        )

        # GeoJSONデータの読み込み
        with open('src/app/ref/map-row.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        src_path = 'src/app/ref/map.geojson'
        time = datetime.now().strftime('%Y%m%d%H%M%S')
        dest_path = f'src/app/ref/backup/map-{time}.geojson'

        shutil.copy(src_path, dest_path)
        print(f"ファイルをコピーしました: {src_path} -> {dest_path}")

        #  検索結果を取得
        filtered_features = search_fields(geojson_data, search_criteria)

        # 新しいGeoJSONを構築
        filtered_geojson = {
            "type": "FeatureCollection",
            "name": "filtered_merged_polygon_with_farm_pin",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
                }
            },
            "features": filtered_features
        }

        # フィルタリング結果をファイルに保存
        with open('src/app/ref/map.geojson', 'w', encoding='utf-8') as f:
            json.dump(filtered_geojson, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "filters_applied": {
                "farmer_id": search_criteria.farmer_id,
                "land_type": search_criteria.land_type,
                "issue_year": search_criteria.issue_year,
                "area_min": search_criteria.area_min,
                "area_max": search_criteria.area_max,
                "prefecture_code": search_criteria.prefecture_code,
                "city_code": search_criteria.city_code,
                "usage_situation": search_criteria.usage_situation,
                "classification": search_criteria.classification
            },
            "results": filtered_geojson
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"JSONパースエラー: {str(e)}",
            "filters_applied": None,
            "results": []
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": f"パラメータ変換エラー: {str(e)}",
            "filters_applied": None,
            "results": []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"検索処理エラー: {str(e)}",
            "filters_applied": None,
            "results": []
        }

def color_farmland(data):
    pass

def fix_reorg(params_json: str) -> dict:
    """
    農地再編成後の修正関数

    Args:
        params_json (str): JSON形式の修正条件

    Returns:
        dict: 修正結果
    """
    try:
        # JSONパース
        params = json.loads(params_json)
        print(params)

        # GeoJSONデータの読み込み
        with open('src/app/ref/map-reorg.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # バックアップ作成
        src_path = 'src/app/ref/map-reorg.geojson'
        time = datetime.now().strftime('%Y%m%d%H%M%S')
        dest_path = f'src/app/ref/backup/map-reorg-{time}.geojson'

        shutil.copy(src_path, dest_path)
        print(f"ファイルをコピーしました: {src_path} -> {dest_path}")

        # 特定の農地の情報を更新
        target_address = params.get("target_address")
        new_farmer_id = params.get("new_farmer_id")
        new_land_type = params.get("new_farm_type")

        updated_count = 0
        updates = []

        for feature in geojson_data['features']:
            properties = feature['properties']
            if properties['Address'] == target_address:
                # 農家IDを更新
                old_farmer_id = properties['FarmerIndicationNumberHash']
                properties['FarmerIndicationNumberHash'] = new_farmer_id

                # 農地種類の更新（指定がある場合のみ）
                if new_land_type is not None:
                    old_type = properties.get('ClassificationOfLand', '')
                    properties['ClassificationOfLand'] = new_land_type
                    properties['ClassificationOfLandCodeName'] = '田' if new_land_type == '1' else '畑'
                    updates.append({
                        'address': properties['Address'],
                        'old_farmer_id': old_farmer_id,
                        'old_type': '田' if old_type == '1' else '畑',
                        'new_type': '田' if new_land_type == '1' else '畑'
                    })

                updated_count += 1

        if updated_count == 0:
            return {
                "status":
                "error",
                "error": f"指定された住所 '{target_address}' に一致する農地が見つかりませんでした。",
                "results": []
            }
        else:
            with open('src/app/ref/map-reorg.geojson', 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=2)
            message = f"{updated_count}件の農地情報を更新しました。"
            if updates:
                message += "\n農地種類の変更内容:"
                for update in updates:
                    message += f"\n- {update['address']}: {update['old_type']} → {update['new_type']}"
                return {
                    "status": "success",
                    "message": message,
                    "updated_count": updated_count,
                    "land_type_updates": updates
                }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"JSONパースエラー: {str(e)}",
            "results": []
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": f"パラメータ変換エラー: {str(e)}",
            "results": []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"修正処理エラー: {str(e)}",
            "results": []
        }



def crop_simulation(params_json: str):
    try:
        params = json.loads(params_json)
        print(params)
        if params.get("lat") is None or params.get("lon") is None:
            print("緯度経度が指定されていません")
            return ValueError("緯度経度が指定されていません")

        # rice, potato, wheatじゃなかったらエラー
        if params.get("crop") not in ["rice", "potato", "wheat"]:
            print("作物名が不正です")
            return ValueError("作物名が不正です")

        # TODO: 収量予測の実装
        result = run_simulation(params.get("crop"), params.get("lat"), params.get("lon"))
        return {
            "status": "success",
            "result": result
        }
    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {str(e)}")
        return {
            "status": "error",
            "error": f"JSONパースエラー: {str(e)}",
            "results": []
        }


TASKS: dict[int, dict[int, dict[str, Union[str, Callable]]]] = {
    1: {
        1: {
            "name": "農地のフィルタリング",
            "description": """
            ユーザーが求める農地のフィルタリングや整形を行うエージェントです。
            ユーザーの指定した条件に基づいて、農地データを検索します。
            農地データを検索するための条件を以下のJSONフォーマットで指定してください：

            ```json
            {
                "farmer_id": "農家識別子のハッシュ値（任意）",
                "land_type": "土地種別コード（任意）",
                "issue_year": "発行年（任意）",
                "area_min": "最小面積（任意）",
                "area_max": "最大面積（任意）",
                "prefecture_code": "都道府県コード（任意）",
                "city_code": "市区町村コード（任意）",
                "usage_situation": "利用状況（任意）",
                "classification": "農地区分（例：田、畑）（任意）"
                "settlement": "農業集落名（任意）"
            }
            ```

            以下は検索例です：
            1. 茨城県（08）の1000平方メートル以上の農地を検索
            2. 特定の農家（farmer_id指定）が所有する遊休農地を検索
            3. 市街化調整区域内の田を検索
            4: 大足(農業集落)の農地を検索

            必要な条件のみを指定してください。指定しない条件は省略可能です。
            """,
            "function": filter_farmland
        },
        2: {
            "name": "農地の色付け",
            "description": """
            ユーザーが求める農地の色付けを行うエージェントです。
            まず、色分けを実行したいのか、解除したいのかを判断してください。
            変数は、以上のうちいずれか一つを指定してください。
            出力は0か1のみにしてください
            0は解除
            1は色分け
            """,
            "function": color_farmland
        },
        3: {
            "name": "農地の再編成",
            "description": """
            農地の再編成を行うエージェントです。
            農地を効率的に再配置するための条件を以下のJSONフォーマットで指定してください：

            ```json
            {
                    "ta_farmer_N" : 田の農家総数,
                    "hata_farmer_N" : 畑の農家総数,
                    "ta_exfarmer_ids_and_rates": 田の既存農家IDと割り当て比(整数),
                    "hata_exfarmer_ids_and_rates": 畑の既存農家IDと割り当て比(整数),
            }
            ```

            以下は指定例です：
            田の農家数は5
            畑の農家数は2
            田の既存農家と面積割合は以下の通り
            "2dacba93d45b0f46a25b29b985bd90e2": 3
            "10aad9b486abee43973bb555cc3362c2": 2
            "7db8af145bda49552f855ba395906a2f": 2
            畑の既存農家と面積割合は以下の通り
            "2dacba93d45b0f46a25b29b985bd90e2": 1

            この時JSONは以下のようになります。
            ```json
            {
                "ta_farmer_N": 5,
                "hata_farmer_N": 2,
                "ta_exfarmer_ids_and_rates": {
                    "2dacba93d45b0f46a25b29b985bd90e2": 3,
                    "10aad9b486abee43973bb555cc3362c2": 2,
                    "7db8af145bda49552f855ba395906a2f": 2
                },
                "hata_exfarmer_ids_and_rates": {
                    "2dacba93d45b0f46a25b29b985bd90e2": 1
                }
            }
            ```

            必要な条件をすべて指定してください。
            """,
            "function": reorganize_farmland
        },
        4: {
            "name": "再編成した農地の修正",
            "description": """
            農地の再編成を行うエージェントです。
            特に再編成した農地に関して、特定の区画の所有者と農地の種類を変更したい場合に修正を実行するエージェントです。
            農地の修正をすrための条件を以下のJsonフォーマットで指定してください：
            ```json
            {
                "target_address": "変更したい農地の住所",
                "new_farmer_id": "変更後の農地の所有者のID",
                "new_farm_type": "変更後の農地の種類",
            }
            ```

            以下は指定例です：
            1. 住所が1234の農地の所有者を5678に変更
            2. 住所が1234の農地の種類を田から畑に変更
            3. 住所が1234の農地の所有者を5678に変更し、種類を田から畑に変更
            """,
            "function": fix_reorg
        }
    },
    2:{
        1:{
            "name": "収量予測",
            "description": """
            緯度経度、農作物を入力することによって終了を予測するエージェントです。
            収量予測を行うための条件を以下のJsonフォーマットで指定してください：
            住所が入力された場合、住所から緯度経度を取得してください.
            わからない場合は実行できないので、lat, lonを指定しないでください。
            ```json
            {
                "lat": 緯度,
                "lon": 経度,
                "crop": 作物名
            }
            ```
            作物名はrice, potato, wheatのいずれかを指定してください。
            """,
            "function": crop_simulation
        }
    },
    3: {
        1:{
            "name": "全般",
            "description": """
            今はは未実装です
            """,
            "function": color_farmland
        }
    },
    4: {
        1:{
            "name": "全般",
            "description": """
            今はは未実装です
            """,
            "function": color_farmland
        }
    }
}
