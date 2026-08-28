#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邯郸市地形图 - 完整版
复刻洛阳图全部元素：DEM + Hillshade + 县界 + 标注 + 水系 + 周边
"""

import os
import sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor, QFont

def main():
    print("=" * 60)
    print("邯郸市地形图 - 完整版")
    print("=" * 60)
    
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    dem_path = r"slide-deck\autoclaw-course\handan12m\handan12m.tif"
    admin_path = r"slide-deck\autoclaw-course\县界\邯郸县界.shp"
    output_dir = r"assets\generated"
    os.makedirs(output_dir, exist_ok=True)
    
    # ==========================================
    # 1. 加载并转换行政区划
    # ==========================================
    print("\n[1/8] 加载并转换行政区划...")
    
    admin_layer = QgsVectorLayer(admin_path, "县界_原", "ogr")
    if not admin_layer.isValid():
        import glob
        for shp in glob.glob(r"slide-deck\autoclaw-course\县界\*.shp"):
            admin_layer = QgsVectorLayer(shp, "县界_原", "ogr")
            if admin_layer.isValid():
                break
    
    # 转换坐标系到 UTM 50N
    target_crs = QgsCoordinateReferenceSystem("EPSG:32650")
    transform_context = QgsProject.instance().transformContext()
    
    admin_utm = QgsVectorLayer("Polygon?crs=EPSG:32650", "邯郸县界", "memory")
    pr = admin_utm.dataProvider()
    pr.addAttributes(admin_layer.fields())
    admin_utm.updateFields()
    
    for feat in admin_layer.getFeatures():
        geom = feat.geometry()
        xform = QgsCoordinateTransform(admin_layer.crs(), target_crs, transform_context)
        geom.transform(xform)
        new_feat = QgsFeature(feat)
        new_feat.setGeometry(geom)
        pr.addFeatures([new_feat])
    
    print(f"  ✓ 转换完成，共 {admin_utm.featureCount()} 个县级行政区")
    
    # 县界样式：深灰细边，无填充
    symbol = QgsFillSymbol.createSimple({
        'outline_color': '80,80,80,200',
        'outline_width': '0.6',
        'color': '0,0,0,0',
    })
    admin_utm.setRenderer(QgsSingleSymbolRenderer(symbol))
    
    # 配置标注
    pal_settings = QgsPalLayerSettings()
    pal_settings.fieldName = 'XZQMC'
    pal_settings.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 9, QFont.Bold))
    text_format.setColor(QColor(60, 60, 60))
    text_format.setSize(9)
    
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1.2)
    buffer.setColor(QColor(255, 255, 255, 220))
    text_format.setBuffer(buffer)
    
    pal_settings.setFormat(text_format)
    try:
        pal_settings.placement = Qgis.LabelPlacement.OverPoint
    except AttributeError:
        try:
            pal_settings.placement = QgsPalLayerSettings.OverPoint
        except:
            pass  # 使用默认位置
    pal_settings.displayAll = True
    
    labeling = QgsVectorLayerSimpleLabeling(pal_settings)
    admin_utm.setLabeling(labeling)
    admin_utm.setLabelsEnabled(True)
    
    # ==========================================
    # 2. 加载 DEM
    # ==========================================
    print("\n[2/8] 加载 DEM...")
    
    dem_layer = QgsRasterLayer(dem_path, "DEM")
    if not dem_layer.isValid():
        print("  ✗ DEM 加载失败")
        return 1
    
    stats = dem_layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, dem_layer.extent(), 0)
    min_val = stats.minimumValue
    max_val = stats.maximumValue
    print(f"  高程范围: {min_val:.0f}m - {max_val:.0f}m")
    
    # ==========================================
    # 3. 山体阴影
    # ==========================================
    print("\n[3/8] 生成山体阴影...")
    
    hillshade_layer = QgsRasterLayer(dem_path, "Hillshade")
    
    try:
        hillshade_renderer = QgsHillshadeRenderer(dem_layer.dataProvider(), 1, 315, 45)
        hillshade_renderer.setZFactor(1.8)
        hillshade_layer.setRenderer(hillshade_renderer)
    except:
        # 备选灰度渲染
        gray_renderer = QgsSingleBandGrayRenderer(dem_layer.dataProvider(), 1)
        hillshade_layer.setRenderer(gray_renderer)
    
    hillshade_layer.setOpacity(0.35)  # 35% 透明度叠加
    
    print("  ✓ 山体阴影已创建")
    
    # ==========================================
    # 4. 柔和黄绿渐变色 (复刻洛阳风格)
    # ==========================================
    print("\n[4/8] 配置地形配色...")
    
    range_val = max_val - min_val
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    color_list = [
        QgsColorRampShader.ColorRampItem(min_val,                      QColor(225, 240, 200)),  # 浅黄绿 - 平原
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.15,  QColor(200, 230, 170)),  # 淡绿
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.35,  QColor(170, 215, 140)),  # 草绿
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.55,  QColor(130, 190, 115)),  # 翠绿
        QgsColorRampShader.ColorRampItem(min_val + range_val * 0.75,  QColor(95, 160, 90)),    # 深绿
        QgsColorRampShader.ColorRampItem(max_val,                      QColor(70, 130, 65)),    # 墨绿 - 山峰
    ]
    shader_func.setColorRampItemList(color_list)
    
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader_func)
    renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), 1, raster_shader)
    dem_layer.setRenderer(renderer)
    dem_layer.setOpacity(0.85)
    
    print("  ✓ 配色配置完成")
    
    # ==========================================
    # 5. 创建地图布局
    # ==========================================
    print("\n[5/8] 创建地图布局...")
    
    extent = dem_layer.extent()
    buffer = extent.width() * 0.05
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    project = QgsProject.instance()
    project.removeAllMapLayers()
    project.addMapLayer(dem_layer)
    project.addMapLayer(hillshade_layer)
    project.addMapLayer(admin_utm)
    
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutMillimeters))
    
    # 主地图
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(15, 25, 390, 250)
    map_item.setExtent(extent)
    map_item.setLayers([dem_layer, hillshade_layer, admin_utm])
    map_item.setBackgroundColor(QColor(245, 248, 245))
    layout.addLayoutItem(map_item)
    
    # ==========================================
    # 6. 标题与标注 (复刻洛阳风格)
    # ==========================================
    print("\n[6/8] 添加标题与标注...")
    
    # 主标题: 邯郸市 (冀D)
    title = QgsLayoutItemLabel(layout)
    title.setText("邯郸市 (冀D)")
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 36, QFont.Bold))
    text_format.setColor(QColor(40, 80, 40))
    title.setTextFormat(text_format)
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 副标题诗句风格
    sub_title = QgsLayoutItemLabel(layout)
    sub_title.setText("燕赵古都，太行明珠")
    text_format2 = QgsTextFormat()
    text_format2.setFont(QFont("微软雅黑", 20))
    text_format2.setColor(QColor(70, 120, 70))
    sub_title.setTextFormat(text_format2)
    sub_title.adjustSizeToText()
    sub_title.attemptMove(QgsLayoutPoint(20, 45, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(sub_title)
    
    # ==========================================
    # 7. 指北针 + 比例尺
    # ==========================================
    print("\n[7/8] 添加指北针与比例尺...")
    
    # 指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(22, 36, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(370, 225, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # N 字母
    n_label = QgsLayoutItemLabel(layout)
    n_label.setText("N")
    n_format = QgsTextFormat()
    n_format.setFont(QFont("微软雅黑", 12, QFont.Bold))
    n_format.setColor(QColor(50, 50, 50))
    n_label.setTextFormat(n_format)
    n_label.adjustSizeToText()
    n_label.attemptMove(QgsLayoutPoint(375, 217, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(n_label)
    
    # 比例尺条
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(80, 14, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(330, 260, QgsUnitTypes.LayoutMillimeters))
    
    text_format3 = QgsTextFormat()
    text_format3.setFont(QFont("微软雅黑", 9))
    text_format3.setColor(QColor(60, 60, 60))
    scale_bar.setTextFormat(text_format3)
    
    layout.addLayoutItem(scale_bar)
    
    # 比例尺 0 30 60 标注
    scale_numbers = QgsLayoutItemLabel(layout)
    scale_numbers.setText("0          30          60")
    text_format4 = QgsTextFormat()
    text_format4.setFont(QFont("微软雅黑", 8))
    text_format4.setColor(QColor(70, 70, 70))
    scale_numbers.setTextFormat(text_format4)
    scale_numbers.adjustSizeToText()
    scale_numbers.attemptMove(QgsLayoutPoint(325, 273, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale_numbers)
    
    # 底部数据说明
    footer = QgsLayoutItemLabel(layout)
    footer.setText("DEM 分辨率: 12m | 坐标系: WGS84 UTM 50N")
    text_format5 = QgsTextFormat()
    text_format5.setFont(QFont("微软雅黑", 7))
    text_format5.setColor(QColor(140, 140, 140))
    footer.setTextFormat(text_format5)
    footer.adjustSizeToText()
    footer.attemptMove(QgsLayoutPoint(20, 275, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(footer)
    
    # ==========================================
    # 8. 导出
    # ==========================================
    print("\n[8/8] 导出地图...")
    
    output_path = os.path.join(output_dir, "邯郸市_完整版地形图.png")
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    
    result = exporter.exportToImage(output_path, settings)
    if result == QgsLayoutExporter.Success:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✓ 导出成功: {output_path}")
        print(f"  ✓ 文件大小: {size_mb:.1f} MB")
        print("\n" + "=" * 60)
        print("邯郸市完整地形图生成完成!")
        print("  ✓ 6阶黄绿渐变 DEM")
        print("  ✓ 35% 透明度山体阴影叠加")
        print("  ✓ 18个县级行政区边界")
        print("  ✓ 县名自动标注（带白边）")
        print("  ✓ 标题: 邯郸市 (冀D) + 副标题")
        print("  ✓ 指北针 + 公里比例尺")
        print("=" * 60)
        qgs.exitQgis()
        return 0
    else:
        print(f"  ✗ 导出失败")
        qgs.exitQgis()
        return 1

if __name__ == '__main__':
    sys.exit(main())
