#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
雪山垂直地带性 DEM 图
=========
使用 QgsHillshadeRenderer + 高程色带的组合方案。

基于 hillshade_map.py 验证过的渲染流程，添加植被带伪彩色叠加。
"""

import os
import sys
import argparse
from datetime import datetime

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsRectangle, QgsHillshadeRenderer, QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader, QgsRasterShader, QgsRasterBandStats,
    QgsSingleSymbolRenderer, QgsLegendStyle, QgsTextFormat, QgsFillSymbol,
    QgsCoordinateReferenceSystem,
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt, QRectF


def init_qgis():
    qgs = QgsApplication([], False)
    qgs.setPrefixPath("C:/Program Files/QGIS 3.40.9/apps/qgis-ltr", True)
    qgs.initQgis()
    return qgs


def main():
    parser = argparse.ArgumentParser(description="Snow Mountain DEM Map")
    parser.add_argument("--dem", required=True)
    parser.add_argument("--output", default="assets/generated/snow_mountain_dem.png")
    parser.add_argument("--title", default="Snow Mountain Vertical Zonation DEM")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    print(f"DEM: {args.dem}")
    print(f"Output: {args.output}")

    # === 1. 加载 DEM ===
    dem_layer = QgsRasterLayer(args.dem, "DEM")
    if not dem_layer.isValid():
        print("ERROR: DEM is invalid!")
        sys.exit(1)
    print(f"[OK] DEM: {dem_layer.width()}x{dem_layer.height()}")

    project.addMapLayer(dem_layer)

    # === 2. DEM 高程范围 ===
    stats = dem_layer.dataProvider().bandStatistics(
        1, QgsRasterBandStats.Min | QgsRasterBandStats.Max
    )
    dem_min = stats.minimumValue
    dem_max = stats.maximumValue
    elev_range = dem_max - dem_min
    print(f"  高程: {dem_min:.1f}m ~ {dem_max:.1f}m (跨度 {elev_range:.1f}m)")

    # === 3. 加载预计算 hillshade 作为底层 ===
    hs_path = os.path.join(os.path.dirname(args.dem), "hillshade.tif")
    hs_layer = None
    if os.path.exists(hs_path):
        hs_layer = QgsRasterLayer(hs_path, "Hillshade")
        if hs_layer.isValid():
            # 将 hillshade 样式设为灰度渐变
            fcn = QgsColorRampShader()
            fcn.setColorRampType(QgsColorRampShader.Interpolated)
            items = []
            for val, color in [
                (0, "#555555"), (50, "#888888"), (100, "#aaaaaa"),
                (150, "#cccccc"), (200, "#eeeeee"), (255, "#ffffff"),
            ]:
                items.append(QgsColorRampShader.ColorRampItem(val, QColor(color), ""))
            fcn.setColorRampItemList(items)
            shader = QgsRasterShader()
            shader.setRasterShaderFunction(fcn)
            renderer = QgsSingleBandPseudoColorRenderer(hs_layer.dataProvider(), 1, shader)
            hs_layer.setRenderer(renderer)
            project.addMapLayer(hs_layer)
            print("[OK] Hillshade 加载成功")

            # 调整图层顺序：hillshade 在底部
            root = project.layerTreeRoot()
            hs_node = root.findLayer(hs_layer.id())
            if hs_node:
                clone = hs_node.clone()
                root.removeChildNode(hs_node)
                root.insertChildNode(0, clone)

    # === 4. DEM 伪彩色渲染（垂直植被带）===
    print("\n应用植被带分类...")

    zones = [
        {"value": dem_min, "color": "#3CB371", "label": "Valley (谷底)"},
        {"value": dem_min + elev_range * 0.2, "color": "#228B22", "label": "Broadleaf (阔叶林)"},
        {"value": dem_min + elev_range * 0.4, "color": "#006400", "label": "Coniferous (针叶林)"},
        {"value": dem_min + elev_range * 0.6, "color": "#A0A0A0", "label": "Alpine (高山)"},
        {"value": dem_min + elev_range * 0.8, "color": "#E8E8F0", "label": "Snow Line (雪线)"},
    ]

    fcn = QgsColorRampShader()
    fcn.setColorRampType(QgsColorRampShader.Interpolated)

    ramp_items = []
    for z in zones:
        ramp_items.append(QgsColorRampShader.ColorRampItem(
            int(z["value"]), QColor(z["color"]), z["label"]
        ))
    ramp_items.append(QgsColorRampShader.ColorRampItem(int(dem_max), QColor("#FFFFFF"), ""))

    fcn.setColorRampItemList(ramp_items)
    fcn.setMinimumValue(dem_min)
    fcn.setMaximumValue(dem_max)

    shader = QgsRasterShader()
    shader.setRasterShaderFunction(fcn)
    renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), 1, shader)
    dem_layer.setRenderer(renderer)
    dem_layer.renderer().setOpacity(0.75)  # 提高不透明度让植被带更明显

    for z in zones:
        print(f"  [{z['color']}] {z['label']} ({z['value']:.0f}m)")

    print(f"\n DEM 图层 ID: {dem_layer.id()}")
    print(f" DEM LayerTree: {dem_layer.renderer().type()}")
    root = project.layerTreeRoot()
    print(f"  图层树节点: {[c.name() for c in root.children()]}")

    # === 5. 紧凑布局（参照 hillshade_map.py 验证过的流程）===
    print("\n构建布局...")

    pw, ph = 297, 210  # A3 横向 mm
    layout = QgsPrintLayout(project)
    layout.setName("SnowLayout")
    layout.initializeDefaults()

    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))

    inset = 10
    title_h = 22
    title_gap = 8

    map_x = inset
    map_y = title_h + title_gap
    map_w = pw - 2 * inset
    map_h = ph - map_y - inset

    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)
    map_item.setRect(QRectF(map_x, map_y, map_w, map_h))
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.3, QgsUnitTypes.LayoutMillimeters))
    map_item.setFrameStrokeColor(QColor(150, 150, 150))
    map_item.setCrs(dem_layer.crs())

    extent = dem_layer.extent()
    map_item.setExtent(extent)
    map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))

    print(f"  地图框: {map_w:.0f}x{map_h:.0f}mm")
    print(f"  CRS: {dem_layer.crs().authid()}")
    print(f"  Extent: {extent.toString()}")

    # === 标题 ===
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText(args.title)
    t_fmt = QgsTextFormat()
    t_fmt.setFont(QFont("SimHei", 20, QFont.Bold))
    t_fmt.setColor(QColor(30, 30, 30))
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter)
    title.setFrameEnabled(False)
    title.attemptResize(QgsLayoutSize(pw - 30, 20, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(15, 2, QgsUnitTypes.LayoutMillimeters))
    layout.raiseItem(title)

    # === 高程标注 ===
    elev = QgsLayoutItemLabel(layout)
    elev.setText(f"Elevation: {dem_min:.0f}m ~ {dem_max:.0f}m")
    elev.setFont(QFont("Microsoft YaHei", 7))
    elev.setFrameEnabled(False)
    elev.attemptResize(QgsLayoutSize(140, 7, QgsUnitTypes.LayoutMillimeters))
    elev.attemptMove(QgsLayoutPoint(map_x + 8, map_y + 8, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(elev)
    layout.raiseItem(elev)

    # === 指北针 ===
    na_path = None
    for svg_dir in QgsApplication.svgPaths():
        if os.path.exists(svg_dir):
            for root_dir, dirs, files in os.walk(svg_dir):
                for f in files:
                    if "north" in f.lower() and f.endswith(".svg"):
                        na_path = os.path.join(root_dir, f)
                        break
                if na_path: break
            if na_path: break
    if na_path:
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(na_path)
        north.attemptResize(QgsLayoutSize(18, 22, QgsUnitTypes.LayoutMillimeters))
        north.attemptMove(
            QgsLayoutPoint(map_x + map_w - 26, map_y + 8, QgsUnitTypes.LayoutMillimeters)
        )
        layout.addLayoutItem(north)
        layout.raiseItem(north)

    # === 比例尺 ===
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setLinkedMap(map_item)
    scalebar.setStyle("Single Box")
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.applyDefaultSize()

    sw, sh = 80, 10
    scale_x = map_x + (map_w - sw) / 2
    scale_y = map_y + map_h - 35
    scalebar.attemptMove(QgsLayoutPoint(scale_x, scale_y, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(sw, sh, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    layout.raiseItem(scalebar)

    # === 图例（带半透明背景）===
    legend_w, legend_h = 75, 55
    lg_x = map_x + map_w - 18 - legend_w
    lg_y = map_y + map_h - 18 - legend_h - 25

    legend_bg = QgsLayoutItemShape(layout)
    legend_bg.setShapeType(QgsLayoutItemShape.Rectangle)
    legend_bg.setSymbol(QgsFillSymbol.createSimple({
        "color": "255,255,255,200",
        "outline_color": "180,180,180,160",
        "outline_width": "0.3",
    }))
    legend_bg.attemptMove(QgsLayoutPoint(lg_x - 2, lg_y - 2, QgsUnitTypes.LayoutMillimeters))
    legend_bg.attemptResize(QgsLayoutSize(legend_w + 4, legend_h + 4, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend_bg)

    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("Vertical Vegetation Zones")
    legend.setFrameEnabled(False)
    legend.setAutoUpdateModel(True)
    legend.adjustBoxSize()
    legend.attemptResize(QgsLayoutSize(legend_w, legend_h, QgsUnitTypes.LayoutMillimeters))
    legend.attemptMove(QgsLayoutPoint(lg_x, lg_y, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend)

    layout.raiseItem(legend_bg)
    layout.raiseItem(legend)

    # === 数据源 ===
    today = datetime.now().strftime("%Y-%m-%d")
    source = QgsLayoutItemLabel(layout)
    source.setText(f"Source: QGIS Test DEM  |  {today}")
    source.setFont(QFont("Microsoft YaHei", 7))
    source.setFrameEnabled(False)
    source.attemptResize(QgsLayoutSize(180, 7, QgsUnitTypes.LayoutMillimeters))
    source.attemptMove(QgsLayoutPoint(map_x + 8, map_y + map_h - 18, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(source)
    layout.raiseItem(source)

    # === 导出 ===
    layout.refresh()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = args.dpi

    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToImage(args.output, settings)

    project.clear()
    qgs.exitQgis()

    if result == QgsLayoutExporter.Success:
        print(f"\n[SUCCESS] {args.output}")
        sys.exit(0)
    else:
        print(f"\n[ERROR] Export failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
