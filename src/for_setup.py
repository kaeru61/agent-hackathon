import os
import shutil
# backupフォルダを作る
os.mkdir('src/app/ref/backup')

# map-row.geojsonをコピーしてmap.geojsonとmap-reorg.geojsonを作る
src_path = 'src/app/ref/map-row.geojson'
map_path = 'src/app/ref/map.geojson'
reorg_path = 'src/app/ref/map-reorg.geojson'
shutil.copy(src_path, map_path)
print(f"ファイルをコピーしました: {src_path} -> {map_path}")
shutil.copy(src_path, reorg_path)
print(f"ファイルをコピーしました: {src_path} -> {reorg_path}")
