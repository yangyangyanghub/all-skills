# -*- coding: utf-8 -*-
"""
点密度图生成器
用法: python-qgis-ltr.bat scripts/dot_density_map.py --data 数据目录 --output 输出路径 [--dpi DPI] [--paper-size A4|A3] [--orientation portrait|landscape]
"""

import os
import sys
import random
import argparse

from qgis.core import (
    QgsApplication, QgsVectorLayer, QgsProject, QgsPrintLayout,
    QgsMapSettings, QgsMapRendererJob, QgsMapRendererSequentialJob, QgsMapRendererCustomPainterJob,
    QgsRectangle, QgsLayoutItemScaleBar, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemMap, QgsLayoutItemPicture,
    QgsReadWriteContext, QgsFillSymbol, QgsSimpleFillSymbolLayer,
    QgsLineSymbol, QgsSimpleLineSymbolLayer,
    QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeatureRequest, QgsExpression, QgsMarkerSymbol,
    QgsSimpleMarkerSymbolLayer, QgsSymbolLayerUtils,
    QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat,
    QgsLayoutItemPage, QgsUnitTypes,
    QgsGeometry, QgsFeature, QgsVectorLayerSimpleLabeling
)
from qgis.PyQt.QtGui import QColor, QPainter, QImage, QFont
from qgis.PyQt.QtCore import QSize, Qt, QRectF, QSizeF, QPointF
from qgis.PyQt.QtXml import QDomDocument

import pandas as pd
import glob

