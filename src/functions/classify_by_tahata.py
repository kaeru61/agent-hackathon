import geopandas as gpd
from typing import Dict, Any

def classify_by_tahata(geojson_data: Dict[str, Any],):
  """農地のデータを田畑ごとに分類する

  Args:
      geojson_data (Dict): 分類対象のGeoJSONデータ
  """
  gdf = gpd.GeoDataFrame.from_features(geojson_data)
