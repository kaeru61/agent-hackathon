import json
from datetime import datetime
from typing import Dict, Any

def update_farmer_info(
    geojson_path: str,
    target_address: str,
    new_farmer_id: str,
    new_land_type: str = None  # 新しい農地の種類（オプション）
) -> Dict[str, Any]:
    """
    GeoJSONファイル内の農地所有者情報と農地種類を更新する

    Args:
        geojson_path (str): 更新対象のGeoJSONファイルパス
        target_address (str): 対象の住所
        new_farmer_id (str): 新しい農家の識別子
        new_land_type (str, optional): 新しい農地の種類 ('1': 田, '2': 畑)

    Returns:
        Dict[str, Any]: 更新結果を含む辞書
            - status: 処理結果のステータス ("success" or "error")
            - message: 処理結果のメッセージ
            - updated_count: 更新された農地の数
            - land_type_updates: 農地種類の更新内容（変更があった場合のみ）
    """
    try:
        # GeoJSONファイルの読み込み
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # バックアップの作成
        backup_path = f'src/app/ref/backup/map-reorg-{datetime.now().strftime("%Y%m%d%H%M%S")}.geojson'
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)

        updated_count = 0
        updates = []

        # 特定の農地の情報を更新
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
                "status": "error",
                "message": f"指定された住所 '{target_address}' に一致する農地が見つかりませんでした。",
                "updated_count": 0
            }

        # 更新したGeoJSONを保存
        with open(geojson_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)

        # メッセージの生成
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

    except Exception as e:
        return {
            "status": "error",
            "message": f"エラーが発生しました: {str(e)}",
            "updated_count": 0
        }