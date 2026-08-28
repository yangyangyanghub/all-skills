#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸各县地形图批量生成
组合方案: QGIS CLI (数据处理) + PyQGIS (地图布局)
"""

import os
import sys
import subprocess
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def run_qgis_cli(algorithm, args):
    """运行 QGIS CLI 命令"""
    cmd = [
        r"C:\Program Files\QGIS 3.40.9\bin\qgis_process-qgis-ltr.bat",
        "run", algorithm
    ] + args
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def main():
    print("=" * 60)
    print("邯郸各县地形图 - QGIS CLI + PyQGIS 组合方案")
    print("=" * 60)
    
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸县界.shp"
    output_dir = r"assets\generated\邯郸各县地形图_最终版"
    os.makedirs(output_dir, exist_ok=True)
    
    # ==========================================
    # 第一步: 用 QGIS CLI 预处理 DEM
    # ==========================================
    print("\n[1/4] QGIS CLI - DEM 配色渲染...")
    color_table = os.path.abspath(r"assets\generated\luoyang_style_colors.txt")
    colored_dem = os.path.join(output_dir, "_dem_colored.tif")
    
    success = run_qgis_cli("gdal:colorrelief", [
        f"--INPUT={dem_path}",
        f"--COLOR_TABLE={color_table}",
        f"--MATCH_MODE=2",
        f"--OUTPUT={colored_dem}"
    ])
    
    if success:
        print("  ✓ DEM 配色完成")
    else:
        print("  ⚠  配色跳过，使用原始 DEM")
        colored_dem = dem_path
    
    # ==========================================
    # 第二步: 加载图层
    # ==========================================
    print("\n[2/4] 加载数据...")
    
    dem_layer = QgsRasterLayer(colored_dem, "DEM")
    admin_layer = QgsVectorLayer(admin_path, "县界", "ogr")
    
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败")
        return 1
    
    if not admin_layer.isValid():
        print("  ✗ 行政区划加载失败")
        return 1
    
    print(f"  ✓ 共 {admin_layer.featureCount()} 个县级行政区")
    
    # ==========================================
    # 第三步: 遍历每个县生成地图
    # ==========================================
    print("\n[3/4] 批量生成各县地图...")
    
    features = list(admin_layer.getFeatures())
    success_count = 0
    
    for i, feature in enumerate(features, 1):
        county_name = feature['XZQMC']
        county_geom = feature.geometry()
        
        print(f"\n  [{i}/{len(features)}] {county_name}")
        
        # 创建临时裁剪图层
        clip_layer = QgsVectorLayer("Polygon?crs=EPSG:32650", "clip", "memory")
        pr = clip_layer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(county_geom)
        pr.addFeatures([feat])
        
        # 获取该县范围
        extent = county_geom.boundingBox()
        buffer = max(extent.width(), extent.height()) * 0.08
        extent.setXMinimum(extent.xMinimum() - buffer)
        extent.setXMaximum(extent.xMaximum() + buffer)
        extent.setYMinimum(extent.yMinimum() - buffer)
        extent.setYMaximum(extent.yMaximum() + buffer)
        
        # 为每个县重新加载 DEM（避免对象生命周期问题）
        dem_local = QgsRasterLayer(colored_dem, "DEM")
        if not dem_local.isValid():
            dem_local = QgsRasterLayer(dem_path, "DEM")
        
        # 创建项目
        project = QgsProject.instance()
        project.removeAllMapLayers()
        project.addMapLayer(dem_local)
        project.addMapLayer(clip_layer)
        
        # 县界样式
        symbol = QgsFillSymbol.createSimple({
            'outline_color': '70, 70, 70, 220',
            'outline_width': '0.8',
            'color': '0,0,0,0',
        })
        clip_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        
        # 创建布局
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        page = layout.pageCollection().pages()[0]
        page.setPageSize(QgsLayoutSize(210, 297, QgsUnitTypes.LayoutMillimeters))
        
        # 主地图
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(15, 50, 180, 180)
        map_item.setExtent(extent)
        map_item.setLayers([dem_layer, clip_layer])
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
        
        # 高程范围
        stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, extent, 0)
        elev_text = f"高程范围: {stats.minimumValue:.0f}m - {stats.maximumValue:.0f}m"
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
        
        # 底部标注
        footer = QgsLayoutItemLabel(layout)
        footer.setText("DEM: 12m | 坐标系: CGCS2000")
        text_format4 = QgsTextFormat()
        text_format4.setFont(QFont("微软雅黑", 7))
        text_format4.setColor(QColor(140, 140, 140))
        footer.setTextFormat(text_format4)
        footer.adjustSizeToText()
        footer.attemptMove(QgsLayoutPoint(20, 275, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(footer)
        
        # 导出
        output_path = os.path.join(output_dir, f"{county_name}_地形图.png")
        exporter = QgsLayoutExporter(layout)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = 300
        
        result = exporter.exportToImage(output_path, settings)
        if result == QgsLayoutExporter.Success:
            file_size = os.path.getsize(output_path) / 1024
            print(f"    ✓ 成功 ({file_size:.0f} KB)")
            success_count += 1
        else:
            print(f"    ✗ 失败")
    
    # ==========================================
    # 完成
    # ==========================================
    print("\n" + "=" * 60)
    print(f"生成完成! 成功: {success_count}/{len(features)}")
    print(f"输出目录: {os.path.abspath(output_dir)}")
    print("=" * 60)
    
    qgs.exitQgis()
    return 0

if __name__ == '__main__':
    sys.exit(main())
