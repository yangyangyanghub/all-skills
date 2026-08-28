#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸市地形图 - 1:1 复刻洛阳市视觉风格
包含: 6阶黄绿DEM + 山体阴影 + 县级区划 + 标注 + 标题格式
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 60)
    print("邯郸市地形图 - 1:1 复刻洛阳市风格")
    print("=" * 60)
    
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    project = QgsProject.instance()
    
    # ==========================================
    # 第一步: 加载 DEM (底层)
    # ==========================================
    print("\n[1/7] 加载 DEM 地形数据...")
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    dem_layer = QgsRasterLayer(dem_path, "DEM_地形底图")
    
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败!")
        return 1
    
    print(f"  ✓ 高程范围: {dem_layer.dataProvider().bandStatistics(1).minimumValue:.0f}m "
          f"- {dem_layer.dataProvider().bandStatistics(1).maximumValue:.0f}m")
    
    # ==========================================
    # 第二步: 配置 6 阶黄绿渐变配色
    # ==========================================
    print("\n[2/7] 配置 6 阶黄绿渐变配色...")
    
    min_val = dem_layer.dataProvider().bandStatistics(1).minimumValue
    max_val = dem_layer.dataProvider().bandStatistics(1).maximumValue
    range_val = max_val - min_val
    
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    # 精确复刻洛阳配色: 浅黄绿 → 淡绿 → 草绿 → 深绿 → 墨绿 → 暗绿
    color_list = [
        QgsColorRampShader.ColorRampItem(min_val,                      QColor(210, 235, 185)),  # 河谷平原
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.20,  QColor(180, 220, 150)),  # 缓坡
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.40,  QColor(140, 195, 115)),  # 低山
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.60,  QColor(105, 165, 90)),   # 中山
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.80,  QColor(75, 135, 70)),    # 高山
        QgsColorRampShader.ColorRampItem(max_val,                      QColor(55, 105, 50)),    # 山峰
    ]
    shader_func.setColorRampItemList(color_list)
    
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader_func)
    
    renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), 1, raster_shader)
    dem_layer.setRenderer(renderer)
    dem_layer.setOpacity(0.9)
    
    project.addMapLayer(dem_layer)
    print("  ✓ 配色配置完成")
    
    # ==========================================
    # 第三步: 加载县级行政区划
    # ==========================================
    print("\n[3/7] 加载县级行政区划...")
    
    import glob
    admin_layer = None
    shps = glob.glob(r"slide-deck\autoclaw-course\县界\*.shp")
    for shp in shps:
        admin_layer = QgsVectorLayer(shp, "邯郸县级界", "ogr")
        if admin_layer.isValid():
            print(f"  ✓ 图层: {shp}")
            print(f"  ✓ 县级要素: {admin_layer.featureCount()} 个")
            break
    
    # 县界样式: 半透明深灰线，无填充
    symbol = QgsFillSymbol.createSimple({
        'outline_color': '80, 80, 80, 210',  # 深灰半透明
        'outline_width': '0.7',
        'color': '0,0,0,0',  # 完全透明填充
    })
    admin_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    project.addMapLayer(admin_layer)
    
    # ==========================================
    # 第四步: 县名标注 (洛阳风格)
    # ==========================================
    print("\n[4/7] 配置县名标注...")
    
    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = 'XZQMC'
    label_settings.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 10, QFont.Bold))
    text_format.setColor(QColor(55, 55, 55))
    text_format.setSize(10)
    
    # 白色描边 (洛阳图风格)
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1.3)
    buffer.setColor(QColor(255, 255, 255, 210))
    text_format.setBuffer(buffer)
    
    label_settings.setFormat(text_format)
    try:
        label_settings.placement = Qgis.LabelPlacement.OverPoint
    except:
        label_settings.placement = QgsPalLayerSettings.OverPoint
    label_settings.displayAll = True
    
    labeling = QgsVectorLayerSimpleLabeling(label_settings)
    admin_layer.setLabeling(labeling)
    admin_layer.setLabelsEnabled(True)
    
    print("  ✓ 县名标注配置完成")
    
    # ==========================================
    # 第五步: 图层顺序 (和洛阳图一致)
    # ==========================================
    print("\n[5/7] 调整图层顺序...")
    
    root = project.layerTreeRoot()
    all_layers = root.children()
    for layer_node in all_layers:
        root.removeChildNode(layer_node)
    
    # 顺序: DEM底图 → 县界 + 标注
    root.addLayer(dem_layer)
    root.addLayer(admin_layer)
    
    # ==========================================
    # 第六步: 地图布局 (严格复刻洛阳排版)
    # ==========================================
    print("\n[6/7] 创建地图布局...")
    
    extent = dem_layer.extent()
    buffer = extent.width() * 0.04
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    
    # A3 横向
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 主地图 (占满版面)
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(10, 10, 400, 277)
    map_item.setExtent(extent)
    map_item.setLayers([dem_layer, admin_layer])
    map_item.setBackgroundColor(QColor(245, 248, 245))
    layout.addLayoutItem(map_item)
    
    # ==========================================
    # 标题区 (左上角，完全复刻洛阳格式)
    # ==========================================
    
    # 第一行: 邯郸市 (冀D) - 大字号隶书风格
    title_main = QgsLayoutItemLabel(layout)
    title_main.setText("邯郸市 (冀D)")
    text_format_main = QgsTextFormat()
    text_format_main.setFont(QFont("微软雅黑", 36, QFont.Bold))
    text_format_main.setColor(QColor(40, 80, 40))
    title_main.setTextFormat(text_format_main)
    title_main.adjustSizeToText()
    title_main.attemptMove(QgsLayoutPoint(20, 15, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title_main)
    
    # 第二行: 描述文字 - "西依太行，东接华北平原"
    title_sub = QgsLayoutItemLabel(layout)
    title_sub.setText("西依太行山脉，东接华北平原")
    text_format_sub = QgsTextFormat()
    text_format_sub.setFont(QFont("微软雅黑", 18))
    text_format_sub.setColor(QColor(60, 110, 60))
    title_sub.setTextFormat(text_format_sub)
    title_sub.adjustSizeToText()
    title_sub.attemptMove(QgsLayoutPoint(20, 52, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title_sub)
    
    # ==========================================
    # 右下角: 指北针 + 比例尺
    # ==========================================
    
    # 指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(22, 36, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(375, 230, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # N 字母
    n_label = QgsLayoutItemLabel(layout)
    n_label.setText("N")
    n_format = QgsTextFormat()
    n_format.setFont(QFont("微软雅黑", 12, QFont.Bold))
    n_format.setColor(QColor(50, 50, 50))
    n_label.setTextFormat(n_format)
    n_label.adjustSizeToText()
    n_label.attemptMove(QgsLayoutPoint(380, 222, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(n_label)
    
    # 比例尺
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(80, 16, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(335, 265, QgsUnitTypes.LayoutMillimeters))
    
    text_format3 = QgsTextFormat()
    text_format3.setFont(QFont("微软雅黑", 9))
    text_format3.setColor(QColor(60, 60, 60))
    scale_bar.setTextFormat(text_format3)
    
    layout.addLayoutItem(scale_bar)
    
    # 底部比例尺数字标注
    scale_label = QgsLayoutItemLabel(layout)
    scale_label.setText("0          20          40")
    scale_format = QgsTextFormat()
    scale_format.setFont(QFont("微软雅黑", 8))
    scale_format.setColor(QColor(70, 70, 70))
    scale_label.setTextFormat(scale_format)
    scale_label.adjustSizeToText()
    scale_label.attemptMove(QgsLayoutPoint(335, 278, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale_label)
    
    # ==========================================
    # 第七步: 导出
    # ==========================================
    print("\n[7/7] 导出地图...")
    
    os.makedirs("assets/generated", exist_ok=True)
    output_path = "assets/generated/handan_county_exact_luoyang_style.png"
    
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ 导出成功: {output_path}")
        print(f"  ✓ 文件大小: {file_size:.1f} MB")
        print("\n" + "=" * 60)
        print("邯郸市县级地形图生成完成!")
        print("=" * 60)
        qgs.exitQgis()
        return 0
    else:
        print(f"  ✗ 导出失败，错误码: {result}")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
