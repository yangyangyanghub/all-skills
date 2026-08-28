#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
城市关系强度图 - 紧凑堆叠布局版（V6）
地图全宽，图例/比例尺/数据源紧凑堆叠在地图下方
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
    parser.add_argument("--output", default="assets/generated/城市关系强度图.png")
    parser.add_argument("--paper-size", default="A3")
    parser.add_argument("--orientation", default="landscape")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--title", default="吉林省城市关系强度图")
    parser.add_argument("--source", default="城市关系强度数据")
    args = parser.parse_args()

    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    # ======================== 1. 加载图层 ========================
    data_dir = args.data
    
    admin = QgsVectorLayer(os.path.join(data_dir, "市级行政区划_p.shp"), "市级行政区划", "ogr")
    if not admin.isValid():
        print("ERROR: 行政区划图层无效")
        sys.exit(1)
    print(f"[OK] 行政区划: {admin.featureCount()} 要素")
    
    lines = QgsVectorLayer(os.path.join(data_dir, "城市关系连线_p.shp"), "城市关系连线", "ogr")
    if not lines.isValid():
        print("ERROR: 连线图层无效")
        sys.exit(1)
    print(f"[OK] 关系连线: {lines.featureCount()} 条")
    
    points = QgsVectorLayer(os.path.join(data_dir, "市_点_p.shp"), "城市点位", "ogr")
    if not points.isValid():
        print("ERROR: 点位图层无效")
        sys.exit(1)
    print(f"[OK] 城市点位: {points.featureCount()} 个")
    
    project.addMapLayer(admin)
    project.addMapLayer(lines)
    project.addMapLayer(points)

    # ======================== 2. 应用样式 ========================
    print("\n应用样式...")
    
    # 行政区划底图
    admin_symbol = QgsFillSymbol.createSimple({
        'color': '245,245,250,200',
        'outline_color': '180,180,180',
        'outline_width': '0.4'
    })
    admin.setRenderer(QgsSingleSymbolRenderer(admin_symbol))
    
    # 连线分级渲染
    print("  - 连线分级渲染...")
    strengths = []
    for feat in lines.getFeatures():
        try:
            s = float(feat['strength'])
            strengths.append(s)
        except:
            pass
    
    if strengths:
        min_s = min(strengths)
        max_s = max(strengths)
        print(f"    强度范围: {min_s:.2f} ~ {max_s:.2f}")
        
        ranges = []
        sym_low = QgsLineSymbol.createSimple({'color': '180,180,180', 'width': '0.4'})
        ranges.append(QgsRendererRange(0, 0.2, sym_low, '弱 (0~0.2)'))
        sym_med = QgsLineSymbol.createSimple({'color': '230,120,0', 'width': '1.2'})
        ranges.append(QgsRendererRange(0.2, 0.4, sym_med, '中 (0.2~0.4)'))
        sym_high = QgsLineSymbol.createSimple({'color': '183,28,28', 'width': '2.5'})
        ranges.append(QgsRendererRange(0.4, max_s + 0.01, sym_high, '强 (0.4+)'))
        
        renderer = QgsGraduatedSymbolRenderer('strength', ranges)
        lines.setRenderer(renderer)
        print("    [OK] 分级完成")
    
    # 城市点 + 标注
    print("  - 城市标注...")
    marker = QgsMarkerSymbol.createSimple({
        'color': '40,40,40',
        'size': '3.5',
        'outline_color': '255,255,255',
        'outline_width': '1.0'
    })
    points.setRenderer(QgsSingleSymbolRenderer(marker))
    
    labeling = QgsPalLayerSettings()
    labeling.fieldName = 'NAME'
    labeling.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setSize(10)
    text_format.setColor(QColor(20, 20, 20))
    text_format.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
    
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.0)
    buf.setColor(QColor(255, 255, 255, 220))
    text_format.setBuffer(buf)
    
    labeling.setFormat(text_format)
    simple_labeling = QgsVectorLayerSimpleLabeling(labeling)
    points.setLabeling(simple_labeling)
    points.setLabelsEnabled(True)
    print("    [OK] 标注完成")

    # ======================== 3. 构建紧凑布局 ========================
    print("\n构建紧凑布局...")
    
    paper_sizes = {
        'A4': (210, 297), 'A3': (297, 420), 'A2': (420, 594),
        'A1': (594, 841), 'A0': (841, 1189)
    }
    pw, ph = paper_sizes[args.paper_size]
    if args.orientation == 'landscape':
        pw, ph = ph, pw  # 横向交换
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("CityRelationshipLayout")
    
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))
    pc = layout.pageCollection().page(0)
    print(f"  页面: {pc.sizeWithUnits().width()}{pc.sizeWithUnits().units()} x {pc.sizeWithUnits().height()}{pc.sizeWithUnits().units()}")
    
    # === 全尺寸地图 + 内部叠加要素 ===
    margin = 10
    title_h = 20
    title_gap = 8  # 标题与地图间距
    
    # 地图区域（顶部标题外部，其余全尺寸）
    map_x = margin
    map_y = title_h + title_gap
    map_w = pw - 2 * margin
    map_h = ph - map_y - margin  # 地图占满剩余高度
    
    # 3.1 地图主体（全尺寸）
    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)
    map_item.setRect(QRectF(map_x, map_y, map_w, map_h))
    map_item.setLayers([admin, lines, points])
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.5, QgsUnitTypes.LayoutMillimeters))
    map_item.setCrs(admin.crs())
    
    extent = QgsRectangle(admin.extent())
    extent.combineExtentWith(lines.extent())
    extent.combineExtentWith(points.extent())
    extent.scale(1.15)
    map_item.setExtent(extent)
    
    # 强制固定尺寸
    map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))
    
    actual_rect = map_item.rect()
    actual_w, actual_h = actual_rect.width(), actual_rect.height()
    print(f"  [OK] 地图: 设定={map_w:.0f}x{map_h:.0f} 实际={actual_w:.0f}x{actual_h:.0f}")
    actual_w, actual_h = map_w, map_h  # 使用设定值确保位置准确
    
    # === 布局要素 ===
    inset = 8  # 内部边距

    # 3.2 标题 - 地图区域外，顶部居中
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText(args.title)
    t_fmt = QgsTextFormat()
    t_fmt.setFont(QFont('Microsoft YaHei', 20, QFont.Bold))
    t_fmt.setColor(QColor(0, 0, 0))
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter)
    title.setFrameEnabled(False)
    title.attemptResize(QgsLayoutSize(pw - 30, 15, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(15, 3, QgsUnitTypes.LayoutMillimeters))
    layout.raiseItem(title)
    print(f"  [OK] 标题 (地图外)")

    # 3.3 指北针 - 动态探测 SVG 路径
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

    # 3.4 比例尺 - 地图内部底部居中
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setLinkedMap(map_item)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.applyDefaultSize()
    
    scale_w = 80
    scale_h = 10
    scale_y = map_y + actual_h - 28  # 从底部上移 28mm，避让图例和数据源
    scale_x = map_x + (actual_w - scale_w) / 2
    scalebar.attemptMove(QgsLayoutPoint(scale_x, scale_y, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(scale_w, scale_h, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    layout.raiseItem(scalebar)
    print(f"  [OK] 比例尺 底部居中 ({scale_x:.0f},{scale_y:.0f})")
    
    # 3.5 图例 - 地图内部右下角（带半透明底）
    # 先创建半透明背景矩形
    legend_w, legend_h = 75, 42
    legend_x = map_x + actual_w - inset - legend_w
    legend_y = map_y + actual_h - inset - legend_h - 2
    
    # 半透明背景（用 QgsLayoutItemShape）
    from qgis.core import QgsLayoutItemShape
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
    
    # 提升层级：背景 < 地图 < 图例
    layout.raiseItem(legend_bg)
    layout.raiseItem(legend)
    print(f"  [OK] 图例 右下 ({legend_x:.0f},{legend_y:.0f}) + 半透明底")
    
    # 3.6 数据源 - 地图内部左下角（紧贴底部）
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
    
    # ======================== 5. 保存工程文件 ========================
    qgs_path = os.path.splitext(args.output)[0] + ".qgs"
    project.write(qgs_path)
    print(f"[SUCCESS] QGIS 工程文件: {qgs_path}")
    
    qgs.exitQgis()


if __name__ == "__main__":
    main()
