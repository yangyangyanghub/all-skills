#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test: Minimal DEM rendering with QgsHillshadeRenderer
Proves that DEM data renders in QgsPrintLayout.
"""

import os, sys
from datetime import datetime

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsRectangle, QgsHillshadeRenderer, QgsRasterBandStats, QgsTextFormat,
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt, QRectF


def init_qgis():
    qgs = QgsApplication([], False)
    qgs.setPrefixPath("C:/Program Files/QGIS 3.40.9/apps/qgis-ltr", True)
    qgs.initQgis()
    return qgs


def main():
    qgs = init_qgis()
    project = QgsProject.instance()
    project.clear()

    # Load DEM
    dem_path = r"E:\code\my-ai-workspace\qgis-source\tests\testdata\analysis\dem.tif"
    dem = QgsRasterLayer(dem_path, "DEM")
    if not dem.isValid():
        print("INVALID DEM")
        sys.exit(1)
    print(f"DEM: {dem.width()}x{dem.height()}")

    # Use QgsHillshadeRenderer (proven to work)
    renderer = QgsHillshadeRenderer(dem.dataProvider(), 1, 315, 45)
    renderer.setMultiDirectional(True)
    dem.setRenderer(renderer)

    project.addMapLayer(dem)

    # Create layout
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()

    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(297, 210, QgsUnitTypes.LayoutMillimeters))

    # Map item
    map_item = QgsLayoutItemMap(layout)
    layout.addLayoutItem(map_item)
    map_item.setRect(QRectF(10, 25, 277, 175))
    map_item.setFrameEnabled(True)
    map_item.setCrs(dem.crs())
    map_item.setExtent(dem.extent())
    map_item.attemptMove(QgsLayoutPoint(10, 25, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(277, 175, QgsUnitTypes.LayoutMillimeters))

    # Title
    title = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(title)
    title.setText("Hillshade Test - Should Show Terrain!")
    t_fmt = QgsTextFormat()
    t_fmt.setFont(QFont("Arial", 16, QFont.Bold))
    t_fmt.setColor(QColor(30, 30, 30))
    title.setTextFormat(t_fmt)
    title.setHAlign(Qt.AlignCenter)
    title.attemptResize(QgsLayoutSize(297, 15, QgsUnitTypes.LayoutMillimeters))
    title.attemptMove(QgsLayoutPoint(0, 5, QgsUnitTypes.LayoutMillimeters))

    # Export
    output = r"E:\code\my-ai-workspace\assets\generated\hillshade_test.png"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300

    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToImage(output, settings)

    project.clear()
    qgs.exitQgis()

    if result == QgsLayoutExporter.Success:
        print(f"SUCCESS: {output}")
    else:
        print(f"FAILED: {result}")


if __name__ == "__main__":
    main()
