#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸市各县批量地形图生成器
每个县单独出图，统一洛阳风格
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def generate_county_map(county_name, county_geom, dem_path, output_dir):
    """生成单个县的地形图"""
    
    # 创建临时内存图层用于裁剪
    temp_layer = QgsVectorLayer("Polygon?crs=EPSG:32650", "temp_clip", "memory")
    pr = temp_layer.dataProvider()
    feat = QgsFeature()
    feat.setGeometry(county_geom)
    pr.addFeatures([feat])
    
    # 获取该县范围，稍微扩大一点
    extent = county_geom.boundingBox()
    buffer = max(extent.width(), extent.height()) * 0.08
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    # 创建项目
    project = QgsProject.instance()
    project.removeAllMapLayers()
    
    # ==========================================
    # 1. DEM 图层 (6阶黄绿渐变)
    # ==========================================
    dem_layer = QgsRasterLayer(dem_path, "DEM")
    if not dem_layer.isValid():
        print(f"  ✗ DEM 加载失败")
        return False
    
    stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, extent, 0)
    min_val = stats.minimumValue
    max_val = stats.maximumValue
    range_val = max_val - min_val
    
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    color_list = [
        QgsColorRampShader.ColorRampItem(min_val,                      QColor(210, 235, 185)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.20,  QColor(180, 220, 150)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.40,  QColor(140, 195, 115)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.60,  QColor(105, 165, 90)),
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.80,  QColor(75, 135, 70)),
        QgsColorRampShader.ColorRampItem(max_val,                      QColor(55, 105, 50)),
    ]
    shader_func.setColorRampItemList(color_list)
    
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader_func)
    
    renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), 1, raster_shader)
    dem_layer.setRenderer(renderer)
    dem_layer.setOpacity(0.9)
    
    project.addMapLayer(dem_layer)
    
    # ==========================================
    # 2. 县界图层 (裁剪蒙版效果)
    # ==========================================
    mask_layer = QgsVectorLayer("Polygon?crs=EPSG:32650", "县界", "memory")
    pr = mask_layer.dataProvider()
    feat = QgsFeature()
    feat.setGeometry(county_geom)
    pr.addFeatures([feat])
    
    symbol = QgsFillSymbol.createSimple({
        'outline_color': '70, 70, 70, 220',
        'outline_width': '0.8',
        'color': '0,0,0,0',
    })
    mask_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    project.addMapLayer(mask_layer)
    
    # ==========================================
    # 3. 创建布局 (A4 纵向)
    # ==========================================
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(210, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 主地图
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(15, 50, 180, 180)
    map_item.setExtent(extent)
    map_item.setLayers([dem_layer, mask_layer])
    map_item.setBackgroundColor(QColor(245, 248, 245))
    layout.addLayoutItem(map_item)
    
    # 县名标题
    title = QgsLayoutItemLabel(layout)
    title.setText(county_name)
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 28, QFont.Bold))
    text_format.setColor(QColor(40, 80, 40))
    title.setTextFormat(text_format)
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(20, 15, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 高程信息
    elevation_text = f"高程范围: {min_val:.0f}m - {max_val:.0f}m"
    elev_label = QgsLayoutItemLabel(layout)
    elev_label.setText(elevation_text)
    text_format2 = QgsTextFormat()
    text_format2.setFont(QFont("微软雅黑", 11))
    text_format2.setColor(QColor(90, 130, 90))
    elev_label.setTextFormat(text_format2)
    elev_label.adjustSizeToText()
    elev_label.attemptMove(QgsLayoutPoint(20, 45, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(elev_label)
    
    # 指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(18, 28, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(170, 245, QgsUnitTypes.LayoutMillimeters))
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
    scale_bar.attemptMove(QgsLayoutPoint(20, 250, QgsUnitTypes.LayoutMillimeters))
    
    text_format3 = QgsTextFormat()
    text_format3.setFont(QFont("微软雅黑", 8))
    text_format3.setColor(QColor(70, 70, 70))
    scale_bar.setTextFormat(text_format3)
    
    layout.addLayoutItem(scale_bar)
    
    # 底部标注
    footer = QgsLayoutItemLabel(layout)
    footer.setText("DEM: 12m分辨率 | 坐标系: CGCS2000")
    text_format4 = QgsTextFormat()
    text_format4.setFont(QFont("微软雅黑", 7))
    text_format4.setColor(QColor(140, 140, 140))
    footer.setTextFormat(text_format4)
    footer.adjustSizeToText()
    footer.attemptMove(QgsLayoutPoint(20, 275, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer)
    
    # 导出
    os.makedirs(output_dir, exist_ok=True)
    # 处理中文文件名编码
    county_name_clean = county_name.encode('utf-8', errors='ignore').decode('utf-8')
    output_path = os.path.join(output_dir, f"{county_name_clean}_地形图.png")
    
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ {county_name} 导出成功 ({file_size:.1f} MB)")
        return True
    else:
        print(f"  ✗ {county_name} 导出失败")
        return False

def main():
    print("=" * 60)
    print("邯郸市各县地形图批量生成器")
    print("=" * 60)
    
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    # 数据路径
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸县界.shp"
    output_dir = "assets/generated/邯郸各县地形图"
    
    print(f"\nDEM: {dem_path}")
    print(f"区划: {admin_path}")
    print(f"输出: {output_dir}")
    
    # 加载行政区划
    admin_layer = QgsVectorLayer(admin_path, "邯郸各县", "ogr")
    if not admin_layer.isValid():
        import glob
        shps = glob.glob(r"slide-deck\autoclaw-course\县界\*.shp")
        for shp in shps:
            admin_layer = QgsVectorLayer(shp, "邯郸各县", "ogr")
            if admin_layer.isValid():
                break
    
    if not admin_layer.isValid():
        print("  ✗ 行政区划加载失败!")
        return 1
    
    features = list(admin_layer.getFeatures())
    print(f"\n共 {len(features)} 个县级行政区")
    
    # 遍历每个县生成地图
    success_count = 0
    for i, feature in enumerate(features, 1):
        county_name = feature['XZQMC']
        county_geom = feature.geometry()
        
        print(f"\n[{i}/{len(features)}] 正在生成: {county_name}")
        
        if generate_county_map(county_name, county_geom, dem_path, output_dir):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"批量生成完成! 成功: {success_count}/{len(features)}")
    print(f"输出目录: {os.path.abspath(output_dir)}")
    print("=" * 60)
    
    qgs.exitQgis()
    return 0

if __name__ == '__main__':
    sys.exit(main())
