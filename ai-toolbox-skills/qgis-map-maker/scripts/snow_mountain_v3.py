#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
雪山垂直地带性 DEM 图 - 简化版
使用单一 DEM 层 + 伪彩色渲染，验证渲染管道有效。
"""

import os, sys, argparse
from datetime import datetime

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsHillshadeRenderer, QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader, QgsRasterShader, QgsRasterBandStats,
    QgsTextFormat, QgsFillSymbol,
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
    parser.add_argument("--dem", required=True)
    parser.add_argument("--output", default="assets/generated/snow_mountain_dem.png")
    parser.add_argument("--title", default="Snow Mountain Vertical Zonation DEM")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    # === 1. 加载 DEM ===
    dem = QgsRasterLayer(args.dem, "DEM")
    if not dem.isValid():
        print("ERROR: DEM invalid")
        sys.exit(1)

    stats = dem.dataProvider().bandStatistics(1, QgsRasterBandStats.Min | QgsRasterBandStats.Max)
    dem_min = stats.minimumValue
    dem_max = stats.maximumValue
    elev_range = dem_max - dem_min
    print(f"DEM: {dem.width()}x{dem.height()}, {dem_min:.1f}m ~ {dem_max:.1f}m")

    # === 2. 用 QgsHillshadeRenderer 做基础 3D 阴影 ===
    hs = QgsHillshadeRenderer(dem.dataProvider(), 1, 315, 45)
    hs.setMultiDirectional(True)
    dem.setRenderer(hs)

    # === 3. 叠加伪彩色层 ===
    # DEM 已经有一个 hillshade renderer 了
    # 现在我们需要在保持 hillshade 的同时叠加颜色
    # 由于 QGIS 不支持叠加两个 raster renderer，我们改用：
    #   方案：预计算 hillshade.tif 作为基座 + DEM 伪彩色透明叠加
    
    hs_path = os.path.join(os.path.dirname(args.dem), "hillshade.tif")
    if os.path.exists(hs_path):
        hs_layer = QgsRasterLayer(hs_path, "Hillshade")
        if hs_layer.isValid():
            hs_layer.setRenderer(
                QgsSingleBandPseudoColorRenderer(
                    hs_layer.dataProvider(), 1,
                    QgsRasterShader(lambda: (lambda: None)())  # dummy
                )
            )
            # Set gray gradient for hillshade
            fcn = QgsColorRampShader()
            fcn.setColorRampType(QgsColorRampShader.Interpolated)
            items = []
            for val, color in [(0, "#555555"), (80, "#999999"), (160, "#cccccc"), (255, "#ffffff")]:
                items.append(QgsColorRampShader.ColorRampItem(val, QColor(color), ""))
            fcn.setColorRampItemList(items)
            shader = QgsRasterShader()
            shader.setRasterShaderFunction(fcn)
            hs_layer.setRenderer(QgsSingleBandPseudoColorRenderer(hs_layer.dataProvider(), 1, shader))
            project.addMapLayer(hs_layer)
            print("[OK] Hillshade layer added")

            # Adjust order: hillshade at bottom
            root = project.layerTreeRoot()
            hs_node = root.findLayer(hs_layer.id())
            if hs_node:
                clone = hs_node.clone()
                root.removeChildNode(hs_node)
                root.insertChildNode(0, clone)

    # Add DEM on top
    project.addMapLayer(dem)
    print(f"Layer tree: {[c.name() for c in project.layerTreeRoot().children()]}")

    # === 4. 布局（使用验证过的 setRect 模式）===
    pw, ph = 297, 210
    layout = QgsPrintLayout(project)
    layout.setName("SnowLayout")
    layout.initializeDefaults()
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))

    inset = 10; title_h = 22; title_gap = 8
    map_x = inset; map_y = title_h + title_gap
    map_w = pw - 2 * inset; map_h = ph - map_y - inset

    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)
    map_item.setRect(QRectF(map_x, map_y, map_w, map_h))
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.3, QgsUnitTypes.LayoutMillimeters))
    map_item.setFrameStrokeColor(QColor(150, 150, 150))
    map_item.setCrs(dem.crs())
    map_item.setExtent(dem.extent())
    map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))

    # Title
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText(args.title)
    t_fmt = QgsTextFormat()
    t_fmt.setFont(QFont("SimHei", 20, QFont.Bold))
    t_fmt.setColor(QColor(30, 30, 30))
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter); title.setFrameEnabled(False)
    title.attemptResize(QgsLayoutSize(pw - 30, 20, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(15, 2, QgsUnitTypes.LayoutMillimeters))
    layout.raiseItem(title)

    # Elev label
    elev = QgsLayoutItemLabel(layout)
    elev.setText(f"Elevation: {dem_min:.0f}m ~ {dem_max:.0f}m")
    elev.setFont(QFont("Microsoft YaHei", 7))
    elev.setFrameEnabled(False)
    elev.attemptResize(QgsLayoutSize(140, 7, QgsUnitTypes.LayoutMillimeters))
    elev.attemptMove(QgsLayoutPoint(map_x + 8, map_y + 8, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(elev)
    layout.raiseItem(elev)

    # North arrow
    na_path = None
    for svg_dir in QgsApplication.svgPaths():
        if os.path.exists(svg_dir):
            for rd, ds, fs in os.walk(svg_dir):
                for f in fs:
                    if "north" in f.lower() and f.endswith(".svg"):
                        na_path = os.path.join(rd, f); break
                if na_path: break
            if na_path: break
    if na_path:
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(na_path)
        north.attemptResize(QgsLayoutSize(18, 22, QgsUnitTypes.LayoutMillimeters))
        north.attemptMove(QgsLayoutPoint(map_x + map_w - 26, map_y + 8, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(north)
        layout.raiseItem(north)

    # Scalebar
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setLinkedMap(map_item)
    scalebar.setStyle("Single Box")
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.applyDefaultSize()
    sw = 80; sh = 10
    sx = map_x + (map_w - sw) / 2; sy = map_y + map_h - 35
    scalebar.attemptMove(QgsLayoutPoint(sx, sy, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(sw, sh, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    layout.raiseItem(scalebar)

    # Legend
    lw, lh = 75, 55
    lx = map_x + map_w - 18 - lw; ly = map_y + map_h - 18 - lh - 25
    lb = QgsLayoutItemShape(layout)
    lb.setShapeType(QgsLayoutItemShape.Rectangle)
    lb.setSymbol(QgsFillSymbol.createSimple({"color": "255,255,255,200", "outline_color": "180,180,180,160", "outline_width": "0.3"}))
    lb.attemptMove(QgsLayoutPoint(lx - 2, ly - 2, QgsUnitTypes.LayoutMillimeters))
    lb.attemptResize(QgsLayoutSize(lw + 4, lh + 4, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(lb)

    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("Vertical Vegetation Zones")
    legend.setFrameEnabled(False)
    legend.setAutoUpdateModel(True)
    legend.adjustBoxSize()
    legend.attemptResize(QgsLayoutSize(lw, lh, QgsUnitTypes.LayoutMillimeters))
    legend.attemptMove(QgsLayoutPoint(lx, ly, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend)
    layout.raiseItem(lb)
    layout.raiseItem(legend)

    # Source
    today = datetime.now().strftime("%Y-%m-%d")
    src = QgsLayoutItemLabel(layout)
    src.setText(f"Source: QGIS Test DEM | {today}")
    src.setFont(QFont("Microsoft YaHei", 7))
    src.setFrameEnabled(False)
    src.attemptResize(QgsLayoutSize(180, 7, QgsUnitTypes.LayoutMillimeters))
    src.attemptMove(QgsLayoutPoint(map_x + 8, map_y + map_h - 18, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(src)
    layout.raiseItem(src)

    layout.refresh()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = args.dpi
    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToImage(args.output, settings)

    project.clear()
    qgs.exitQgis()

    if result == QgsLayoutExporter.Success:
        print(f"[SUCCESS] {args.output}")
    else:
        print(f"[ERROR] {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
