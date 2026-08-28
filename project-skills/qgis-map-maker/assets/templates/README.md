# QGIS 地图制图师

基于 PyQGIS 引擎的自动化地图制图技能。

## 快速开始

```bash
# 第一步：查看数据
& "C:\Program Files\QGIS 3.40.9\bin\python-qgis-ltr.bat" .opencode/skill/qgis-map-maker/scripts/inspect_data.py --data "<你的Shapefile目录>"

# 第二步：一键制图（用水系模板）
& "C:\Program Files\QGIS 3.40.9\bin\python-qgis-ltr.bat" .opencode/skill/qgis-map-maker/scripts/map_engine.py \
  --data "<数据目录>" \
  --layers "行政区划,道路,水体,城市" \
  --template water \
  --dpi 300
```

## 可用模板（14种）

### 基础类
| 模板 | 说明 |
|------|------|
| `water`     | 🌊 水系地图（蓝调） |
| `admin`     | 🏛️ 行政区划（政务典雅） |
| `transport` | 🛣️ 交通路网（灰调） |
| `minimal`   | ⚡ 极简黑白（论文插图） |

### 自然地理类
| 模板 | 说明 |
|------|------|
| `landuse`     | 🌾 土地利用图 |
| `geology`     | 🪨 地质图 |
| `vegetation`  | 🌿 植被覆盖图 |

### 人文经济类
| 模板 | 说明 |
|------|------|
| `population`  | 👥 人口分布图 |
| `economy`     | 📊 经济分布图 |

### 规划工程类
| 模板 | 说明 |
|------|------|
| `planning`    | 📐 空间规划图 |
| `environment` | 🌍 环境评价图 |

### 特殊用途
| 模板 | 说明 |
|------|------|
| `heatmap`   | 🔥 热力专题图 |
| `military`  | ⚔️ 军事地形图 |
| `nautical`  | ⛵ 航海图 |
