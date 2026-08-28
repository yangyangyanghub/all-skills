#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版批量生成脚本
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 50)
    print("邯郸各县地形图批量生成")
    print("=" * 50)
    
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸县界.shp"
    output_dir = r"assets\generated\邯郸各县_最终版"
    os.makedirs(output_dir, exist_ok=True)
    
    admin_layer = QgsVectorLayer(admin_path, "县界", "ogr")
    if not admin_layer.isValid():
        import glob
        for shp in glob.glob(r"slide-deck\autoclaw-course\县界\*.shp"):
            admin_layer = QgsVectorLayer(shp, "县界", "ogr")
            if admin_layer.isValid():
                break
    
    features = list(admin_layer.getFeatures())
    print(f"共 {len(features)} 个县级行政区")
    
    for i, feature in enumerate(features, 1):
        county_name = feature['XZQMC']
        print(f"\n[{i}/{len(features)}] {county_name}")
        
        county_geom = feature.geometry()
        extent = county_geom.boundingBox()
        buffer = max(extent.width(), extent.height()) * 0.08
        extent.setXMinimum(extent.xMinimum() - buffer)
        extent.setXMaximum(extent.xMaximum() + buffer)
        extent.setYMinimum(extent.yMinimum() - buffer)
        extent.setYMaximum(extent.yMaximum() + buffer)
        
        # 每次重新加载
        dem = QgsRasterLayer(dem_path, "DEM")
        
        # 6阶黄绿渐变配色
        stats = dem.dataProvider().bandStatistics(1, QgsRasterBandStats.All, extent, 0)
        min_val = stats.minimumValue
        max_val = stats.maximumValue
        range_val = max_val - min_val
        
        shader_func = QgsColorRampShader()
        shader_func.setColorRampType(QgsColorRampShader.Interpolated)
        color_list = [
            QgsColorRampShader.ColorRampItem(min_val, QColor(210, 235, 185)),
            QgsColorRampShader.ColorRampItem(min_val + range_val * 0.2, QColor(180, 220, 150)),
            QgsColorRampShader.ColorRampItem(min_val + range_val * 0.4, QColor(140, 195, 115)),
            QgsColorRampShader.ColorRampItem(min_val + range_val * 0.6, QColor(105, 165, 90)),
            QgsColorRampShader.ColorRampItem(min_val + range_val * 0.8, QColor(75, 135, 70)),
            QgsColorRampShader.ColorRampItem(max_val, QColor(55, 105, 50)),
        ]
        shader_func.setColorRampItemList(color_list)
        
        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(shader_func)
        renderer = QgsSingleBandPseudoColorRenderer(dem.dataProvider(), 1, raster_shader)
        dem.setRenderer(renderer)
        dem.setOpacity(0.9)
        
        # 县界图层
        mask = QgsVectorLayer("Polygon?crs=EPSG:32650", "县界", "memory")
        pr = mask.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(county_geom)
        pr.addFeatures([feat])
        
        symbol = QgsFillSymbol.createSimple({
            'outline_color': '70,70,70,220',
            'outline_width': '0.8',
            'color': '0,0,0,0',
        })
        mask.setRenderer(QgsSingleSymbolRenderer(symbol))
        
        # 布局
        project = QgsProject.instance()
        project.removeAllMapLayers()
        project.addMapLayer(dem)
        project.addMapLayer(mask)
        
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        page = layout.pageCollection().pages()[0]
        page.setPageSize(QgsLayoutSize(210, 297, QgsUnitTypes.LayoutMillimeters))
        
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(15, 50, 180, 180)
        map_item.setExtent(extent)
        map_item.setLayers([dem, mask])
        map_item.setBackgroundColor(QColor(245, 248, 245))
        layout.addLayoutItem(map_item)
        
        # 标题
        title = QgsLayoutItemLabel(layout)
        title.setText(county_name)
        text_format = QgsTextFormat()
        text_format.setFont(QFont("微软雅黑", 28, QFont.Bold))
        text_format.setColor(QColor(40, 80, 40))
        title.setTextFormat(text_format)
        title.adjustSizeToText()
        title.attemptMove(QgsLayoutPoint(20, 15, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(title)
        
        # 高程
        elev_text = f"高程范围: {min_val:.0f}m - {max_val:.0f}m"
        elev_label = QgsLayoutItemLabel(layout)
        elev_label.setText(elev_text)
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
        
        # 导出
        output_path = os.path.join(output_dir, f"{county_name}_地形图.png")
        exporter = QgsLayoutExporter(layout)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = 300
        
        result = exporter.exportToImage(output_path, settings)
        if result == QgsLayoutExporter.Success:
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  ✓ 成功 ({size_kb:.0f} KB)")
        else:
            print(f"  ✗ 失败")
    
    print("\n" + "=" * 50)
    print(f"输出目录: {os.path.abspath(output_dir)}")
    print("=" * 50)
    
    qgs.exitQgis()
    return 0

if __name__ == '__main__':
    sys.exit(main())
