#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地形晕渲行政区划图 - PyQGIS 制图脚本
参考洛阳市地图风格制作
"""

import os
import sys
import argparse
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QSize

def get_shapefile_paths(data_dir):
    """获取数据目录下的所有 shapefile 路径"""
    shp_files = []
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith('.shp'):
                shp_files.append(os.path.join(root, f))
    return shp_files

def find_dem_file(data_dir):
    """查找 DEM 栅格文件"""
    dem_extensions = ['.tif', '.tiff', '.img', '.dem']
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in dem_extensions and ('dem' in f.lower() or '高程' in f):
                return os.path.join(root, f)
    return None

def setup_qgis():
    """初始化 QGIS 环境"""
    qgs = QgsApplication([], False)
    qgs.initQgis()
    return qgs

def add_dem_hillshade_layer(project, dem_path, layer_name):
    """添加 DEM 地形晕渲图层"""
    dem_layer = QgsRasterLayer(dem_path, layer_name)
    if not dem_layer.isValid():
        print(f"DEM 图层加载失败: {dem_path}")
        return None
    
    # 山体阴影渲染
    shader_func = QgsColorRampShader()
    shader_func.setColorRampType(QgsColorRampShader.Interpolated)
    
    # 绿色系高程配色 - 参考洛阳市风格
    color_list = [
        QgsColorRampShader.ColorRampItem(0, QColor(180, 220, 150)),
        QgsColorRampShader.ColorRampItem(300, QColor(140, 200, 120)),
        QgsColorRampShader.ColorRampItem(600, QColor(100, 180, 90)),
        QgsColorRampShader.ColorRampItem(1000, QColor(80, 150, 70)),
        QgsColorRampShader.ColorRampItem(1500, QColor(60, 120, 50)),
        QgsColorRampShader.ColorRampItem(2000, QColor(50, 90, 40)),
    ]
    shader_func.setColorRampItemList(color_list)
    
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader_func)
    
    renderer = QgsSingleBandPseudoColorRenderer(
        dem_layer.dataProvider(), 
        dem_layer.bandCount(), 
        raster_shader
    )
    dem_layer.setRenderer(renderer)
    
    # 添加透明度
    dem_layer.setOpacity(0.85)
    
    project.addMapLayer(dem_layer)
    return dem_layer

def add_polygon_layer(project, shp_path, layer_name, outline_color, fill_color=None, line_width=0.5):
    """添加面图层"""
    layer = QgsVectorLayer(shp_path, layer_name, "ogr")
    if not layer.isValid():
        print(f"图层加载失败: {shp_path}")
        return None
    
    symbol = QgsFillSymbol.createSimple({
        'outline_color': outline_color,
        'outline_width': str(line_width),
        'color': fill_color if fill_color else '0,0,0,0',
    })
    
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    project.addMapLayer(layer)
    return layer

def add_line_layer(project, shp_path, layer_name, line_color, line_width=0.3):
    """添加线图层"""
    layer = QgsVectorLayer(shp_path, layer_name, "ogr")
    if not layer.isValid():
        print(f"图层加载失败: {shp_path}")
        return None
    
    symbol = QgsLineSymbol.createSimple({
        'color': line_color,
        'width': str(line_width),
    })
    
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    project.addMapLayer(layer)
    return layer

def add_point_label_layer(project, shp_path, layer_name, field_name):
    """添加点标注图层"""
    layer = QgsVectorLayer(shp_path, layer_name, "ogr")
    if not layer.isValid():
        print(f"图层加载失败: {shp_path}")
        return None
    
    # 透明点符号
    symbol = QgsMarkerSymbol.createSimple({
        'color': '0,0,0,0',
        'outline_color': '0,0,0,0',
        'size': '0',
    })
    
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    
    # 设置标注
    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = field_name
    label_settings.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setFont(QFont("微软雅黑", 9))
    text_format.setColor(QColor(50, 50, 50))
    text_format.setSize(9)
    
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1)
    buffer.setColor(QColor(255, 255, 255, 200))
    text_format.setBuffer(buffer)
    
    label_settings.setFormat(text_format)
    
    # 使用正确的枚举
    try:
        label_settings.placement = QgsPalLayerSettings.LabelPlacement.OverPoint
    except AttributeError:
        try:
            label_settings.placement = Qgis.LabelPlacement.OverPoint
        except:
            pass  # 跳过标注设置，继续运行
    
    label_settings.displayAll = True
    
    labeling = QgsVectorLayerSimpleLabeling(label_settings)
    layer.setLabeling(labeling)
    layer.setLabelsEnabled(True)
    
    project.addMapLayer(layer)
    return layer

def export_map(project, layers, output_path, paper_size, dpi):
    """导出地图"""
    # 获取图层范围
    extent = None
    for layer in layers:
        if layer:
            if extent is None:
                extent = layer.extent()
            else:
                extent.combineExtentWith(layer.extent())
    
    if extent is None:
        print("没有有效的图层范围")
        return False
    
    # 稍微扩大范围
    buffer = extent.width() * 0.05
    extent.setXMinimum(extent.xMinimum() - buffer)
    extent.setXMaximum(extent.xMaximum() + buffer)
    extent.setYMinimum(extent.yMinimum() - buffer)
    extent.setYMaximum(extent.yMaximum() + buffer)
    
    # 创建布局
    manager = project.layoutManager()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    
    # 页面尺寸设置
    page_size_map = {
        'A4': (210, 297),
        'A3': (297, 420),
        'A2': (420, 594),
        'A1': (594, 841),
    }
    
    width_mm, height_mm = page_size_map.get(paper_size.upper(), (297, 420))
    
    # 横向
    if width_mm < height_mm:
        width_mm, height_mm = height_mm, width_mm
    
    page = layout.pageCollection().pages()[0]
    page.setPageSize(QgsLayoutSize(width_mm, height_mm, QgsUnitTypes.LayoutMillimeters))
    
    # 添加地图项
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(20, 20, width_mm - 40, height_mm - 60)
    map_item.setExtent(extent)
    map_item.setLayers([layer for layer in layers if layer])
    map_item.setBackgroundColor(QColor(245, 248, 245))
    layout.addLayoutItem(map_item)
    
    # 添加标题
    title = QgsLayoutItemLabel(layout)
    title.setText("行政区划图")
    title.setFont(QFont("微软雅黑", 24, QFont.Bold))
    title.setFontColor(QColor(40, 80, 40))
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(30, 15, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)
    
    # 添加指北针
    north = QgsLayoutItemPicture(layout)
    north.setPicturePath(":/images/north_arrows/north_arrow_01.svg")
    north.attemptResize(QgsLayoutSize(20, 30, QgsUnitTypes.LayoutMillimeters))
    north.attemptMove(QgsLayoutPoint(width_mm - 35, height_mm - 50, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north)
    
    # 添加比例尺
    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setStyle('Single Box')
    scale_bar.setLinkedMap(map_item)
    scale_bar.setUnitLabel('km')
    scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setNumberOfSegmentsLeft(0)
    scale_bar.attemptResize(QgsLayoutSize(60, 15, QgsUnitTypes.LayoutMillimeters))
    scale_bar.attemptMove(QgsLayoutPoint(30, height_mm - 35, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale_bar)
    
    # 导出
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = dpi
    
    result = exporter.exportToImage(output_path, settings)
    
    if result == QgsLayoutExporter.Success:
        print(f"地图已导出到: {output_path}")
        return True
    else:
        print(f"导出失败，错误码: {result}")
        return False

def main():
    parser = argparse.ArgumentParser(description='DEM 地形晕渲行政区划图')
    parser.add_argument('--admin-data', required=True, help='行政区划数据目录')
    parser.add_argument('--dem-data', required=True, help='DEM 数据目录')
    parser.add_argument('--output', required=True, help='输出 PNG 路径')
    parser.add_argument('--paper-size', default='A3', help='纸张尺寸: A4, A3, A2, A1')
    parser.add_argument('--dpi', type=int, default=300, help='DPI 分辨率')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("地形晕渲行政区划图生成器")
    print("=" * 50)
    
    # 初始化 QGIS
    qgs = setup_qgis()
    
    # 创建项目
    project = QgsProject.instance()
    
    # 查找数据文件
    admin_shps = get_shapefile_paths(args.admin_data)
    dem_file = find_dem_file(args.dem_data)
    
    print(f"\n找到 {len(admin_shps)} 个行政区划 Shapefile")
    print(f"找到 DEM 文件: {dem_file}")
    
    if not dem_file:
        print("错误: 未找到 DEM 文件")
        return 1
    
    layers = []
    
    # 1. 添加 DEM 地形晕渲层（最底层）
    print("\n正在加载 DEM 地形图层...")
    dem_layer = add_dem_hillshade_layer(project, dem_file, "DEM_地形晕渲")
    if dem_layer:
        layers.append(dem_layer)
        print("✓ DEM 图层已添加")
    
    # 2. 添加行政区划面图层
    print("\n正在加载行政区划图层...")
    for shp in admin_shps:
        name = os.path.splitext(os.path.basename(shp))[0]
        
        # 检测图层几何类型
        layer_test = QgsVectorLayer(shp, "test", "ogr")
        if not layer_test.isValid():
            continue
            
        geom_type = layer_test.geometryType()
        
        if geom_type == QgsWkbTypes.PolygonGeometry:
            # 面图层 - 行政区划边界
            admin_layer = add_polygon_layer(
                project, shp, name,
                outline_color='80, 80, 80, 200',
                fill_color=None,  # 透明填充
                line_width=0.6
            )
            if admin_layer:
                layers.append(admin_layer)
                print(f"✓ 添加面图层: {name}")
        
        elif geom_type == QgsWkbTypes.LineGeometry:
            # 线图层 - 道路/河流等
            line_layer = add_line_layer(
                project, shp, name,
                line_color='100, 150, 200, 180',
                line_width=0.3
            )
            if line_layer:
                layers.append(line_layer)
                print(f"✓ 添加线图层: {name}")
        
        elif geom_type == QgsWkbTypes.PointGeometry:
            # 点图层 - 标注点
            fields = [f.name() for f in layer_test.fields()]
            name_field = None
            for f in fields:
                if f in ['NAME', 'name', '名称', '地名', 'Name']:
                    name_field = f
                    break
            
            if name_field:
                label_layer = add_point_label_layer(
                    project, shp, name, name_field
                )
                if label_layer:
                    layers.append(label_layer)
                    print(f"✓ 添加标注图层: {name} (字段: {name_field})")
    
    print(f"\n共添加 {len(layers)} 个图层")
    
    # 调整图层顺序: DEM -> 面 -> 线 -> 点/标注
    root = project.layerTreeRoot()
    for i, layer in enumerate(reversed(layers)):
        layer_node = root.findLayer(layer.id())
        if layer_node:
            root.insertChildNode(0, layer_node.clone())
    
    # 导出地图
    print("\n正在生成并导出地图...")
    success = export_map(project, layers, args.output, args.paper_size, args.dpi)
    
    if success:
        print("\n✓ 地图生成完成!")
    else:
        print("\n✗ 地图生成失败")
    
    qgs.exitQgis()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
