#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸市地形图 - 完全复刻洛阳市地图风格
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 60)
    print("邯郸市地形图生成器 - 复刻洛阳市风格")
    print("=" * 60)
    
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    project = QgsProject.instance()
    
    # ==========================================
    # 第一步: 加载 DEM 并生成山体阴影
    # ==========================================
    print("\n[1/6] 加载 DEM 地形数据...")
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    dem_layer = QgsRasterLayer(dem_path, "DEM_邯郸")
    
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败!")
        return 1
    
    print(f"  ✓ 范围: {dem_layer.extent()}")
    print(f"  ✓ CRS: {dem_layer.crs().authid()}")
    
    # 获取统计信息
    provider = dem_layer.dataProvider()
    stats = provider.bandStatistics(1, QgsRasterBandStats.All, dem_layer.extent(), 0)
    min_val = stats.minimumValue
    max_val = stats.maximumValue
    range_val = max_val - min_val
    print(f"  ✓ 高程范围: {min_val:.1f}m - {max_val:.1f}m")
    
    # ==========================================
    # 第二步: 生成 Hillshade 山体阴影图层
    # ==========================================
    print("\n[2/6] 生成山体阴影...")
    
    # 方法: 用 Hillshade 滤镜生成灰度山体阴影
    # 西北光照 (315°), 太阳高度 45°
    hillshade_renderer = QgsSingleBandGrayRenderer(provider, 1)
    
    # 调整亮度对比度模拟 hillshade 效果
    contrast_enhancement = QgsContrastEnhancement()
    contrast_enhancement.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
    hillshade_renderer.setContrastEnhancement(contrast_enhancement)
    
    # 先把 DEM 添加到项目作为 hillshade 层
    dem_layer.setRenderer(hillshade_renderer)
    dem_layer.setOpacity(0.35)  # 35% 不透明度，作为阴影层
    project.addMapLayer(dem_layer)
    
    # ==========================================
    # 第三步: 创建彩色地形图层 (6阶黄绿渐变)
    # ==========================================
    print("\n[3/6] 配置6阶黄绿渐变配色...")
    
    dem_color_layer = QgsRasterLayer(dem_path, "DEM_彩色")
    project.addMapLayer(dem_color_layer)
    
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    # 复刻洛阳市配色: 浅黄绿 → 淡绿 → 草绿 → 深绿 → 墨绿 → 暗绿
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
    
    color_renderer = QgsSingleBandPseudoColorRenderer(dem_color_layer.dataProvider(), 1, raster_shader)
    dem_color_layer.setRenderer(color_renderer)
    dem_color_layer.setOpacity(0.85)  # 85% 透明度，让 hillshade 透出来
    
    print("  ✓ 配色配置完成")
    
    # ==========================================
    # 第四步: 加载行政区划图层
    # ==========================================
    print("\n[4/6] 加载行政区划...")
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸市界.shp"
    admin_layer = QgsVectorLayer(admin_path, "县界", "ogr")
    
    if not admin_layer.isValid():
        # 尝试找其他 shp
        import glob
        shps = glob.glob(r"slide-deck\autoclaw-course\县界\*.shp")
        for shp in shps:
            admin_layer = QgsVectorLayer(shp, "县界", "ogr")
            if admin_layer.isValid():
                print(f"  ✓ 找到图层: {shp}")
                break
    
    if admin_layer.isValid():
        print(f"  ✓ 要素数: {admin_layer.featureCount()}")
        
        # 查看字段名
        field_names = [f.name() for f in admin_layer.fields()]
        print(f"  ✓ 属性字段: {field_names}")
        
        # 面样式: 透明填充 + 灰色边界
        symbol = QgsFillSymbol.createSimple({
            'outline_color': '85, 85, 85, 200',
            'outline_width': '0.6',
            'color': '0,0,0,0',
        })
        admin_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        project.addMapLayer(admin_layer)
        
        # ==========================================
        # 第五步: 添加县名标注
        # ==========================================
        print("\n[5/6] 配置县名标注...")
        
        label_settings = QgsPalLayerSettings()
        
        # 找名称字段
        name_field = None
        for fn in field_names:
            if 'NAME' in fn.upper() or '名称' in fn or '县' in fn or 'XIAN' in fn.upper() or 'XZQMC' in fn.upper():
                name_field = fn
                break
        
        if name_field:
            print(f"  ✓ 使用字段: {name_field}")
            label_settings.fieldName = name_field
            label_settings.enabled = True
            
            text_format = QgsTextFormat()
            text_format.setFont(QFont("微软雅黑", 9, QFont.Bold))
            text_format.setColor(QColor(60, 60, 60))
            text_format.setSize(9)
            
            buffer = QgsTextBufferSettings()
            buffer.setEnabled(True)
            buffer.setSize(1.2)
            buffer.setColor(QColor(255, 255, 255, 220))
            text_format.setBuffer(buffer)
            
            label_settings.setFormat(text_format)
            try:
                label_settings.placement = Qgis.LabelPlacement.OverPoint
            except AttributeError:
                try:
                    label_settings.placement = QgsPalLayerSettings.OverPoint
                except:
                    pass  # 使用默认位置
            label_settings.displayAll = True
            
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            admin_layer.setLabeling(labeling)
            admin_layer.setLabelsEnabled(True)
        else:
            print("  ⚠ 未找到名称字段，跳过标注")
    
    # 图层顺序: hillshade → 彩色DEM → 行政区边界
    root = project.layerTreeRoot()
    all_layers = root.children()
    for layer_node in all_layers:
        root.removeChildNode(layer_node)
    
    # 按正确顺序添加
    root.addLayer(dem_layer)          # 最底层: hillshade 灰度
    root.addLayer(dem_color_layer)    # 中间层: 彩色地形 (85%透明)
    if admin_layer.isValid():
        root.addLayer(admin_layer)    # 最上层: 边界线 + 标注
    
    # ==========================================
    # 第六步: 创建地图布局
    # ==========================================
    print("\n[6/6] 创建地图布局...")
    
    extent = dem_layer.extent()
    buffer = extent.width() * 0.05
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    
    # A3 横向
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 主地图
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(15, 30, 390, 245)
    map_item.setExtent(extent)
    
    # 收集所有可见图层
    visible_layers = [dem_layer, dem_color_layer]
    if admin_layer.isValid():
        visible_layers.append(admin_layer)
    map_item.setLayers(visible_layers)
    map_item.setBackgroundColor(QColor(245, 250, 245))
    layout.addLayoutItem(map_item)
    
    # 主标题 - 复刻洛阳市风格 "邯郸市 (冀D)"
    title = QgsLayoutItemLabel(layout)
    title.setText("邯郸市 (冀D)")
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 32, QFont.Bold))
    text_format.setColor(QColor(40, 80, 40))
    title.setTextFormat(text_format)
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(25, 8, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 副标题
    sub_title = QgsLayoutItemLabel(layout)
    sub_title.setText("西依太行山脉，东接华北平原")
    text_format2 = QgsTextFormat()
    text_format2.setFont(QFont("微软雅黑", 16))
    text_format2.setColor(QColor(70, 120, 70))
    sub_title.setTextFormat(text_format2)
    sub_title.adjustSizeToText()
    sub_title.attemptMove(QgsLayoutPoint(25, 45, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(sub_title)
    
    # 指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(20, 32, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(375, 245, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # 比例尺
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(70, 14, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(25, 260, QgsUnitTypes.LayoutMillimeters))
    
    # 比例尺颜色 - 绿色系
    scale_bar.setFillColor(QColor(100, 160, 100))
    scale_bar.setFillColor2(QColor(200, 230, 200))
    scale_bar.setLineColor(QColor(60, 100, 60))
    
    text_format3 = QgsTextFormat()
    text_format3.setFont(QFont("微软雅黑", 8))
    text_format3.setColor(QColor(50, 50, 50))
    scale_bar.setTextFormat(text_format3)
    
    layout.addLayoutItem(scale_bar)
    
    # 右下角小标注
    footer = QgsLayoutItemLabel(layout)
    footer.setText("DEM分辨率: 12m | 坐标系: CGCS2000")
    text_format4 = QgsTextFormat()
    text_format4.setFont(QFont("微软雅黑", 7))
    text_format4.setColor(QColor(120, 120, 120))
    footer.setTextFormat(text_format4)
    footer.adjustSizeToText()
    footer.attemptMove(QgsLayoutPoint(280, 275, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer)
    
    # ==========================================
    # 导出
    # ==========================================
    print("\n正在导出地图...")
    
    os.makedirs("assets/generated", exist_ok=True)
    output_path = "assets/generated/handan_luoyang_style.png"
    
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ 导出成功: {output_path}")
        print(f"  ✓ 文件大小: {file_size:.1f} MB")
        print("\n" + "=" * 60)
        print("邯郸市地形图生成完成!")
        print("=" * 60)
        qgs.exitQgis()
        return 0
    else:
        print(f"  ✗ 导出失败，错误码: {result}")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
