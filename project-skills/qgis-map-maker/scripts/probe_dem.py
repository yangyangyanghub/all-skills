import os, sys
from qgis.core import *

QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.40.9/apps/qgis-ltr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

for dem_path in sys.argv[1:]:
    if not os.path.exists(dem_path):
        print(f"{dem_path}: NOT FOUND")
        continue
    layer = QgsRasterLayer(dem_path, os.path.basename(dem_path))
    if not layer.isValid():
        print(f"{os.path.basename(dem_path)}: INVALID")
        continue
    stats = layer.dataProvider().bandStatistics(1)
    base = os.path.basename(dem_path)
    print(f"FILE: {base}")
    print(f"  CRS: {layer.crs().authid()}")
    print(f"  Width: {layer.width()}, Height: {layer.height()}")
    print(f"  Min: {stats.minimumValue:.2f}, Max: {stats.maximumValue:.2f}")
    print(f"  Range: {stats.maximumValue - stats.minimumValue:.2f}")
    print()

qgs.exitQgis()