class DotDensityMapper:
    """点密度图生成器"""
    
    def __init__(self, data_dir, output_path, template_name='population', 
                 paper_size='A3', orientation='landscape', dpi=300):
        self.data_dir = data_dir
        self.output_path = output_path
        self.template_name = template_name
        self.paper_size = paper_size
        self.orientation = orientation
        self.dpi = dpi
        self.qgs = None
        self.project = None
        self.admin_layer = None
        self.dot_layer = None
        self.population_data = {}
        
        # 纸张尺寸定义（毫米）
        self.paper_sizes = {
            'A4': (210, 297),
            'A3': (297, 420),
            'A2': (420, 594),
            'A1': (594, 841),
            'A0': (841, 1189)
        }
        
    def init_qgis(self):
        """初始化 QGIS 环境"""
        self.qgs = QgsApplication([], False)
        self.qgs.setPrefixPath("C:/Program Files/QGIS 3.40.9/apps/qgis-ltr", True)
        self.qgs.initQgis()
        self.project = QgsProject.instance()
        print("✅ QGIS 初始化完成")
        
    def load_population_data(self):
        """加载 Excel 人口数据"""
        xls_files = glob.glob(os.path.join(self.data_dir, "*.xls"))
        if not xls_files:
            print("⚠️ 未找到 Excel 文件")
            return False
            
        xls_path = xls_files[0]
        print(f"📊 加载人口数据: {os.path.basename(xls_path)}")
        
        try:
            df = pd.read_excel(xls_path, engine='xlrd')
            # 获取人口列（选择最后一列或指定列）
            pop_cols = [c for c in df.columns if '人口' in c or 'pop' in c.lower()]
            if pop_cols:
                pop_col = pop_cols[-1]  # 使用最晚年份
                print(f"   使用人口列: {pop_col}")
            else:
                # 取第4列（索引3）作为人口数据
                pop_col = df.columns[3]
                print(f"   默认使用人口列: {pop_col}")
                
            for _, row in df.iterrows():
                pac = str(int(row['PAC'])) if pd.notna(row['PAC']) else ''
                pop = int(row[pop_col]) if pd.notna(row[pop_col]) else 0
                name = str(row.get('NAME', ''))
                self.population_data[pac] = {'population': pop, 'name': name}
                
            print(f"   ✅ 加载 {len(self.population_data)} 条人口数据")
            return True
        except Exception as e:
            print(f"❌ 读取 Excel 失败: {e}")
            return False
            
    def load_admin_layer(self):
        """加载行政区划图层"""
        shp_files = glob.glob(os.path.join(self.data_dir, "*/县级行政区划.shp"))
        if not shp_files:
            shp_files = glob.glob(os.path.join(self.data_dir, "县级行政区划.shp"))
            
        if not shp_files:
            print("❌ 未找到行政区划 Shapefile")
            return False
            
        self.admin_layer = QgsVectorLayer(shp_files[0], "县级行政区划", "ogr")
        if not self.admin_layer.isValid():
            print("❌ 行政区划图层无效")
            return False
            
        print(f"🗺️ 加载行政区划: {len(self.admin_layer)} 个要素")
        self.project.addMapLayer(self.admin_layer)
        return True
        
    def generate_dots(self, dots_per_person=0.0001):
        """生成点密度图层"""
        print("🔵 生成点密度图层...")
        
        # 从内存创建点图层
        uri = "Point?crs=epsg:4499&field=id:integer&field=population:integer&index=yes"
        self.dot_layer = QgsVectorLayer(uri, "人口点", "memory")
        
        if not self.dot_layer:
            print("❌ 创建点图层失败")
            return False
            
        # 获取人口范围，计算合适的点值
        populations = [d['population'] for d in self.population_data.values()]
        max_pop = max(populations) if populations else 1000000
        
        # 调整比例使点数合理（约 5-20 点/区县）
        dots_per_value = 10.0 / max_pop if max_pop > 0 else 0.00001
        
        provider = self.dot_layer.dataProvider()
        features_to_add = []
        
        feat_id = 0
        for feature in self.admin_layer.getFeatures():
            pac = str(feature['PAC']) if feature['PAC'] else ''
            pop_info = self.population_data.get(pac)
            if not pop_info:
                continue
                
            population = pop_info['population']
            num_dots = max(1, int(population * dots_per_value))
            
            # 获取行政区划几何的边界框
            geom = feature.geometry()
            if geom.isEmpty():
                continue
                
            bbox = geom.boundingBox()
            
            # 在行政区划内随机布点
            points_added = 0
            attempts = 0
            max_attempts = num_dots * 100  # 防止无限循环
            
            while points_added < num_dots and attempts < max_attempts:
                attempts += 1
                
                # 在边界框内随机生成点
                x = random.uniform(bbox.xMinimum(), bbox.xMaximum())
                y = random.uniform(bbox.yMinimum(), bbox.yMaximum())
                point = QgsPointXY(x, y)
                
                # 检查点是否在多边形内
                if geom.contains(QgsGeometry.fromPointXY(point)):
                    feat = QgsFeature()
                    feat.setGeometry(QgsGeometry.fromPointXY(point))
                    feat.setAttributes([feat_id, population])
                    features_to_add.append(feat)
                    points_added += 1
                    feat_id += 1
                    
            print(f"   {pop_info['name']}: 人口 {population}, 生成 {points_added} 个点")
            
        provider.addFeatures(features_to_add)
        self.dot_layer.updateExtents()
        self.project.addMapLayer(self.dot_layer)
        
        print(f"✅ 生成完成，共 {len(features_to_add)} 个点")
        return True
        
    def apply_styles(self):
        """应用样式"""
        # 行政区划样式（浅色填充，深色边框）
        admin_symbol = QgsFillSymbol.createSimple({
            'color': '240,245,250,150',
            'outline_color': '100,120,140',
            'outline_width': '0.5',
            'style': 'solid'
        })
        self.admin_layer.setRenderer(QgsSingleSymbolRenderer(admin_symbol))
        
        # 标注名称
        labeling = QgsPalLayerSettings()
        labeling.fieldName = 'NAME'
        labeling.enabled = True
        
        text_format = QgsTextFormat()
        text_format.setSize(8)
        text_format.setColor(QColor(40, 60, 80))
        text_format.setFont(QFont('Microsoft YaHei'))
        labeling.setFormat(text_format)
        
        from qgis.core import QgsVectorLayerSimpleLabeling
        simple_labeling = QgsVectorLayerSimpleLabeling(labeling)
        self.admin_layer.setLabeling(simple_labeling)
        self.admin_layer.setLabelsEnabled(True)
        
        # 点样式（红色圆点）
        dot_symbol = QgsMarkerSymbol.createSimple({
            'color': '220,50,50',
            'size': '1.5',
            'outline_color': '200,40,40',
            'outline_width': '0.2'
        })
        self.dot_layer.setRenderer(QgsSingleSymbolRenderer(dot_symbol))
        
    def create_layout_and_export(self):
        """导出地图图片 - 使用简化渲染方式"""
        width_mm, height_mm = self.paper_sizes[self.paper_size]
        if self.orientation == 'portrait':
            width_mm, height_mm = height_mm, width_mm
            
        print(f"📐 创建布局: {self.paper_size} {self.orientation} ({width_mm}x{height_mm}mm, {self.dpi}DPI)")
        
        # 使用简化的渲染方式
        # 获取图层范围
        extent = self.admin_layer.extent()
        
        # 计算图像尺寸
        img_width = int(width_mm / 25.4 * self.dpi)
        img_height = int(height_mm / 25.4 * self.dpi)
        
        print(f"   图像尺寸: {img_width}x{img_height} 像素")
        
        # 渲染设置
        map_settings = QgsMapSettings()
        map_settings.setLayers([self.admin_layer, self.dot_layer])
        map_settings.setExtent(extent)
        map_settings.setOutputSize(QSize(img_width, img_height))
        map_settings.setDestinationCrs(self.admin_layer.crs())
        map_settings.setOutputDpi(self.dpi)
        map_settings.setBackgroundColor(QColor(255, 255, 255))
        map_settings.setFlag(QgsMapSettings.DrawLabeling, True)
        map_settings.setFlag(QgsMapSettings.Antialiasing, True)
        
        # 渲染图像
        # 创建图像
        image = QImage(QSize(img_width, img_height), QImage.Format_ARGB32_Premultiplied)
        image.fill(QColor(255, 255, 255))
        
        # 创建渲染器
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 渲染地图
        job = QgsMapRendererCustomPainterJob(map_settings, painter)
        job.start()
        job.waitForFinished()
        
        painter.end()
        
        output_dir = os.path.dirname(self.output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        export_path = self.output_path
        if not export_path.endswith('.png'):
            export_path += '.png'
            
        print(f"💾 导出到: {export_path}")
            
        success = image.save(export_path)
        if success:
            print(f"✅ 导出成功: {export_path}")
            return True
        else:
            print("❌ 保存图像失败")
            return False
            
    def run(self):
        """执行完整流程"""
        try:
            self.init_qgis()
            
            if not self.load_population_data():
                return False
                
            if not self.load_admin_layer():
                return False
                
            if not self.generate_dots():
                return False
                
            self.apply_styles()
            
            if not self.create_layout_and_export():
                return False
                
            return True
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.qgs:
                self.qgs.exitQgis()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="点密度图生成器")
    parser.add_argument("--data", required=True, help="数据目录路径")
    parser.add_argument("--output", default="assets/generated/population_dot_map.png", help="输出路径")
    parser.add_argument("--template", default="population", help="模板名")
    parser.add_argument("--paper-size", default="A3", choices=['A4', 'A3', 'A2', 'A1', 'A0'])
    parser.add_argument("--orientation", default="landscape", choices=['portrait', 'landscape'])
    parser.add_argument("--dpi", type=int, default=300)
    
    args = parser.parse_args()
    
    mapper = DotDensityMapper(
        data_dir=args.data,
        output_path=args.output,
        template_name=args.template,
        paper_size=args.paper_size,
        orientation=args.orientation,
        dpi=args.dpi
    )
    
    if mapper.run():
        print("\n🎉 制图完成！")
        sys.exit(0)
    else:
        print("\n❌ 制图失败")
        sys.exit(1)
