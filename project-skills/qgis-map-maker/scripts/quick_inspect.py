# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from qgis.core import QgsApplication, QgsVectorLayer
import glob, os

qgs = QgsApplication([], False)
qgs.initQgis()

data_dir = r'E:\BaiduNetdiskDownload\制图Data\制图Data\Data2\城市关系强度图'
output_file = os.path.join(os.path.dirname(__file__), 'inspect_result.txt')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f'数据目录: {data_dir}\n')
    f.write(f'目录存在: {os.path.isdir(data_dir)}\n')
    
    shp_files = glob.glob(os.path.join(data_dir, '*.shp'))
    f.write(f'找到 {len(shp_files)} 个shp文件\n\n')
    
    for shp_path in shp_files:
        basename = os.path.basename(shp_path)
        f.write(f'=== {basename} ===\n')
        layer = QgsVectorLayer(shp_path, 'test', 'ogr')
        if layer.isValid():
            geom_names = {0: '点(Point)', 1: '线(Polyline)', 2: '面(Polygon)'}
            f.write(f'  几何类型: {geom_names.get(layer.geometryType(), "未知")}\n')
            f.write(f'  要素数: {layer.featureCount()}\n')
            f.write(f'  CRS: {layer.crs().authid()}\n')
            fields = [fld.name() for fld in layer.fields()]
            f.write(f'  字段: {", ".join(fields)}\n')
            
            # 找可标注字段
            label_candidates = ["NAME", "name", "名称", "市名", "NAME_CHN", "县名", "省名"]
            label_field = None
            for fld in layer.fields():
                if fld.name() in label_candidates:
                    label_field = fld.name()
                    break
            if label_field:
                f.write(f'  [可标注字段: {label_field}]\n')
        else:
            f.write('  图层无效!\n')
        f.write('\n')

qgs.exitQgis()
print(f'探查结果已写入: {output_file}')
