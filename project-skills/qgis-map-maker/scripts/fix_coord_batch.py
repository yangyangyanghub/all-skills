#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸各县地形图 - 修复坐标系版本
问题：DEM (UTM50N) vs 行政区划 (CGCS2000 3度带38)
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 60)
    print("邯郸各县地形图 - 坐标系修复版")
    print("=" * 60)
    
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸县界.shp"
    output_dir = r"assets\generated\邯郸各县_修复版"
    os.makedirs(output_dir, exist_ok=True)
    
    # ==========================================
    # 第一步: 先转换行政区划坐标系到 UTM50N
    # ==========================================
    print("\n[1/5] 转换行政区划坐标系...")
    
    admin_layer = QgsVectorLayer(admin_path, "县界_原", "ogr")
    if not admin_layer.isValid():
        import glob
        for shp in glob.glob(r"slide-deck\autoclaw-course\县界\*.shp"):
            admin_layer = QgsVectorLayer(shp, "县界_原", "ogr")
            if admin_layer.isValid():
                break
    
    print(f"  原坐标系: {admin_layer.crs().authid()}")
    
    # 转换到 DEM 的坐标系 (EPSG:32650 - WGS84 UTM 50N)
    target_crs = QgsCoordinateReferenceSystem("EPSG:32650")
    transform_context = QgsProject.instance().transformContext()
    
    # 创建新的内存图层
    admin_utm = QgsVectorLayer("Polygon?crs=EPSG:32650", "县界_UTM", "memory")
    pr = admin_utm.dataProvider()
    
    # 复制字段
    pr.addAttributes(admin_layer.fields())
    admin_utm.updateFields()
    
    # 转换每个要素
    count = 0
    for feat in admin_layer.getFeatures():
        geom = feat.geometry()
        # 坐标变换
        xform = QgsCoordinateTransform(admin_layer.crs(), target_crs, transform_context)
        geom.transform(xform)
        
        new_feat = QgsFeature(feat)
        new_feat.setGeometry(geom)
        pr.addFeatures([new_feat])
        count += 1
    
    print(f"  ✓ 转换完成，共 {count} 个要素")
    print(f"  新坐标系: {admin_utm.crs().authid()}")
    
    # ==========================================
    # 第二步: 加载 DEM 验证
    # ==========================================
    print("\n[2/5] 加载 DEM...")
    
    dem_layer = QgsRasterLayer(dem_path, "DEM")
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败")
        return 1
    
    dem_extent = dem_layer.extent()
    print(f"  DEM 范围: {dem_extent}")
    print(f"  DEM CRS: {dem_layer.crs().authid()}")
    
    stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, dem_extent, 0)
    print(f"  DEM 原始高程: {stats.minimumValue:.0f}m - {stats.maximumValue:.0f}m")
    
    # ==========================================
    # 第三步: 遍历每个县生成地图
    # ==========================================
    print("\n[3/5] 批量生成各县地图...")
    
    features = list(admin_utm.getFeatures())
    success_count = 0
    
    for i, feature in enumerate(features, 1):
        county_name = feature['XZQMC']
        county_geom = feature.geometry()
        county_extent = county_geom.boundingBox()
        
        print(f"\n  [{i}/{len(features)}] {county_name}")
        print(f"    范围: {county_extent}")
        
        # 检查该县是否在 DEM 范围内
        if not dem_extent.intersects(county_extent):
            print(f"    ⚠  警告: 该县范围与 DEM 不相交!")
            print(f"    该县中心: {county_extent.center().x():.0f}, {county_extent.center().y():.0f}")
            print(f"    DEM 中心: {dem_extent.center().x():.0f}, {dem_extent.center().y():.0f}")
        
        # 扩展范围用于显示
        buffer = max(county_extent.width(), county_extent.height()) * 0.08
        extent = QgsRectangle(
            county_extent.xMinimum() - buffer,
            county_extent.yMinimum() - buffer,
            county_extent.xMaximum() + buffer,
            county_extent.yMaximum() + buffer
        )
        
        # 获取该县高程统计
        county_stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, extent, 0)
        min_val = county_stats.minimumValue
        max_val = county_stats.maximumValue
        print(f"    高程范围: {min_val:.0f}m - {max_val:.0f}m")
        
        # 每次循环重新加载 DEM
        dem_local = QgsRasterLayer(dem_path, "DEM")
        
        # 6阶黄绿渐变配色
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
        renderer = QgsSingleBandPseudoColorRenderer(dem_local.dataProvider(), 1, raster_shader)
        dem_local.setRenderer(renderer)
        dem_local.setOpacity(0.9)
        
        # 县界图层
        clip_layer = QgsVectorLayer("Polygon?crs=EPSG:32650", "县界", "memory")
        pr_clip = clip_layer.dataProvider()
        feat_clip = QgsFeature()
        feat_clip.setGeometry(county_geom)
        pr_clip.addFeatures([feat_clip])
        
        symbol = QgsFillSymbol.createSimple({
            'outline_color': '70,70,70,220',
            'outline_width': '0.8',
            'color': '0,0,0,0',
        })
        clip_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        
        # 创建项目和布局
        project = QgsProject.instance()
        project.removeAllMapLayers()
        project.addMapLayer(dem_local)
        project.addMapLayer(clip_layer)
        
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        page = layout.pageCollection().pages()[0]
        page.setPageSize(QgsLayoutSize(210, 297, QgsUnitTypes.LayoutMillimeters))
        
        # 主地图
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(15, 50, 180, 180)
        map_item.setExtent(extent)
        map_item.setCrs(target_crs)
        map_item.setLayers([dem_local, clip_layer])
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
        
        # 底部标注
        footer = QgsLayoutItemLabel(layout)
        footer.setText("DEM: 12m | 坐标系: WGS84 UTM 50N")
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
            size_kb = os.path.getsize(output_path) / 1024
            print(f"    ✓ 成功 ({size_kb:.0f} KB)")
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
