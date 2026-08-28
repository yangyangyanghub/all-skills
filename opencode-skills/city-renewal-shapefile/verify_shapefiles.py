#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import fiona
import os

print("=" * 70)
print("84个Shapefile完整性验证")
print("=" * 70)
print()

# 统计文件
shp_files = [f for f in os.listdir('.') if f.endswith('.shp')]
print(f"总文件数: {len(shp_files)}")
print()

# 验证关键文件
test_files = [
    ('FCTZF.shp', 'Polygon', 19, '非成套住房'),
    ('CJWXZF.shp', 'Point', 15, 'C级危险住房'),
    ('CZLJXQ.shp', 'Polygon', 20, '2000年底前建成的城镇老旧小区'),
    ('LJCQ.shp', 'Polygon', 27, '老旧厂区'),
    ('LJCF.shp', 'Point', 28, '老旧厂房'),
    ('ZGD.shp', 'LineString', 13, '主干道'),
    ('RQGX.shp', 'LineString', 12, '燃气管线'),
    ('XFZ.shp', 'Point', 12, '消防站'),
    ('YY.shp', 'Point', 12, '医院'),
    ('BJDCHDJXD.shp', 'Polygon', 16, '未利用边角地、插花地、夹心地'),
    ('MXXT.shp', 'LineString', 16, '需要改造提升的慢行系统'),
    ('BHTSLSJZ.shp', 'Point', 20, '需要保护提升的历史建筑'),
    ('GYYC.shp', 'Polygon', 20, '工业遗产'),
    ('XZRFGC.shp', 'Point', 13, '闲置人防工程'),
]

print("关键文件验证:")
print("-" * 70)
for filename, expected_geom, expected_fields, name in test_files:
    if os.path.exists(filename):
        with fiona.open(filename) as src:
            actual_geom = src.schema['geometry']
            actual_fields = len(src.schema['properties'])
            geom_ok = "OK" if actual_geom == expected_geom else "FAIL"
            fields_ok = "OK" if actual_fields == expected_fields else "FAIL"
            print(f"{name:30s} | 几何: {geom_ok:4s} | 字段: {fields_ok:4s} | {actual_fields}个字段")
    else:
        print(f"{name:30s} | 文件不存在")

print()
print("=" * 70)
print("验证完成")
print("=" * 70)
