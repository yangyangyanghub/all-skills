#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 DEM 地形晕渲图
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    project = QgsProject.instance()
    
    # DEM 文件路径
    dem_path = r"slide-deck\autoclaw-course\Data4\DEM10m.tif"
    
    print("正在加载 DEM 图层...")
    dem_layer = QgsRasterLayer(dem_path, "DEM")
    
    if not dem_layer.isValid():
        print("DEM 图层加载失败!")
        return 1
    
    print("DEM 图层加载成功!")
    print(f"  范围: {dem_layer.extent()}")
    print(f"  波段数: {dem_layer.bandCount()}")
    print(f"  CRS: {dem_layer.crs().authid()}")
    
    # 添加到项目
    project.addMapLayer(dem_layer)
    
    # 简单的单波段灰度渲染
    renderer = QgsSingleBandGrayRenderer(dem_layer.dataProvider(), 1)
    dem_layer.setRenderer(renderer)
    
    # 获取范围
    extent = dem_layer.extent()
    
    # 创建布局
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    
    # A3 横向
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 添加地图项
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(10, 10, 400, 270)
    map_item.setExtent(extent)
    map_item.setLayers([dem_layer])
    layout.addLayoutItem(map_item)
    
    # 确保目录存在
    os.makedirs("assets/generated", exist_ok=True)
    
    # 导出
    output_path = "assets/generated/simple_dem_map.png"
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    print(f"\n正在导出到: {output_path}")
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        print("✓ 导出成功!")
        qgs.exitQgis()
        return 0
    else:
        print(f"✗ 导出失败，错误码: {result}")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
