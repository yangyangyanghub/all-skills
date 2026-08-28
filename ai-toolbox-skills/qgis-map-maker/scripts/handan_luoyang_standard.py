#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸市地形图 - 完全复刻洛阳市标准
添加: 山体阴影叠加 + 柔和配色 + 效果增强
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 60)
    print("邯郸市地形图 - 洛阳市标准复刻版")
    print("=" * 60)
    
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    output_dir = r"assets\generated"
    os.makedirs(output_dir, exist_ok=True)
    
    # ==========================================
    # 第一步: 加载 DEM
    # ==========================================
    print("\n[1/6] 加载 DEM...")
    
    dem_layer = QgsRasterLayer(dem_path, "DEM")
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败")
        return 1
    
    stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, dem_layer.extent(), 0)
    min_val = stats.minimumValue
    max_val = stats.maximumValue
    print(f"  高程范围: {min_val:.0f}m - {max_val:.0f}m")
    
    # ==========================================
    # 第二步: 创建山体阴影图层 (Hillshade)
    # ==========================================
    print("\n[2/6] 生成山体阴影...")
    
    # 西北光照 315°，太阳高度 45°
    hillshade_renderer = QgsHillshadeRenderer(dem_layer.dataProvider(), 1, 315, 45)
    hillshade_renderer.setZFactor(1.5)
    
    hillshade_layer = QgsRasterLayer(dem_path, "Hillshade")
    hillshade_layer.setRenderer(hillshade_renderer)
    hillshade_layer.setOpacity(0.35)  # 35% 透明度叠加
    
    print("  ✓ 山体阴影已创建")
    
    # ==========================================
    # 第三步: 柔和黄绿渐变色 (复刻洛阳风格)
    # ==========================================
    print("\n[3/6] 配置柔和配色...")
    
    range_val = max_val - min_val
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    # 洛阳图配色：更柔和的黄绿过渡
    color_list = [
        QgsColorRampShader.ColorRampItem(min_val,                      QColor(225, 240, 200)),  # 浅黄绿 - 平原
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.15,  QColor(200, 230, 170)),  # 淡绿
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.35,  QColor(170, 215, 140)),  # 草绿
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.55,  QColor(130, 190, 115)),  # 翠绿
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.75,  QColor(95, 160, 90)),    # 深绿
        QgsColorRampShader.ColorRampItem(max_val,                      QColor(70, 130, 65)),    # 墨绿 - 山峰
    ]
    shader_func.setColorRampItemList(color_list)
    
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader_func)
    renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), 1, raster_shader)
    dem_layer.setRenderer(renderer)
    dem_layer.setOpacity(0.85)
    
    print("  ✓ 配色配置完成")
    
    # ==========================================
    # 第四步: 邯郸市级整体图布局
    # ==========================================
    print("\n[4/6] 创建地图布局...")
    
    extent = dem_layer.extent()
    buffer = extent.width() * 0.05
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    project = QgsProject.instance()
    project.removeAllMapLayers()
    project.addMapLayer(dem_layer)
    project.addMapLayer(hillshade_layer)
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 主地图
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(15, 25, 390, 250)
    map_item.setExtent(extent)
    map_item.setLayers([dem_layer, hillshade_layer])
    map_item.setBackgroundColor(QColor(245, 248, 245))
    layout.addLayoutItem(map_item)
    
    # ==========================================
    # 第五步: 标题与标注 (复刻洛阳风格)
    # ==========================================
    print("\n[5/6] 添加标题与标注...")
    
    # 主标题: 邯郸市 (冀D)
    title = QgsLayoutItemLabel(layout)
    title.setText("邯郸市 (冀D)")
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 36, QFont.Bold))
    text_format.setColor(QColor(40, 80, 40))
    title.setTextFormat(text_format)
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 副标题诗句风格: 燕赵古都 太行明珠
    sub_title = QgsLayoutItemLabel(layout)
    sub_title.setText("燕赵古都，太行明珠")
    text_format2 = QgsTextFormat()
    text_format2.setFont(QFont("微软雅黑", 20))
    text_format2.setColor(QColor(70, 120, 70))
    sub_title.setTextFormat(text_format2)
    sub_title.adjustSizeToText()
    sub_title.attemptMove(QgsLayoutPoint(20, 45, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(sub_title)
    
    # 指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(22, 36, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(370, 225, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # 比例尺条
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(80, 14, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(330, 260, QgsUnitTypes.LayoutMillimeters))
    
    text_format3 = QgsTextFormat()
    text_format3.setFont(QFont("微软雅黑", 9))
    text_format3.setColor(QColor(60, 60, 60))
    scale_bar.setTextFormat(text_format3)
    # 比例尺配色
    
    layout.addLayoutItem(scale_bar)
    
    # 底部标注
    footer = QgsLayoutItemLabel(layout)
    footer.setText("DEM 分辨率: 12m | 坐标系: WGS84 UTM 50N")
    text_format4 = QgsTextFormat()
    text_format4.setFont(QFont("微软雅黑", 7))
    text_format4.setColor(QColor(140, 140, 140))
    footer.setTextFormat(text_format4)
    footer.adjustSizeToText()
    footer.attemptMove(QgsLayoutPoint(20, 275, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer)
    
    # ==========================================
    # 第六步: 导出
    # ==========================================
    print("\n[6/6] 导出地图...")
    
    output_path = os.path.join(output_dir, "邯郸市_洛阳标准地形图.png")
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    if result == QgsLayoutExporter.Success:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ 导出成功: {output_path}")
        print(f"  ✓ 文件大小: {size_mb:.1f} MB")
        print("\n" + "=" * 60)
        print("邯郸市级标准地形图生成完成!")
        print("=" * 60)
        qgs.exitQgis()
        return 0
    else:
        print(f"  ✗ 导出失败")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
