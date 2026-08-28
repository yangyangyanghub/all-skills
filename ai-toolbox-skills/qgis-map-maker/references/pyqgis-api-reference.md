# PyQGIS API 文档参考

> **官方文档地址**: https://qgis.org/pyqgis/master/core/
> 当脚本遇到参数签名错误、API 废弃等问题时，优先查阅此文档确认正确用法。

---

## 核心模块

| 模块 | 文档 | 主要用途 |
|------|------|----------|
| `qgis.core` | [Core API](https://qgis.org/pyqgis/master/core/) | 核心类：图层、渲染、布局、几何 |
| `qgis.gui` | [GUI API](https://qgis.org/pyqgis/master/gui/) | 图形界面组件 |
| `qgis.analysis` | [Analysis API](https://qgis.org/pyqgis/master/analysis/) | 空间分析、地形分析 |
| `qgis.processing` | [Processing API](https://qgis.org/pyqgis/master/processing/) | 处理框架算法 |

---

## 常用类速查

### 渲染相关

| 类名 | 文档链接 | 说明 |
|------|----------|------|
| `QgsMapSettings` | [文档](https://qgis.org/pyqgis/master/core/QgsMapSettings.html#qgis.core.QgsMapSettings) | 地图渲染设置（图层、范围、DPI） |
| `QgsMapRendererCustomPainterJob` | [文档](https://qgis.org/pyqgis/master/core/QgsMapRendererCustomPainterJob.html) | 自定义渲染器 |
| `QgsVectorLayer` | [文档](https://qgis.org/pyqgis/master/core/QgsVectorLayer.html) | 矢量图层 |
| `QgsSymbol` / `QgsMarkerSymbol` / `QgsFillSymbol` | [文档](https://qgis.org/pyqgis/master/core/QgsSymbol.html) | 符号系统 |

### 布局相关

| 类名 | 文档链接 | 说明 |
|------|----------|------|
| `QgsPrintLayout` | [文档](https://qgis.org/pyqgis/master/core/QgsPrintLayout.html) | 打印布局 |
| `QgsLayoutItemPage` | [文档](https://qgis.org/pyqgis/master/core/QgsLayoutItemPage.html) | 布局页面 |
| `QgsLayoutItemMap` | [文档](https://qgis.org/pyqgis/master/core/QgsLayoutItemMap.html) | 地图项 |
| `QgsLayoutItemLabel` | [文档](https://qgis.org/pyqgis/master/core/QgsLayoutItemLabel.html) | 文本标签 |
| `QgsLayoutItemLegend` | [文档](https://qgis.org/pyqgis/master/core/QgsLayoutItemLegend.html) | 图例 |
| `QgsLayoutItemScaleBar` | [文档](https://qgis.org/pyqgis/master/core/QgsLayoutItemScaleBar.html) | 比例尺 |

### 标注相关

| 类名 | 文档链接 | 说明 |
|------|----------|------|
| `QgsPalLayerSettings` | [文档](https://qgis.org/pyqgis/master/core/QgsPalLayerSettings.html) | 图层标注设置 |
| `QgsTextFormat` | [文档](https://qgis.org/pyqgis/master/core/QgsTextFormat.html) | 文本格式 |
| `QgsVectorLayerSimpleLabeling` | [文档](https://qgis.org/pyqgis/master/core/QgsVectorLayerSimpleLabeling.html) | 简单标注 |

---

## 高频 API 问题排查

### 1. 页面尺寸设置（QGIS 3.10+ 变更）

```python
# ❌ 旧写法（已废弃）
page.setPageSize('Custom', QSizeF(w, h))
page.setPageSize(QSizeF(w, h))

# ✅ 新写法
from qgis.core import QgsLayoutSize, QgsUnitTypes
page.setPageSizeWithUnits(QgsLayoutSize(w, h, QgsUnitTypes.LayoutMillimeters))
# 或使用预设
page.setPageSize('A4')
page.setPageSize('A3')
```

### 2. 标注放置模式（QGIS 3.16+ 变更）

```python
# ❌ 旧枚举值
labeling.placement = QgsPalLayerSettings.Centroid  # 已废弃

# ✅ 新写法 - 直接不设置 placement 或使用整数
from qgis.core import Qgis
labeling.placement = Qgis.LabelPlacement.Polygon  # 面要素标注
```

### 3. 布局项定位

```python
# ✅ 推荐写法
from PyQt5.QtCore import QPointF

# attemptMove 接受 QPointF
title_label.attemptMove(QPointF(x, y))
# 或使用 attemptResize
title_label.attemptResize(QgsLayoutSize(w, h, QgsUnitTypes.LayoutMillimeters))
```

---

## 文档构建工具

- **源码仓库**: https://github.com/qgis/pyqgis-api-docs-builder
- **在线文档**: https://qgis.org/pyqgis/
  - 稳定版（LTR）: https://qgis.org/pyqgis/ltr/core/
  - 开发版: https://qgis.org/pyqgis/master/core/

> **注意**: 本项目使用 QGIS 3.40.9，应参考 `master`（最新稳定版）或 `ltr`（长期支持版）文档。
> 不同 QGIS 版本的 API 签名可能不同，查阅时注意版本切换。

---

## 常见错误速查表

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `QgsComposition object has no attribute...` | QgsComposition 已废弃 | 改用 QgsPrintLayout |
| `argument 1 has unexpected type 'QSizeF'` | setPageSize() 签名变更 | 用 setPageSizeWithUnits(QgsLayoutSize) |
| `QgsPalLayerSettings.Centroid` 不存在 | 枚举值迁移到 Qgis.LabelPlacement | 用 Qgis.LabelPlacement.Polygon |
| `attemptMove(): argument 1 has unexpected type 'QPointF'` | 布局项位置 API 可能变更 | 检查 QGIS 版本文档 |
| `QgsVectorLayer.setLabeling()` 类型错误 | 需用 QgsVectorLayerSimpleLabeling 包装 | simple = QgsVectorLayerSimpleLabeling(settings); layer.setLabeling(simple) |
| `QgsLayoutItemScaleBar.setNumberOfSegmentsRight()` 不存在 | 该方法在 QGIS 3.40+ 已移除 | 只使用 `setNumberOfSegmentsLeft()` + `applyDefaultSize()` |
| 布局元素 `setFont(QFont)` 有 DeprecationWarning | 推荐改用 `setTextFormat(QgsTextFormat)` | 旧方法在 3.40 仍可用，但后续版本可能移除 |
| **禁止使用 `QgsMapRendererCustomPainterJob` 输出最终地图** | 只输出地图主体，无标题/图例等布局要素 | 必须使用 `QgsPrintLayout` + `QgsLayoutExporter` |
| 地图要素不显示 | 图例、比例尺等元素位置超出页面范围，或被地图主体覆盖 | 使用 `layout.raiseItem()` 提升层级；检查 y 坐标是否小于页面高度 |
| 指北针 SVG 路径未找到 | QGIS 3.40.9 的 SVG 路径变更 | 使用 `apps/qgis-ltr/svg/arrows/NorthArrow_*.svg` 而非已废弃的 `share/svg/north_arrows/` |
| 比例尺不显示 | `QgsLayoutItemScaleBar` 高度为0或未初始化成功 | 确保 `setLinkedMap()` 已调用；`applyDefaultSize()` 后检查尺寸；手动添加 `setNumberFormat()` |
| 图例不显示 | 未添加图例项到布局或未链接地图 | 确保 `layout.addLayoutItem(legend)` + 设置 `setTitle()` |

---

## 出图自检经验（实战踩坑总结）

### 坑1：地图框尺寸控制
**问题**：`setRect()` 后 QGIS 会根据 extent 比例自动调整高度，导致底部要素被挤出页面
**解决**：设置 extent 后**二次调用** `attemptResize()` 固定尺寸
```python
map_item.setExtent(extent)  # QGIS 可能会调整尺寸
map_item.attemptResize(QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters))  # 强制覆盖
```

### 坑2：地图要素 Z-Order（层级）
**问题**：QgsLayoutItemMap 渲染时会覆盖后续添加的布局元素
**解决**：叠加元素后**必须调用** `layout.raiseItem()`
```python
layout.addLayoutItem(legend)
layout.raiseItem(legend)  # 必须！确保图例在地图上方
```

### 坑3：要素位置计算不匹配实际
**问题**：`attemptResize()` 后实际尺寸可能与设定值不符
**解决**：使用 `map_item.rect()` 获取实际尺寸，基于实际值计算后续元素位置
```python
actual_h = map_item.rect().height()
scale_y = map_y + actual_h - inset - 10  # 基于实际高度，而非设定值
```

### 坑4：行政区边界出图框
**问题**：`extent.scale(1.05)` 不够，边界紧贴或超出图框
**解决**：**至少缩放 1.15 倍**，或根据数据范围动态调整
```python
extent.scale(1.15)  # 至少 15% 外扩，确保边界不被截断
```

### 坑5：比例尺单位不规范
**问题**：自动适配单位可能显示 "1.37米" 这种不规整值
**解决**：使用 `applyDefaultSize()` 自动计算规整单位
```python
scalebar.setNumberOfSegmentsLeft(0)  # 只有右侧分段
scalebar.applyDefaultSize()          # 自动选择 10/50/100 等规整数
```

### 坑6：图例不显示/显示不全
**问题**：QgsLayoutItemLegend 未初始化内容
**解决**：需要设置 `setAutoUpdateModel(True)` 或手动刷新
```python
legend.setAutoUpdateModel(True)  # 自动同步工程图层
legend.adjustBoxSize()           # 根据内容自适应尺寸
```

### 坑7：布局元素层级关系
**问题**：多个元素叠加，后添加的可能不显示
**解决**：按以下顺序添加，并提升层级
```python
# 1. 先添加地图主体
layout.addLayoutItem(map_item)
# 2. 添加叠加元素
layout.addLayoutItem(legend); layout.raiseItem(legend)
layout.addLayoutItem(scalebar); layout.raiseItem(scalebar)
layout.addLayoutItem(source); layout.raiseItem(source)
```

### 出图后人工检查要点
1. **五要素完整**：标题、图例、比例尺、指北针、数据源
2. **要素位置**：均不超出页面边界，不与地图内容重叠
3. **地图完整性**：行政区边界无出框，所有图层可见
4. **字体协调**：标题字号适中（A3横版20pt），要素文字清晰（7-8pt）
