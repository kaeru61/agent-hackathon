import json
from typing import Dict, Any, List, Union, Callable
from dataclasses import dataclass
from functions.filiter import FieldSearchCriteria, search_fields

def filter_farmland(json_str) -> List[Dict[str, Any]]:
    """
    JSON文字列から検索条件を解析し、農地検索を実行する。
    検索結果を新しいGeoJSONファイルとして保存する。

    Args:
        json_str (str): JSON形式の検索条件

    Returns:
        List[Dict[str, Any]]: 検索結果の農地データリスト
    """
    try:
        # JSONをパース
        search_params = json_str
        print(search_params)
        
        # 元のGeoJSONファイルを別名で保存
        import shutil
        from datetime import datetime
        
        base_path = "src/app/components/"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"map_backup_{timestamp}.geojson"
        
        # バックアップの作成
        shutil.copy(f"{base_path}map-row.geojson", f"{base_path}{backup_filename}")
        
        # 元のGeoJSONファイルの読み込み
        with open(f"{base_path}map.geojson", 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # FieldSearchCriteriaオブジェクトを作成
        criteria = FieldSearchCriteria(
            farmer_id=search_params.get('farmer_id'),
            land_type=search_params.get('land_type'),
            issue_year=search_params.get('issue_year'),
            area_min=search_params.get('area_min'),
            area_max=search_params.get('area_max'),
            prefecture_code=search_params.get('prefecture_code'),
            city_code=search_params.get('city_code'),
            usage_situation=search_params.get('usage_situation'),
            classification=search_params.get('classification')
        )
        
        # 検索を実行
        results = search_fields(geojson_data, criteria)
        
        # 検索結果を新しいGeoJSONとして保存
        new_geojson = {
            "type": "FeatureCollection",
            "features": results
        }
        
        with open(f"{base_path}map.geojson", 'w', encoding='utf-8') as f:
            json.dump(new_geojson, f, ensure_ascii=False, indent=2)
        
        return results
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing search request: {str(e)}")
    
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
            }
            ```

            以下は検索例です：
            1. 茨城県（08）の1000平方メートル以上の農地を検索
            2. 特定の農家（farmer_id指定）が所有する遊休農地を検索
            3. 市街化調整区域内の田を検索

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