#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
雪山垂直植被带 DEM 图 - Discrete 分级渲染
Hillshade 灰度底图 + 离散伪彩色 DEM 叠加，模拟垂直植被带效果
"""

import os, sys, argparse, shutil, tempfile
from datetime import datetime

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemPage,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsRectangle,
    QgsHillshadeRenderer, QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader, QgsRasterShader, QgsRasterBandStats,
    QgsTextFormat, QgsFillSymbol, QgsTextBufferSettings, QgsLegendStyle, QgsLayerTreeLayer,
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
    parser.add_argument("--output", default="assets/generated/snow_mountain_dem_vertical.png")
    parser.add_argument("--title", default="Vertical Vegetation Zonation")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    # === 1. 加载 DEM（两份实例：hillshade 底图 + 彩色覆盖层）===
    dem_path = args.dem
    if not os.path.exists(dem_path):
        print(f"ERROR: DEM file not found: {dem_path}")
        sys.exit(1)

    # 复制 DEM 到临时文件，确保两个图层使用独立的数据源
    dem_tmp = os.path.join(tempfile.gettempdir(), "qgis_dem_hs_work.tif")
    shutil.copy2(dem_path, dem_tmp)
    print(f"  [OK] DEM temp copy created")

    # 底图：Hillshade 灰度层（使用临时文件副本）
    hs_layer = QgsRasterLayer(dem_tmp, "Hillshade")
    if not hs_layer.isValid():
        print("ERROR: Hillshade layer invalid")
        sys.exit(1)

    stats = hs_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.Min | QgsRasterBandStats.Max)
    dem_min = stats.minimumValue
    dem_max = stats.maximumValue
    print(f"DEM: {hs_layer.width()}x{hs_layer.height()}, {dem_min:.1f}m ~ {dem_max:.1f}m")

    # Hillshade 渲染器（多向光照做底图阴影）
    hs_renderer = QgsHillshadeRenderer(hs_layer.dataProvider(), 1, 315, 45)
    hs_renderer.setMultiDirectional(True)
    hs_layer.setRenderer(hs_renderer)

    # 彩色覆盖层：伪彩色离散渲染
    color_layer = QgsRasterLayer(dem_path, "Vegetation Zones")

    # 直接内联构建 shader（避免克隆问题）
    elev_range = dem_max - dem_min
    t1 = dem_min + elev_range * 0.15
    t2 = dem_min + elev_range * 0.35
    t3 = dem_min + elev_range * 0.55
    t4 = dem_min + elev_range * 0.75

    fcn = QgsColorRampShader()
    fcn.setColorRampType(QgsColorRampShader.Discrete)
    items = [
        QgsColorRampShader.ColorRampItem(int(dem_min), QColor(144, 238, 144), "Base"),
        QgsColorRampShader.ColorRampItem(int(t1),       QColor(46, 139, 87),   "Forest"),
        QgsColorRampShader.ColorRampItem(int(t2),       QColor(85, 107, 47),   "Transition"),
        QgsColorRampShader.ColorRampItem(int(t3),       QColor(210, 180, 140), "Alpine/Bare"),
        QgsColorRampShader.ColorRampItem(int(t4),       QColor(255, 255, 255), "Snow"),
    ]
    fcn.setColorRampItemList(items)

    shader = QgsRasterShader()
    shader.setRasterShaderFunction(fcn)

    pc_renderer = QgsSingleBandPseudoColorRenderer(color_layer.dataProvider(), 1, shader)
    pc_renderer.setClassificationMin(dem_min)
    pc_renderer.setClassificationMax(dem_max)
    color_layer.setRenderer(pc_renderer)

    print(f"  [OK] Shader ramp type: {fcn.colorRampType()} (2=Exact, 1=Discrete)")
    print(f"  [OK] Color items: {len(items)}")

    # 图层顺序：Hillshade 在底，Color 在顶
    # PyQGIS addMapLayer 会把图层插入到树顶部（显示在上层）
    # 所以先加 Color（顶层），再加 Hillshade（底层）
    project.addMapLayer(color_layer)
    project.addMapLayer(hs_layer)

    # === 2. 设置颜色层的半透明效果 ===
    color_layer.setOpacity(0.55)

    # 图层顺序：ColorLayer 在 ON TOP of Hillshade
    project.addMapLayer(color_layer)
    project.addMapLayer(hs_layer)

    # clone-reinsert 确保 ColorLayer 在树顶部（显示在上层）
    root = project.layerTreeRoot()
    for node in list(root.children()):
        if isinstance(node, QgsLayerTreeLayer) and node.name() == "Vegetation Zones":
            clone = node.clone()
            root.removeChildNode(node)
            root.insertChildNode(0, clone)
            print(f"  [OK] Layer reorder: ColorLayer on top")
            break

    tree_names = [c.name() for c in root.children()]
    print(f"  Layer tree: {tree_names}")

    # === 3. 构建布局 ===
    pw, ph = 420, 297  # A3 横向
    layout = QgsPrintLayout(project)
    layout.setName("VerticalZonationLayout")

    # 手动添加页面（避免 initializeDefaults 干扰渲染）
    page = QgsLayoutItemPage(layout)
    page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))
    layout.pageCollection().addPage(page)

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
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.5, QgsUnitTypes.LayoutMillimeters))
    map_item.setFrameStrokeColor(QColor(120, 120, 120))
    map_item.setCrs(hs_layer.crs())

    # 地图范围：DEM extent 缩放 5% 留边
    extent = hs_layer.extent()
    cx = extent.center().x()
    cy = extent.center().y()
    ew = extent.width() * 1.05
    eh = extent.height() * 1.05
    map_extent = QgsRectangle(cx - ew / 2, cy - eh / 2, cx + ew / 2, cy + eh / 2)
    map_item.setExtent(map_extent)

    map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))

    actual_w = map_w
    actual_h = map_h
    print(f"Map area: {actual_w:.0f}x{actual_h:.0f}mm")

    # === 地图要素 ===
    inset_elem = 8

    # 标题
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText(args.title)
    t_fmt = QgsTextFormat()
    title_font = QFont("SimHei", 20, QFont.Bold)
    t_fmt.setFont(title_font)
    t_fmt.setColor(QColor(30, 30, 30))
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.5)
    buf.setColor(QColor(255, 255, 255, 180))
    t_fmt.setBuffer(buf)
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter)
    title.setFrameEnabled(False)
    title.attemptResize(QgsLayoutSize(pw - 30, 20, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(15, 2, QgsUnitTypes.LayoutMillimeters))
    layout.raiseItem(title)
    print("[OK] 标题")

    # 指北针 — 地图内部右上角
    na_path = None
    for svg_dir in QgsApplication.svgPaths():
        if os.path.exists(svg_dir):
            for rd, ds, fs in os.walk(svg_dir):
                for f in fs:
                    if "north" in f.lower() and f.endswith(".svg"):
                        na_path = os.path.join(rd, f)
                        break
                if na_path:
                    break
            if na_path:
                break

    if na_path:
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(na_path)
        north.attemptResize(QgsLayoutSize(18, 22, QgsUnitTypes.LayoutMillimeters))
        north.attemptMove(QgsLayoutPoint(map_x + actual_w - inset_elem - 22, map_y + inset_elem, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(north)
        layout.raiseItem(north)
        print("[OK] 指北针 (SVG)")
    else:
        na_label = QgsLayoutItemLabel(layout)
        na_label.setText("N \u2191")
        label_fmt = QgsTextFormat()
        label_fmt.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        label_fmt.setColor(QColor(255, 255, 255))
        lbl_buf = QgsTextBufferSettings()
        lbl_buf.setEnabled(True)
        lbl_buf.setSize(1)
        lbl_buf.setColor(QColor(0, 0, 0, 150))
        label_fmt.setBuffer(lbl_buf)
        na_label.setTextFormat(label_fmt)
        na_label.setHAlign(Qt.AlignCenter)
        na_label.setFrameEnabled(False)
        na_label.attemptResize(QgsLayoutSize(25, 22, QgsUnitTypes.LayoutMillimeters))
        na_label.attemptMove(QgsLayoutPoint(map_x + actual_w - inset_elem - 28, map_y + inset_elem, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(na_label)
        layout.raiseItem(na_label)
        print("[OK] 指北针 (文字)")

    # 比例尺 — 地图内部底部居中
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setLinkedMap(map_item)
    scalebar.setStyle("Single Box")
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.applyDefaultSize()
    sw = 80
    sh = 10
    scale_y_from_bottom = 32
    sx = map_x + (actual_w - sw) / 2
    sy = map_y + actual_h - scale_y_from_bottom
    scalebar.attemptMove(QgsLayoutPoint(sx, sy, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(sw, sh, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)
    layout.raiseItem(scalebar)
    print(f"[OK] 比例尺 ({sx:.0f},{sy:.0f})")

    # 图例 — 地图内部右下角 + 半透明底
    lw, lh = 90, 85
    lx = map_x + actual_w - inset_elem - lw
    ly = map_y + actual_h - inset_elem - lh - 35
    lb = QgsLayoutItemShape(layout)
    lb.setShapeType(QgsLayoutItemShape.Rectangle)
    lb.setSymbol(QgsFillSymbol.createSimple({
        "color": "255,255,255,190",
        "outline_color": "180,180,180,160",
        "outline_width": "0.3",
    }))
    lb.attemptMove(QgsLayoutPoint(lx - 3, ly - 3, QgsUnitTypes.LayoutMillimeters))
    lb.attemptResize(QgsLayoutSize(lw + 6, lh + 6, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(lb)

    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("Vegetation Zones")
    legend.setFrameEnabled(False)
    legend.setAutoUpdateModel(True)
    for st in [QgsLegendStyle.Title, QgsLegendStyle.Group,
               QgsLegendStyle.Subgroup, QgsLegendStyle.Symbol,
               QgsLegendStyle.SymbolLabel]:
        fmt = legend.style(st)
        fmt.setFont(QFont("Microsoft YaHei", 8))

    legend.adjustBoxSize()
    legend.attemptResize(QgsLayoutSize(lw, lh, QgsUnitTypes.LayoutMillimeters))
    legend.attemptMove(QgsLayoutPoint(lx, ly, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(legend)
    layout.raiseItem(lb)
    layout.raiseItem(legend)
    print(f"[OK] 图例 ({lx:.0f},{ly:.0f})")

    # 数据源 — 地图内部左下角
    today = datetime.now().strftime("%Y-%m-%d")
    src = QgsLayoutItemLabel(layout)
    src.setText(f"Data: QGIS DEM | {today}")
    src_fmt = QgsTextFormat()
    src_fmt.setFont(QFont("Microsoft YaHei", 7))
    src_fmt.setColor(QColor(255, 255, 255))
    src_buf = QgsTextBufferSettings()
    src_buf.setEnabled(True)
    src_buf.setSize(0.8)
    src_buf.setColor(QColor(0, 0, 0, 150))
    src_fmt.setBuffer(src_buf)
    src.setTextFormat(src_fmt)
    src.setHAlign(Qt.AlignLeft)
    src.setFrameEnabled(False)
    src.attemptResize(QgsLayoutSize(180, 8, QgsUnitTypes.LayoutMillimeters))
    src.attemptMove(QgsLayoutPoint(map_x + inset_elem, map_y + actual_h - inset_elem - 8 - 2, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(src)
    layout.raiseItem(src)
    print("[OK] 数据源")

    # 高程范围 — 地图内部左上角
    elev = QgsLayoutItemLabel(layout)
    elev.setText(f"Elevation: {dem_min:.0f}m ~ {dem_max:.0f}m")
    elev_fmt = QgsTextFormat()
    elev_fmt.setFont(QFont("Microsoft YaHei", 8, QFont.Bold))
    elev_fmt.setColor(QColor(255, 255, 255))
    elev_buf = QgsTextBufferSettings()
    elev_buf.setEnabled(True)
    elev_buf.setSize(1)
    elev_buf.setColor(QColor(0, 0, 0, 160))
    elev_fmt.setBuffer(elev_buf)
    elev.setTextFormat(elev_fmt)
    elev.setHAlign(Qt.AlignLeft)
    elev.setFrameEnabled(False)
    elev.attemptResize(QgsLayoutSize(160, 10, QgsUnitTypes.LayoutMillimeters))
    elev.attemptMove(QgsLayoutPoint(map_x + inset_elem + 2, map_y + inset_elem + 26, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(elev)
    layout.raiseItem(elev)
    print("[OK] 高程标注")

    layout.refresh()

    # === 4. 导出 ===
    print(f"\nExporting...")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"Output: {args.output}")

    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = args.dpi

    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToImage(args.output, settings)

    project.clear()
    qgs.exitQgis()

    if result == QgsLayoutExporter.Success:
        print(f"[SUCCESS] {args.output}")
        print(f"  Paper: A3 Landscape ({pw}x{ph}mm)")
        print(f"  DPI: {args.dpi}")
        print(f"  Elevation: {dem_min:.1f}m ~ {dem_max:.1f}m")
        print(f"  Style: Discrete Pseudocolor + Hillshade")
    else:
        print(f"[ERROR] Export failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
