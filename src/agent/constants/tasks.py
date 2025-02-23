import json
from typing import Dict, Any, List, Union, Callable
from dataclasses import dataclass
from functions.filiter import FieldSearchCriteria, search_fields
import shutil
from datetime import datetime

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
    
def reorganize_farmland(data):
    # 農地の再編成ロジックをここに記述します
    pass

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
            "name": "農地の再編成",
            "description": """
            ユーザーが求める農地の再編成を行うエージェントです。
            今は、ユーザーの要望を要約してください
            """,
            "function": reorganize_farmland
        }
    },
    2:{
        1:{
            "name": "全般",
            "description": """
            今はは未実装です
            """,
            "function": reorganize_farmland
        }
    }
}