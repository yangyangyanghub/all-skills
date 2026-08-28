#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸市县级行政区地图 - 小清新马卡龙配色
"""

import os
import sys
import random
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 60)
    print("邯郸市县级行政区地图 - 小清新风格")
    print("=" * 60)
    
    # 初始化 QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    project = QgsProject.instance()
    
    # ==========================================
    # 第一步: 加载行政区划
    # ==========================================
    print("\n[1/4] 加载县级行政区划...")
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸市界.shp"
    admin_layer = QgsVectorLayer(admin_path, "邯郸各县", "ogr")
    
    if not admin_layer.isValid():
        import glob
        shps = glob.glob(r"slide-deck\autoclaw-course\县界\*.shp")
        for shp in shps:
            admin_layer = QgsVectorLayer(shp, "邯郸各县", "ogr")
            if admin_layer.isValid():
                print(f"  ✓ 图层: {shp}")
                break
    
    if not admin_layer.isValid():
        print("  ✗ 行政区划加载失败!")
        return 1
    
    print(f"  ✓ 要素数: {admin_layer.featureCount()}")
    field_names = [f.name() for f in admin_layer.fields()]
    print(f"  ✓ 属性字段: {field_names}")
    
    # ==========================================
    # 第二步: 小清新配色方案 (马卡龙色系)
    # ==========================================
    print("\n[2/4] 配置小清新配色...")
    
    # 马卡龙色系 - 18种柔和颜色
    fresh_colors = [
        QColor(255, 218, 193),  # 淡桃色
        QColor(255, 230, 200),  # 浅杏色
        QColor(255, 241, 210),  # 奶黄色
        QColor(240, 248, 200),  # 淡黄绿
        QColor(220, 250, 210),  # 薄荷绿
        QColor(200, 245, 220),  # 浅青绿
        QColor(190, 235, 235),  # 淡青色
        QColor(200, 230, 250),  # 天蓝色
        QColor(210, 218, 250),  # 淡蓝紫
        QColor(225, 210, 250),  # 浅紫色
        QColor(240, 208, 245),  # 淡紫色
        QColor(250, 200, 225),  # 浅粉色
        QColor(255, 200, 210),  # 粉红色
        QColor(245, 220, 230),  # 玫瑰粉
        QColor(255, 228, 225),  # 薄雾玫瑰
        QColor(240, 230, 220),  # 杏仁色
        QColor(235, 235, 220),  # 浅卡其
        QColor(228, 240, 235),  # 青瓷色
    ]
    
    # 创建分类渲染器
    categories = []
    name_field = 'XZQMC'  # 行政区划名称
    
    features = list(admin_layer.getFeatures())
    random.seed(42)  # 固定随机种子，颜色可复现
    random.shuffle(fresh_colors)
    
    for i, feature in enumerate(features):
        county_name = feature[name_field]
        color = fresh_colors[i % len(fresh_colors)]
        color.setAlpha(220)  # 85%不透明度
        
        symbol = QgsFillSymbol.createSimple({
            'color': f'{color.red()},{color.green()},{color.blue()},{color.alpha()}',
            'outline_color': '255,255,255,200',
            'outline_width': '0.8',
            'outline_style': 'solid',
        })
        
        category = QgsRendererCategory(county_name, symbol, county_name)
        categories.append(category)
    
    renderer = QgsCategorizedSymbolRenderer(name_field, categories)
    admin_layer.setRenderer(renderer)
    
    project.addMapLayer(admin_layer)
    print(f"  ✓ 已配置 {len(categories)} 个县级行政区配色")
    
    # ==========================================
    # 第三步: 添加县名标注
    # ==========================================
    print("\n[3/4] 配置县名标注...")
    
    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = name_field
    label_settings.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 10, QFont.Medium))
    text_format.setColor(QColor(80, 80, 80))
    text_format.setSize(10)
    
    # 白色描边，让文字在任何底色上都清晰
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1.5)
    buffer.setColor(QColor(255, 255, 255, 230))
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
    
    print("  ✓ 标注配置完成")
    
    # ==========================================
    # 第四步: 创建地图布局
    # ==========================================
    print("\n[4/4] 创建地图布局...")
    
    extent = admin_layer.extent()
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
    map_item.setLayers([admin_layer])
    map_item.setBackgroundColor(QColor(250, 252, 250))
    layout.addLayoutItem(map_item)
    
    # 主标题 - 小清新字体
    title = QgsLayoutItemLabel(layout)
    title.setText("邯郸市")
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 30, QFont.Bold))
    text_format.setColor(QColor(100, 130, 120))
    title.setTextFormat(text_format)
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(25, 8, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 副标题
    sub_title = QgsLayoutItemLabel(layout)
    sub_title.setText("县级行政区分布图")
    text_format2 = QgsTextFormat()
    text_format2.setFont(QFont("微软雅黑", 14))
    text_format2.setColor(QColor(130, 160, 150))
    sub_title.setTextFormat(text_format2)
    sub_title.adjustSizeToText()
    sub_title.attemptMove(QgsLayoutPoint(25, 45, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(sub_title)
    
    # 指北针 - 简约款
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(18, 28, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(375, 245, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # 比例尺 - 简约样式
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(70, 12, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(25, 260, QgsUnitTypes.LayoutMillimeters))
    
    text_format3 = QgsTextFormat()
    text_format3.setFont(QFont("微软雅黑", 8))
    text_format3.setColor(QColor(100, 100, 100))
    scale_bar.setTextFormat(text_format3)
    
    layout.addLayoutItem(scale_bar)
    
    # 底部说明
    footer = QgsLayoutItemLabel(layout)
    footer.setText("数据来源: 公开地理信息数据 | 坐标系: CGCS2000")
    text_format4 = QgsTextFormat()
    text_format4.setFont(QFont("微软雅黑", 7))
    text_format4.setColor(QColor(160, 160, 160))
    footer.setTextFormat(text_format4)
    footer.adjustSizeToText()
    footer.attemptMove(QgsLayoutPoint(260, 275, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer)
    
    # ==========================================
    # 导出
    # ==========================================
    print("\n正在导出地图...")
    
    os.makedirs("assets/generated", exist_ok=True)
    output_path = "assets/generated/handan_county_fresh_style.png"
    
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ 导出成功: {output_path}")
        print(f"  ✓ 文件大小: {file_size:.1f} MB")
        print("\n" + "=" * 60)
        print("邯郸市县级行政区小清新地图生成完成!")
        print("=" * 60)
        qgs.exitQgis()
        return 0
    else:
        print(f"  ✗ 导出失败，错误码: {result}")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
