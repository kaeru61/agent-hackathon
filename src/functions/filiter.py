from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class FieldSearchCriteria:
    """農地検索条件を定義するデータクラス"""
    farmer_id: Optional[str] = None
    land_type: Optional[int] = None
    issue_year: Optional[int] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    prefecture_code: Optional[str] = None
    city_code: Optional[str] = None
    usage_situation: Optional[str] = None
    classification: Optional[str] = None  # 田、畑などの区分

def search_fields(
    geojson_data: Dict[str, Any],
    criteria: FieldSearchCriteria
) -> List[Dict[str, Any]]:
    """
    GeoJSONデータから指定された条件に合致する農地データを検索する

    Args:
        geojson_data (Dict): 検索対象のGeoJSONデータ
        criteria (FieldSearchCriteria): 検索条件

    Returns:
        List[Dict]: 条件に合致する農地データのリスト
    """
    results = []
    
    for feature in geojson_data.get('features', []):
        properties = feature.get('properties', {})
        
        if _matches_criteria(properties, criteria):
            results.append(feature)
    
    return results

def _matches_criteria(properties: Dict[str, Any], criteria: FieldSearchCriteria) -> bool:
    """
    プロパティが検索条件に一致するかチェックする
    
    Args:
        properties (Dict): 検査対象のプロパティ
        criteria (FieldSearchCriteria): 検索条件
    
    Returns:
        bool: すべての条件に一致する場合True
    """
    # 各条件をチェック（Noneの場合はその条件をスキップ）
    if (criteria.farmer_id and 
        properties.FarmerIndicationNumberHash != criteria.farmer_id):
        return False
        
    if criteria.land_type and properties.get('land_type') != criteria.land_type:
        return False
        
    if criteria.issue_year and properties.get('issue_year') != criteria.issue_year:
        return False
        
    area = float(properties.get('AreaOnRegistry', 0))
    if criteria.area_min and area < criteria.area_min:
        return False
    if criteria.area_max and area > criteria.area_max:
        return False
        
    if (criteria.prefecture_code and 
        properties.get('TodofukenCode') != criteria.prefecture_code):
        return False
        
    if criteria.city_code and properties.get('ShikuchosonCode') != criteria.city_code:
        return False
        
    if (criteria.usage_situation and 
        properties.get('UsageSituationInvestigationResultCodeName') != criteria.usage_situation):
        return False
        
    if (criteria.classification and 
        properties.get('ClassificationOfLandCodeName') != criteria.classification):
        return False
        
    return True
