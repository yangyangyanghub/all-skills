# GIS Frontend Skill

GIS（地理信息系统）行业前端开发技能 - 专注于地图集成和地理数据可视化。

## 功能特性

### ✅ 已实现

- **Leaflet 地图集成**
  - 基础地图初始化
  - Marker 标注（单点、批量）
  - Popup 信息窗
  - GeoJSON 数据加载
  - 折线（轨迹）、多边形绘制

- **交互功能**
  - 测距工具（点击测量距离）
  - 地图事件处理（点击、移动、缩放）
  - 图层控制

- **框架支持**
  - 原生 HTML/JS
  - Vue 3 + Vite
  - React（参考 SKILL.md 示例）

- **实用工具**
  - 快速启动脚本
  - 示例代码库
  - 测试用例

### 🚧 计划扩展（Phase 2/3）

- Mapbox GL JS 集成
- 百度/高德地图（国内项目）
- 热力图、标记聚合
- 路径规划
- 坐标转换工具
- Cesium 3D 地球

## 快速开始

### 方式 1：使用技能创建页面

在与 AI 对话时，直接描述你的需求，例如：

```
帮我做一个地图页面，显示北京五环内的地图，添加 5 个地铁站的标注
```

AI 会自动使用此技能生成完整代码。

### 方式 2：使用启动脚本

```bash
cd gis-frontend
node scripts/create-leaflet-page.js ./my-project
```

生成一个包含测距功能的 Leaflet 地图页面。

### 方式 3：复制示例代码

从 `SKILL.md` 或 `examples/` 目录复制代码模板，根据需求修改。

## 目录结构

```
gis-frontend/
├── SKILL.md              # 技能核心指令
├── evals/
│   └── evals.json       # 测试用例定义
├── examples/
│   ├── vue-example.md   # Vue 集成示例
│   └── sample-provinces.geojson  # 示例 GeoJSON 数据
├── references/
│   └── leaflet-basics.md  # Leaflet 基础 API 参考
├── scripts/
│   └── create-leaflet-page.js  # 快速启动脚本
└── README.md            # 本文件
```

## 测试用例

当前包含 4 个测试用例：

1. **基础地图集成 - 原生 HTML**：显示北京地图 + 地铁站标注
2. **轨迹展示 - Vue 组件**：快递员配送轨迹
3. **测量工具 - 测距功能**：点击测量距离
4. **GeoJSON 区域展示**：省份边界数据加载

运行测试（待完善）：

```bash
# 测试技能效果
node scripts/test-skill.js eval-1
```

## 使用场景

### 典型业务场景

| 场景 | 功能 | 推荐方案 |
|------|------|---------|
| 物流轨迹展示 | 折线绘制、自适应视图 | Leaflet + polyline |
| 站点标注管理 | 批量 Marker、自定义图标 | Leaflet + markercluster |
| 配送区域划分 | 多边形绘制、面积计算 | Leaflet.Draw |
| 实时位置监控 | 定时更新 Marker 位置 | WebSocket + map.panTo |
| 数据统计展示 | 热力图、分级设色 | leaflet.heat / choropleth |

### 坐标系说明

- **WGS84**：国际标准，Leaflet/Mapbox 使用
- **GCJ-02**：国测局标准，高德/腾讯地图使用
- **BD-09**：百度地图使用

**注意**：在国内项目中使用 Leaflet 时，如果使用高德/百度数据，需要进行坐标转换。推荐库：`coordtransform`

```bash
npm install coordtransform
```

```javascript
import { wgs2gcj, gcj2bd } from 'coordtransform';
```

## 开发建议

### 性能优化

1. **大量标记点**：使用 `Leaflet.markercluster` 聚合
2. **复杂图形**：使用 Canvas 渲染 `L.canvas()`
3. **瓦片加载**：使用多个子域名 `subdomains: 'abcd'`
4. **视口外数据**：根据 `map.getBounds()` 过滤数据

### 代码组织

- 地图实例单例管理
- 图层分类（底图、业务图层、临时图层）
- 事件监听及时清理（避免内存泄漏）
- 组件化封装（Vue/React）

## 常见问题

### Q: Marker 图标不显示？
**A**：Webpack/Vite 打包时路径问题，参考 `SKILL.md` 中的修复方案。

### Q: 如何自定义底图？
**A**：参考 `references/leaflet-basics.md` 中的底图源列表。

### Q: 如何实现地图联动？
**A**：使用 `map.on('moveend', ...)` 同步多个地图的中心点和缩放级别。

## 参考资料

- [Leaflet 官方文档](https://leafletjs.com/)
- [Leaflet GitHub](https://github.com/Leaflet/Leaflet)
- [Awesome Leaflet](https://github.com/Leaflet/Leaflet/blob/master/PLUGINS.md)
- [GeoJSON 规范](https://geojson.org/)

## 许可证

MIT License
