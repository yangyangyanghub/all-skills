#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
路网图 - 梵高星月夜模板 + 内部叠加要素
"""

import os
import sys
import argparse
from datetime import datetime

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsRectangle, QgsGraduatedSymbolRenderer, QgsRendererRange,
    QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat,
    QgsVectorLayerSimpleLabeling, QgsLegendStyle,
    QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsTextBufferSettings,
    QgsLayoutItemShape
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt, QRectF


def init_qgis():
    qgs = QgsApplication([], False)
    qgs.setPrefixPath("C:/Program Files/QGIS 3.40.9/apps/qgis-ltr", True)
    qgs.initQgis()
    return qgs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="assets/generated/路网图_星月夜.png")
    parser.add_argument("--paper-size", default="A3")
    parser.add_argument("--orientation", default="landscape")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--title", default="梵 高 · 星 月 夜")
    parser.add_argument("--source", default="城市路网数据")
    args = parser.parse_args()

    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    # ======================== 1. 加载图层 ========================
    data_dir = args.data
    
    water = QgsVectorLayer(os.path.join(data_dir, "水体_p.shp"), "水体", "ogr")
    if not water.isValid():
        print("ERROR: 水体图层无效")
        sys.exit(1)
    print(f"[OK] 水体: {water.featureCount()} 要素")
    
    admin = QgsVectorLayer(os.path.join(data_dir, "市级行政区划_p.shp"), "市级行政区划", "ogr")
    if not admin.isValid():
        print("ERROR: 行政区划图层无效")
        sys.exit(1)
    print(f"[OK] 行政区划: {admin.featureCount()} 要素")
    
    roads = QgsVectorLayer(os.path.join(data_dir, "道路_p.shp"), "道路", "ogr")
    if not roads.isValid():
        print("ERROR: 道路图层无效")
        sys.exit(1)
    print(f"[OK] 道路: {roads.featureCount()} 条")
    
    points = QgsVectorLayer(os.path.join(data_dir, "市_点_p.shp"), "城市点位", "ogr")
    if not points.isValid():
        print("ERROR: 城市点位图层无效")
        sys.exit(1)
    print(f"[OK] 城市点位: {points.featureCount()} 个")
    
    project.addMapLayer(water)
    project.addMapLayer(admin)
    project.addMapLayer(roads)
    project.addMapLayer(points)

    # ======================== 2. 梵高星月夜样式 ========================
    print("\n应用梵高星月夜样式...")
    
    # 2.1 水体 - 深蓝渐变
    water_symbol = QgsFillSymbol.createSimple({
        'color': '30,60,120,180',
        'outline_color': '10,36,78',
        'outline_width': '0.6'
    })
    water.setRenderer(QgsSingleSymbolRenderer(water_symbol))
    print("  [OK] 水体: 深蓝底")
    
    # 2.2 行政区划 - 深蓝底粗边
    admin_symbol = QgsFillSymbol.createSimple({
        'color': '44,70,130,150',
        'outline_color': '90,120,200',
        'outline_width': '1.2'
    })
    admin.setRenderer(QgsSingleSymbolRenderer(admin_symbol))
    print("  [OK] 行政区划: 深蓝描边")
    
    # 2.3 道路 - 金色漩涡流线（星月夜标志性风格）
    road_symbol = QgsLineSymbol.createSimple({
        'color': '230,190,50',    # 梵高金色
        'width': '0.8',
        'capstyle': 'round',
        'joinstyle': 'round'
    })
    roads.setRenderer(QgsSingleSymbolRenderer(road_symbol))
    print("  [OK] 道路: 金色流线")
    
    # 2.4 城市点位 - 星光效果
    point_symbol = QgsMarkerSymbol.createSimple({
        'color': '249,215,28',    # 亮黄星
        'size': '4.0',
        'outline_color': '249,215,28',
        'outline_width': '1.5'
    })
    points.setRenderer(QgsSingleSymbolRenderer(point_symbol))
    
    # 标注设置 - 浅蓝白色带深色缓冲
    labeling = QgsPalLayerSettings()
    labeling.fieldName = 'NAME'
    labeling.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setSize(10)
    text_format.setColor(QColor(212, 224, 245))  # 浅蓝白
    text_format.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
    
    # 深色缓冲增加对比度
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.2)
    buf.setColor(QColor(10, 26, 58, 220))  # 深蓝黑缓冲
    text_format.setBuffer(buf)
    
    labeling.setFormat(text_format)
    simple_labeling = QgsVectorLayerSimpleLabeling(labeling)
    points.setLabeling(simple_labeling)
    points.setLabelsEnabled(True)
    print("  [OK] 城市标注: 浅蓝白+深色缓冲")

    # ======================== 3. 构建紧凑布局 ========================
    print("\n构建紧凑布局...")
    
    paper_sizes = {
        'A4': (210, 297), 'A3': (297, 420), 'A2': (420, 594),
        'A1': (594, 841), 'A0': (841, 1189)
    }
    pw, ph = paper_sizes[args.paper_size]
    if args.orientation == 'landscape':
        pw, ph = ph, pw
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("StarryNightRoadMap")
    
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))
    pc = layout.pageCollection().page(0)
    print(f"  页面: {pc.sizeWithUnits().width()}{pc.sizeWithUnits().units()} x {pc.sizeWithUnits().height()}{pc.sizeWithUnits().units()}")
    
    # === 全尺寸地图 + 内部叠加要素 ===
    margin = 12
    title_h = 22
    title_gap = 8
    
    map_x = margin
    map_y = title_h + title_gap
    map_w = pw - 2 * margin
    map_h = ph - map_y - margin
    
    # 3.1 地图主体
    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)
    map_item.setRect(QRectF(map_x, map_y, map_w, map_h))
    map_item.setLayers([water, admin, roads, points])
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.6, QgsUnitTypes.LayoutMillimeters))
    map_item.setFrameStrokeColor(QColor(80, 100, 160))  # 深蓝边框
    map_item.setCrs(admin.crs())
    
    extent = QgsRectangle(admin.extent())
    extent.combineExtentWith(water.extent())
    extent.combineExtentWith(roads.extent())
    extent.scale(1.25)  # 增大缩放到 1.25，确保所有边界完整显示在图框内
    map_item.setExtent(extent)
    
    # 强制固定尺寸
    map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))
    
    actual_rect = map_item.rect()
    actual_w, actual_h = actual_rect.width(), actual_rect.height()
    # 使用设定值确保位置准确
    actual_w, actual_h = map_w, map_h
    print(f"  [OK] 地图: 设定={map_w:.0f}x{map_h:.0f}")
    
    inset = 8  # 内部边距

    # 3.2 标题 - 地图区域外，顶部居中
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText(args.title)
    t_fmt = QgsTextFormat()
    t_fmt.setFont(QFont('Microsoft YaHei', 22, QFont.Bold))
    t_fmt.setColor(QColor(249, 215, 28))  # 金色标题
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter)
    title.setFrameEnabled(False)
    title.attemptResize(QgsLayoutSize(pw - 30, 20, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(15, 2, QgsUnitTypes.LayoutMillimeters))
    layout.raiseItem(title)
    print(f"  [OK] 标题 (地图外)")

    # === 地图要素叠加在地图内部 ===
    
    # 3.3 指北针 - 地图内部右上角（动态探测 SVG 路径）
    na_path = None
    for svg_dir in QgsApplication.svgPaths():
        for root, dirs, files in os.walk(svg_dir):
            for f in files:
                if 'north' in f.lower() and f.endswith('.svg'):
                    na_path = os.path.join(root, f)
                    break
            if na_path: break
        if na_path: break
    
    if na_path:
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(na_path)
        north.attemptResize(QgsLayoutSize(18, 22, QgsUnitTypes.LayoutMillimeters))
        north.attemptMove(QgsLayoutPoint(map_x + actual_w - inset - 18, map_y + inset, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(north)
        layout.raiseItem(north)
        print("  [OK] 指北针 右上 (SVG)")
    else:
        # Fallback: 文字指北针
        na_label = QgsLayoutItemLabel(layout)
        na_label.setText("N ↑")
        na_label.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        na_label.setHAlign(Qt.AlignCenter)
        na_label.setFrameEnabled(False)
        na_label.attemptResize(QgsLayoutSize(22, 22, QgsUnitTypes.LayoutMillimeters))
        na_label.attemptMove(QgsLayoutPoint(map_x + actual_w - inset - 22, map_y + inset, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(na_label)
        layout.raiseItem(na_label)
        print("  [OK] 指北针 右上 (文字)")
    
    # 3.4 比例尺 - 地图内部底部居中（上移避让其他要素）
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setLinkedMap(map_item)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.applyDefaultSize()
    
    scale_w = 80
    scale_h = 10
    scale_y = map_y + actual_h - 28  # 从底部上移 28mm
    scale_x = map_x + (actual_w - scale_w) / 2
    scalebar.attemptMove(QgsLayoutPoint(scale_x, scale_y, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(scale_w, scale_h, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    layout.raiseItem(scalebar)
    print(f"  [OK] 比例尺 底部居中 ({scale_x:.0f},{scale_y:.0f})")
    
    # 3.5 图例 - 地图内部右下角（带半透明底）
    legend_w, legend_h = 75, 45
    legend_x = map_x + actual_w - inset - legend_w
    legend_y = map_y + actual_h - inset - legend_h - 2
    
    # 半透明背景框
    legend_bg = QgsLayoutItemShape(layout)
    legend_bg.setShapeType(QgsLayoutItemShape.Rectangle)
    fill_symbol = QgsFillSymbol.createSimple({
        'color': '255,255,255,180',
        'outline_color': '200,200,200,150',
        'outline_width': '0.3'
    })
    legend_bg.setSymbol(fill_symbol)
    legend_bg.attemptMove(QgsLayoutPoint(legend_x - 2, legend_y - 2, QgsUnitTypes.LayoutMillimeters))
    legend_bg.attemptResize(QgsLayoutSize(legend_w + 4, legend_h + 4, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend_bg)
    
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("图例")
    legend.setFrameEnabled(False)
    legend.setAutoUpdateModel(True)
    
    for st in [QgsLegendStyle.Title, QgsLegendStyle.Group, 
               QgsLegendStyle.Subgroup, QgsLegendStyle.Symbol, 
               QgsLegendStyle.SymbolLabel]:
        legend.style(st).setFont(QFont('Microsoft YaHei', 8))
    
    legend.adjustBoxSize()
    legend.attemptResize(QgsLayoutSize(legend_w, legend_h, QgsUnitTypes.LayoutMillimeters))
    legend.attemptMove(QgsLayoutPoint(legend_x, legend_y, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend)
    
    layout.raiseItem(legend_bg)
    layout.raiseItem(legend)
    print(f"  [OK] 图例 右下 ({legend_x:.0f},{legend_y:.0f}) + 半透明底")
    
    # 3.6 数据源 - 地图内部左下角
    today = datetime.now().strftime("%Y-%m-%d")
    source = QgsLayoutItemLabel(layout)
    source.setText(f"数据源：{args.source}  |  {today}")
    source.setFont(QFont('Microsoft YaHei', 7))
    source.setHAlign(Qt.AlignLeft)
    source.setFrameEnabled(False)
    source_w = 160
    source_h = 7
    source_x = map_x + inset
    source_y = map_y + actual_h - inset - source_h - 1  # 紧贴底部
    source.attemptResize(QgsLayoutSize(source_w, source_h, QgsUnitTypes.LayoutMillimeters))
    source.attemptMove(QgsLayoutPoint(source_x, source_y, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(source)
    layout.raiseItem(source)
    print(f"  [OK] 数据源 左下 ({source_x:.0f},{source_y:.0f})")
    
    layout.refresh()

    # ======================== 4. 导出 ========================
    print(f"\n导出图片...")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = args.dpi
    
    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToImage(args.output, settings)
    
    if result == QgsLayoutExporter.Success:
        print(f"[SUCCESS] {args.output}")
        print(f"  规格: {args.paper_size} {args.orientation} {args.dpi}DPI")
    else:
        print(f"[ERROR] 导出失败: {result}")
        sys.exit(1)
    
    qgs.exitQgis()


if __name__ == "__main__":
    main()
