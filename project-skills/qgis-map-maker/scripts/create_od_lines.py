# -*- coding: utf-8 -*-
"""
将 Excel 中的城市关系 OD 数据转换为线状 Shapefile
支持城市名称模糊匹配（如"白城"→"白城市"）
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from qgis.core import QgsApplication
_qgs = QgsApplication([], False)
_qgs.initQgis()

from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsField, QgsFields, QgsVectorFileWriter,
    QgsWkbTypes
)
from PyQt5.QtCore import QVariant
import pandas as pd
import os

# --- 配置 ---
data_dir = r'E:\BaiduNetdiskDownload\制图Data\制图Data\Data2\城市关系强度图'
excel_path = os.path.join(data_dir, '城市关系强度.xlsx')
point_shp = os.path.join(data_dir, '市_点_p.shp')
output_shp = os.path.join(data_dir, '城市关系连线_p.shp')

# 1. 读取城市点坐标
print("📍 读取城市点位数据...")
point_layer = QgsVectorLayer(point_shp, 'cities', 'ogr')
city_coords = {}
city_keys = []  # 简化后的名称用于匹配
for feat in point_layer.getFeatures():
    name = feat.attribute('NAME')
    geom = feat.geometry().asPoint()
    city_coords[name] = (geom.x(), geom.y())
    # 提取关键词：去掉"市"、"朝鲜族自治州"等后缀
    key = name.replace('市', '').replace('朝鲜族自治州', '').replace('地区', '').replace('盟', '')
    city_keys.append((key, name))
    print(f"   {name} -> 匹配键: '{key}'")

print(f"\n共找到 {len(city_coords)} 个城市坐标点")

# 城市名匹配函数
def find_city(name):
    """精确匹配 -> 去除'市'后缀匹配 -> 包含匹配"""
    name = str(name).strip()
    # 1. 精确匹配
    if name in city_coords:
        return name
    # 2. 加上"市"再匹配
    if name + '市' in city_coords:
        return name + '市'
    # 3. 关键词匹配（如"延边"->"延边朝鲜族自治州"）
    for key, full_name in city_keys:
        if name in key or key in name:
            print(f"   ~~ 模糊匹配: '{name}' -> '{full_name}'")
            return full_name
    # 4. 包含匹配
    for full_name in city_coords:
        if name in full_name or full_name in name:
            print(f"   ~~ 包含匹配: '{name}' -> '{full_name}'")
            return full_name
    return None

# 2. 读取 Excel 关系数据
print("\n📊 读取关系强度数据...")
df = pd.read_excel(excel_path)
print(f"共 {len(df)} 条关系记录")
print(f"城市A 唯一值: {df['城市A'].unique().tolist()}")
print(f"城市B 唯一值: {df['城市B'].unique().tolist()}")

# 3. 创建线 Shapefile
print(f"\n🔗 生成连线 Shapefile...")

fields = QgsFields()
fields.append(QgsField('origin', QVariant.String))
fields.append(QgsField('destinatio', QVariant.String))  # Shapefile 字段名限10字符
fields.append(QgsField('strength', QVariant.Double))

writer = QgsVectorFileWriter(
    output_shp,
    'UTF-8',
    fields,
    QgsWkbTypes.LineString,
    point_layer.crs(),
    'ESRI Shapefile'
)

connected_count = 0
skipped_count = 0
for _, row in df.iterrows():
    origin_raw = str(row['城市A']).strip()
    dest_raw = str(row['城市B']).strip()
    strength = float(row['城市强度'])
    
    origin = find_city(origin_raw)
    dest = find_city(dest_raw)
    
    if origin and dest and origin in city_coords and dest in city_coords:
        x1, y1 = city_coords[origin]
        x2, y2 = city_coords[dest]
        
        line = QgsGeometry.fromPolylineXY([QgsPointXY(x1, y1), QgsPointXY(x2, y2)])
        
        feat = QgsFeature()
        feat.setGeometry(line)
        feat.setAttributes([origin, dest[:10], strength])
        writer.addFeature(feat)
        connected_count += 1
        print(f"   OK {origin_raw}({origin}) -> {dest_raw}({dest}) 强度:{strength}")
    else:
        print(f"   XX 跳过: {origin_raw} -> {dest_raw} (找不到坐标)")
        skipped_count += 1

writer.flushBuffer()
del writer

print(f"\n✅ 生成完成!")
print(f"   OK 成功连线: {connected_count} 条")
print(f"   XX 跳过: {skipped_count} 条")

_qgs.exitQgis()
