#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
山体阴影图 - 基于 DEM 的 Hillshade 渲染 + 内置叠加要素
"""

import os
import sys
import argparse
import math
from datetime import datetime

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsRectangle, QgsHillshadeRenderer, QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader, QgsRasterShader, QgsRasterBandStats,
    QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat,
    QgsVectorLayerSimpleLabeling, QgsLegendStyle, QgsTextBufferSettings,
    QgsLineSymbol, QgsMarkerSymbol, QgsFillSymbol, QgsCoordinateReferenceSystem
)
from qgis.PyQt.QtGui import QColor, QFont, QRadialGradient
from qgis.PyQt.QtCore import Qt, QRectF


def init_qgis():
    qgs = QgsApplication([], False)
    qgs.setPrefixPath("C:/Program Files/QGIS 3.40.9/apps/qgis-ltr", True)
    qgs.initQgis()
    return qgs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--dem-name", default="DEM10m.tif")
    parser.add_argument("--contour", default=None, help="等高线/矢量叠加图层")
    parser.add_argument("--output", default="assets/generated/山体阴影图.png")
    parser.add_argument("--paper-size", default="A3")
    parser.add_argument("--orientation", default="landscape")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--title", default="山 体 阴 影 图")
    parser.add_argument("--source", default="DEM 高程数据")
    parser.add_argument("--contour-color", default="100,100,100", help="矢量叠加颜色")
    args = parser.parse_args()

    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    # ======================== 1. 加载 DEM ========================
    dem_path = os.path.join(args.data, args.dem_name)
    if not os.path.exists(dem_path):
        print(f"ERROR: DEM 文件不存在: {dem_path}")
        sys.exit(1)

    raster = QgsRasterLayer(dem_path, "DEM")
    if not raster.isValid():
        print("ERROR: DEM 栅格无效")
        sys.exit(1)
    print(f"[OK] DEM: {raster.width()}x{raster.height()} 像素")
    
    # 获取 DEM 高程范围
    stats = raster.dataProvider().bandStatistics(1, QgsRasterBandStats.Min | QgsRasterBandStats.Max)
    min_elev = stats.minimumValue
    max_elev = stats.maximumValue
    print(f"  高程范围: {min_elev:.1f}m ~ {max_elev:.1f}m")
    
    project.addMapLayer(raster)

    # ======================== 2. Hillshade + 伪彩色 ========================
    print("\n渲染山体阴影...")
    
    # 2.1 山体阴影渲染器
    hillshade = QgsHillshadeRenderer(raster.dataProvider(), 1, 315, 45)  # 方位角 315°，高度角 45°
    hillshade.setMultiDirectional(True)  # 多向光照
    raster.setRenderer(hillshade)

    print("  [OK] 山体阴影（多向光照）")
    
    # 2.2 可选：叠加等高线/矢量
    contour_layer = None
    if args.contour:
        contour_path = os.path.join(args.data, args.contour)
        if os.path.exists(contour_path):
            contour_layer = QgsVectorLayer(contour_path, args.contour.replace('.shp', ''), "ogr")
            if contour_layer.isValid():
                # 半透明矢量轮廓
                r, g, b = args.contour_color.split(',')
                symbol = QgsLineSymbol.createSimple({
                    'color': f'{r},{g},{b}',
                    'width': '0.4',
                    'opacity': '0.6'
                })
                contour_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
                project.addMapLayer(contour_layer)
                print(f"  [OK] 叠加矢量: {contour_layer.featureCount()} 要素")
            else:
                print(f"  [WARN] 矢量图层无效: {args.contour}")
        else:
            print(f"  [WARN] 矢量文件不存在: {args.contour}")

    # ======================== 3. 构建紧凑布局 ========================
    print("\n构建紧凑布局...")
    
    paper_sizes = {
        'A4': (210, 297), 'A3': (297, 420), 'A2': (420, 594),
        'A1': (594, 841), 'A0': (841, 1189)
    }
    pw, ph = paper_sizes[args.paper_size]
    if args.orientation == 'landscape':
        pw, ph = ph, pw  # 横向
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("HillshadeLayout")
    
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))
    
    inset = 10
    title_h = 22
    title_gap = 8
    
    map_x = inset
    map_y = title_h + title_gap
    map_w = pw - 2 * inset
    map_h = ph - map_y - inset
    
    # 3.1 地图主体（全尺寸）
    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)
    map_item.setRect(QRectF(map_x, map_y, map_w, map_h))
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.3, QgsUnitTypes.LayoutMillimeters))
    map_item.setFrameStrokeColor(QColor(150, 150, 150))
    map_item.setCrs(raster.crs())
    
    extent = raster.extent()
    map_item.setExtent(extent)
    
    map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))
    
    actual_w, actual_h = map_w, map_h
    print(f"  [OK] 地图: {actual_w:.0f}x{actual_h:.0f}mm")

    # === 叠加要素 ===
    inset_elem = 8  # 内部边距

    # 3.2 标题（地图外，顶部居中，金色）
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText(args.title)
    t_fmt = QgsTextFormat()
    t_fmt.setFont(QFont('Microsoft YaHei', 22, QFont.Bold))
    t_fmt.setColor(QColor(50, 50, 50))
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter)
    title.setFrameEnabled(False)
    title.attemptResize(QgsLayoutSize(pw - 30, 20, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(15, 2, QgsUnitTypes.LayoutMillimeters))
    layout.raiseItem(title)
    print("  [OK] 标题 (地图外)")

    # 3.3 指北针 - 地图内部右上角
    na_path = None
    for svg_dir in QgsApplication.svgPaths():
        if os.path.exists(svg_dir):
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
        north.attemptMove(QgsLayoutPoint(map_x + actual_w - inset_elem - 18, map_y + inset_elem, QgsUnitTypes.LayoutMillimeters))
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
        na_label.attemptMove(QgsLayoutPoint(map_x + actual_w - inset_elem - 22, map_y + inset_elem, QgsUnitTypes.LayoutMillimeters))
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
    scale_y_from_bottom = 28
    scale_y = map_y + actual_h - scale_y_from_bottom
    scale_x = map_x + (actual_w - scale_w) / 2
    scalebar.attemptMove(QgsLayoutPoint(scale_x, scale_y, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(scale_w, scale_h, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    layout.raiseItem(scalebar)
    print(f"  [OK] 比例尺 底部居中 ({scale_x:.0f},{scale_y:.0f})")
    
    # 3.5 图例 - 地图内部右下角（带半透明底）
    legend_w, legend_h = 70, 35
    legend_x = map_x + actual_w - inset_elem - legend_w
    legend_y = map_y + actual_h - inset_elem - legend_h - 2
    
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
    source_x = map_x + inset_elem
    source_y = map_y + actual_h - inset_elem - source_h - 1
    source.attemptResize(QgsLayoutSize(source_w, source_h, QgsUnitTypes.LayoutMillimeters))
    source.attemptMove(QgsLayoutPoint(source_x, source_y, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(source)
    layout.raiseItem(source)
    print(f"  [OK] 数据源 左下 ({source_x:.0f},{source_y:.0f})")
    
    # 3.7 高程标注 - 右上角下方，显示高程范围
    elev_label = QgsLayoutItemLabel(layout)
    elev_label.setText(f"高程: {min_elev:.0f}m ~ {max_elev:.0f}m")
    elev_label.setFont(QFont('Microsoft YaHei', 7))
    elev_label.setHAlign(Qt.AlignLeft)
    elev_label.setFrameEnabled(False)
    elev_w = 120
    elev_h = 7
    elev_x = map_x + inset_elem
    elev_y = map_y + inset_elem + 2
    elev_label.attemptResize(QgsLayoutSize(elev_w, elev_h, QgsUnitTypes.LayoutMillimeters))
    elev_label.attemptMove(QgsLayoutPoint(elev_x, elev_y, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(elev_label)
    layout.raiseItem(elev_label)
    print(f"  [OK] 高程标注 左上 ({elev_x:.0f},{elev_y:.0f})")
    
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
        print(f"  高程: {min_elev:.1f}m ~ {max_elev:.1f}m")
    else:
        print(f"[ERROR] 导出失败: {result}")
        sys.exit(1)
    
    qgs.exitQgis()


if __name__ == "__main__":
    main()
