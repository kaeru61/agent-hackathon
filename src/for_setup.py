import os
import shutil
# backupフォルダがない時、作成する
if not os.path.exists('backup'):
    os.makedirs('backup')
    print("backupフォルダを作成しました")


# map-row.geojsonをコピーしてmap.geojsonとmap-reorg.geojsonを作る
src_path = 'src/app/ref/map-row.geojson'
map_path = 'src/app/ref/map.geojson'
reorg_path = 'src/app/ref/map-reorg.geojson'
shutil.copy(src_path, map_path)
print(f"ファイルをコピーしました: {src_path} -> {map_path}")
shutil.copy(src_path, reorg_path)
print(f"ファイルをコピーしました: {src_path} -> {reorg_path}")
