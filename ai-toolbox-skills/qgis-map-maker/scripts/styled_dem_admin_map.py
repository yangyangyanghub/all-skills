#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风格化 DEM 地形晕渲 + 行政区划图
参考洛阳市地图风格制作
"""

import os
import sys
import glob
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt

def get_shapefiles(data_dir):
    """获取目录下所有 shp 文件"""
    shps = []
    for ext in ['*.shp', '*.SHP']:
        shps.extend(glob.glob(os.path.join(data_dir, ext)))
    return shps

def main():
    print("=" * 50)
    print("风格化 DEM 地形晕渲行政区划图")
    print("=" * 50)
    
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    project = QgsProject.instance()
    
    # ==========================================
    # 第一步: 加载 DEM 并做地形晕渲
    # ==========================================
    print("\n[1/4] 加载 DEM 地形数据...")
    dem_path = r"slide-deck\autoclaw-course\Data4\DEM10m.tif"
    dem_layer = QgsRasterLayer(dem_path, "DEM_地形")
    
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败")
        return 1
    
    print(f"  ✓ DEM 范围: {dem_layer.extent()}")
    print(f"  ✓ CRS: {dem_layer.crs().authid()}")
    
    # 获取统计信息用于配色
    provider = dem_layer.dataProvider()
    stats = provider.bandStatistics(1, QgsRasterBandStats.All, dem_layer.extent(), 0)
    min_val = stats.minimumValue
    max_val = stats.maximumValue
    print(f"  ✓ 高程范围: {min_val:.1f}m - {max_val:.1f}m")
    
    # 绿色系渐变配色
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    # 计算色阶位置
    range_val = max_val - min_val
    color_list = [
        QgsColorRampShader.ColorRampItem(min_val, QColor(190, 230, 160)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.2, QColor(160, 215, 130)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.4, QColor(130, 195, 100)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.6, QColor(100, 170, 80)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.8, QColor(70, 140, 60)),
        QgsColorRampShader.ColorRampItem(max_val, QColor(50, 110, 45)),
    ]
    shader_func.setColorRampItemList(color_list)
    
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader_func)
    
    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, raster_shader)
    dem_layer.setRenderer(renderer)
    dem_layer.setOpacity(0.9)
    
    project.addMapLayer(dem_layer)
    print("  ✓ DEM 地形着色完成")
    
    # ==========================================
    # 第二步: 加载行政区划图层
    # ==========================================
    print("\n[2/4] 加载行政区划数据...")
    
    admin_dir = r"slide-deck\autoclaw-course\Data1"
    shp_files = get_shapefiles(admin_dir)
    
    layers = [dem_layer]  # DEM 放在最底层
    
    for shp in shp_files:
        name = os.path.splitext(os.path.basename(shp))[0]
        layer = QgsVectorLayer(shp, name, "ogr")
        
        if not layer.isValid():
            continue
        
        geom_type = layer.geometryType()
        
        if geom_type == QgsWkbTypes.PolygonGeometry:
            # 面图层 - 行政区划边界
            symbol = QgsFillSymbol.createSimple({
                'outline_color': '70, 70, 70, 180',
                'outline_width': '0.6',
                'color': '0,0,0,0',
            })
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))
            project.addMapLayer(layer)
            layers.append(layer)
            print(f"  ✓ 添加面图层: {name} ({layer.featureCount()} 个要素)")
        
        elif geom_type == QgsWkbTypes.LineGeometry:
            # 线图层 - 水系/道路
            symbol = QgsLineSymbol.createSimple({
                'color': '80, 140, 200, 160',
                'width': '0.4',
            })
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))
            project.addMapLayer(layer)
            layers.append(layer)
            print(f"  ✓ 添加线图层: {name} ({layer.featureCount()} 个要素)")
    
    # ==========================================
    # 第三步: 创建地图布局
    # ==========================================
    print("\n[3/4] 创建地图布局...")
    
    extent = dem_layer.extent()
    buffer = extent.width() * 0.03
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    
    # A3 横向
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 添加主地图
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(15, 25, 390, 255)
    map_item.setExtent(extent)
    map_item.setLayers(layers)
    map_item.setBackgroundColor(QColor(245, 250, 245))
    layout.addLayoutItem(map_item)
    
    # 标题
    title = QgsLayoutItemLabel(layout)
    title.setText("行政区划地形图")
    # 设置标题字体
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 24, QFont.Bold))
    text_format.setColor(QColor(40, 80, 40))
    title.setTextFormat(text_format)
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(25, 8, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(18, 28, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(380, 250, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # 比例尺
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(60, 12, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(25, 260, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale_bar)
    
    # ==========================================
    # 第四步: 导出地图
    # ==========================================
    print("\n[4/4] 导出地图...")
    
    os.makedirs("assets/generated", exist_ok=True)
    output_path = "assets/generated/styled_admin_dem_map.png"
    
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        print(f"  ✓ 地图已导出: {output_path}")
        print("\n" + "=" * 50)
        print("生成完成!")
        print("=" * 50)
        qgs.exitQgis()
        return 0
    else:
        print(f"  ✗ 导出失败，错误码: {result}")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
