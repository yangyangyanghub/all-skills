# -*- coding: utf-8 -*-
"""
城市关系强度图专用制图脚本
- 行政区面 + 城市点 + 强度连线
- 连线按 strength 字段分级渲染（越粗越强）
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, glob

from qgis.core import QgsApplication
_qgs = QgsApplication([], False)
_qgs.initQgis()

from qgis.core import (
    QgsProject, QgsVectorLayer,
    QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer,
    QgsGraduatedSymbolRenderer, QgsRendererRange,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutExporter, QgsLayoutPoint, QgsLayoutSize, QgsLayoutMeasurement,
    QgsUnitTypes, QgsRectangle,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

def log(msg):
    print(msg)
    sys.stdout.flush()

def make_fill_symbol(color, outline_color, outline_width):
    return QgsFillSymbol.createSimple({
        "color": color,
        "outline_color": outline_color,
        "outline_width": str(outline_width),
    })

def make_marker_symbol(color, size, outline_color="255,255,255", outline_width="0.8"):
    return QgsMarkerSymbol.createSimple({
        "color": color,
        "size": str(size),
        "outline_color": outline_color,
        "outline_width": str(outline_width),
    })

def make_line_symbol(color, width):
    return QgsLineSymbol.createSimple({
        "color": color,
        "width": str(width),
        "capstyle": "round",
    })

# ======================== 配置 ========================
data_dir = r'E:\BaiduNetdiskDownload\制图Data\制图Data\Data2\城市关系强度图'
output_path = r'E:\code\my-ai-workspace\assets\generated\城市关系强度图.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

page_w, page_h = 420, 297  # A3 横向
dpi = 300
title = "城 市 关 系 强 度 图"

# ======================== 1. 项目初始化 ========================
log("="*60)
log("   城市关系强度图 - 制图引擎")
log("="*60)

log("\n[1/5] 初始化项目...")
project = QgsProject.instance()
project.clear()

# 探测 CRS
probe_shp = glob.glob(os.path.join(data_dir, "*.shp"))[0]
probe = QgsVectorLayer(probe_shp, "probe", "ogr")
crs = probe.crs()
project.setCrs(crs)
log(f"  CRS: {crs.authid()}")

# ======================== 2. 加载图层 ========================
log("\n[2/5] 加载图层...")

# 2a. 行政面图层
admin_path = os.path.join(data_dir, "市级行政区划_p.shp")
admin_layer = QgsVectorLayer(admin_path, "行政区", "ogr")
admin_sym = make_fill_symbol("250,248,240,180", "200,180,150", 0.5)
admin_layer.setRenderer(QgsSingleSymbolRenderer(admin_sym))
# 行政区不标注，城市点已标注

project.addMapLayer(admin_layer)
log("  OK: 市级行政区划 (面)")

# 2b. 城市点图层
city_path = os.path.join(data_dir, "市_点_p.shp")
city_layer = QgsVectorLayer(city_path, "城市", "ogr")
city_sym = make_marker_symbol("200,50,50", 4.5, "255,255,255", 1.0)
city_layer.setRenderer(QgsSingleSymbolRenderer(city_sym))

# 城市名称标注
pal_city = QgsPalLayerSettings()
pal_city.fieldName = "NAME"
fmt_city = QgsTextFormat()
fmt_city.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
fmt_city.setColor(QColor(30, 30, 30))
buf_city = QgsTextBufferSettings()
buf_city.setEnabled(True)
buf_city.setSize(1.2)
buf_city.setColor(QColor(255, 255, 255))
fmt_city.setBuffer(buf_city)
pal_city.setFormat(fmt_city)
pal_city.enabled = True
pal_city.dist = 2.0
city_layer.setLabeling(QgsVectorLayerSimpleLabeling(pal_city))
city_layer.setLabelsEnabled(True)

project.addMapLayer(city_layer)
log("  OK: 城市点位 (点)")

# 2c. 关系强度连线（分级渲染）
line_path = os.path.join(data_dir, "城市关系连线_p.shp")
line_layer = QgsVectorLayer(line_path, "关系连线", "ogr")

# 按 strength 字段分级
strength_field = "strength"
# 使用自然间断点 (Quantile)
from qgis.core import QgsClassificationQuantile
classes = QgsClassificationQuantile().classes(line_layer, strength_field, 4)

# 颜色分级：浅橙 → 橙红 → 深红
color_ramp = [
    (0.05, 0.10, "255,180,100", 1.0),    # 弱：浅橙，细
    (0.10, 0.20, "255,140,50",  1.5),    # 中弱：橙
    (0.20, 0.30, "255,80,50",   2.2),    # 中强：橙红
    (0.30, 0.60, "200,20,20",   3.0),    # 强：深红，粗
]

# 自定义分级
ranges = []
for lower, upper, color_str, width in color_ramp:
    sym = make_line_symbol(color_str, width)
    label = f"{lower:.2f} - {upper:.2f}"
    rng = QgsRendererRange(lower, upper, sym, label)
    ranges.append(rng)

grad_renderer = QgsGraduatedSymbolRenderer(strength_field, ranges)
grad_renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
line_layer.setRenderer(grad_renderer)

project.addMapLayer(line_layer)
log("  OK: 关系连线 (分级渲染: 4级)")

# 调整图层顺序（面 → 线 → 点）
root = project.layerTreeRoot()
for child in root.children():
    root.removeChildNode(child)
root.addLayer(admin_layer)
root.addLayer(line_layer)
root.addLayer(city_layer)

# ======================== 3. 创建布局 ========================
log("\n[3/5] 创建布局...")

layout = QgsPrintLayout(project)
layout.setName("关系强度图布局")
layout.initializeDefaults()
page_collection = layout.pageCollection()
page_collection.page(0).setPageSize(QgsLayoutSize(page_w, page_h, QgsUnitTypes.LayoutMillimeters))

# 地图主体
map_w = page_w - 110
map_h = page_h - 55
map_item = QgsLayoutItemMap(layout)
map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))
map_item.attemptMove(QgsLayoutPoint(18, 18, QgsUnitTypes.LayoutMillimeters))

# 计算总范围
full_extent = None
for layer in [admin_layer, line_layer, city_layer]:
    ext = layer.extent()
    if not ext.isEmpty():
        if full_extent is None:
            full_extent = QgsRectangle(ext)
        else:
            full_extent.combineExtentWith(ext)

if full_extent:
    dx = full_extent.width() * 0.08
    dy = full_extent.height() * 0.08
    full_extent.setXMinimum(full_extent.xMinimum() - dx)
    full_extent.setXMaximum(full_extent.xMaximum() + dx)
    full_extent.setYMinimum(full_extent.yMinimum() - dy)
    full_extent.setYMaximum(full_extent.yMaximum() + dy)
    map_item.setExtent(full_extent)

map_item.setFrameEnabled(True)
map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.5))
layout.addLayoutItem(map_item)

# 标题
title_label = QgsLayoutItemLabel(layout)
title_label.setText(title)
title_label.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
title_label.setHAlign(Qt.AlignCenter)
title_label.setFrameEnabled(False)
title_label.attemptResize(QgsLayoutSize(page_w - 40, 14, QgsUnitTypes.LayoutMillimeters))
title_label.attemptMove(QgsLayoutPoint(20, 2, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(title_label)
log("  OK: 标题")

# 图例
legend = QgsLayoutItemLegend(layout)
legend.setTitle("图  例")
legend.setFrameEnabled(True)
legend.setBoxSpace(3)
legend.setSymbolWidth(12)
legend.setSymbolHeight(7)
legend.setAutoUpdateModel(True)
legend.updateLegend()

legend.attemptResize(QgsLayoutSize(85, 70, QgsUnitTypes.LayoutMillimeters))
legend.attemptMove(QgsLayoutPoint(page_w - 105, page_h - 85, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(legend)
log("  OK: 图例")

# 比例尺
scalebar = QgsLayoutItemScaleBar(layout)
scalebar.setLinkedMap(map_item)
scalebar.setStyle("Single Box")
scalebar.setUnits(QgsUnitTypes.DistanceMeters)
sf = scalebar.font()
sf.setFamily("Microsoft YaHei")
sf.setPointSize(8)
scalebar.setFont(sf)
scalebar.applyDefaultSize()
scalebar.attemptMove(QgsLayoutPoint(22, page_h - 20, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(scalebar)
log("  OK: 比例尺")

# 指北针
north = QgsLayoutItemPicture(layout)
for p in [r"C:\Program Files\QGIS 3.40.9\share\svg\north_arrows\default.svg",
          r"C:\Program Files\QGIS 3.40.9\share\svg\north_arrows\arrow.svg"]:
    if os.path.exists(p):
        north.setPicturePath(p)
        break
north.attemptResize(QgsLayoutSize(14, 14, QgsUnitTypes.LayoutMillimeters))
north.attemptMove(QgsLayoutPoint(page_w - 45, 22, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(north)
log("  OK: 指北针")

project.layoutManager().addLayout(layout)

# ======================== 4. 导出 ========================
log(f"\n[4/5] 导出图片 @ {dpi}DPI...")
exporter = QgsLayoutExporter(layout)
settings = QgsLayoutExporter.ImageExportSettings()
settings.dpi = dpi
if os.path.exists(output_path):
    os.remove(output_path)
result = exporter.exportToImage(output_path, settings)
if result == QgsLayoutExporter.Success:
    import pathlib
    size = pathlib.Path(output_path).stat().st_size
    log(f"  OK: {output_path}")
    log(f"      文件大小: {size/1024/1024:.1f} MB")
else:
    log(f"  失败: 错误码 {result}")

# 保存项目文件
qgz_path = output_path.replace(".png", ".qgz")
project.write(qgz_path)
log(f"  项目: {qgz_path}")

log(f"\n{'='*60}")
log("   制图完成!")
log(f"{'='*60}")

_qgs.exitQgis()
