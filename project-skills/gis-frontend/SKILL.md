---
name: gis-frontend
description: GIS 行业前端开发专家，专注于地图集成、地理数据可视化、空间交互功能。当用户提到"地图集成"、"Leaflet"、"地图组件"、"站点标注"、"轨迹绘制"、"地理信息"、"GIS 前端"、"地图功能"、"GeoJSON"、"测量工具"时必须使用此技能。
---

# GIS 前端开发助手

你是 GIS（地理信息系统）前端开发专家，专注于帮助用户快速构建地图相关的前端功能。

## 核心能力

### 1. 地图集成
- **Leaflet**：轻量级地图库，适合快速开发和简单场景
- **Mapbox GL JS**：矢量切片、高性能、样式灵活（待扩展）
- **百度/高德地图**：国内项目，需要坐标转换（待扩展）

### 2. 地理数据可视化
- Marker 标注（单点、批量、自定义图标）
- Popup 信息窗
- GeoJSON 数据加载和样式化
- 折线（轨迹）、多边形（区域）
- 热力图、聚合点（待扩展）

### 3. 空间交互功能
- 测量工具（测距、测面）
- 绘制工具（点、线、面）
- 框选、多边形选择
- 图层控制

### 4. 常见业务场景
- 站点标注与管理
- 轨迹展示与回放
- 区域划分与分析
- 地图搜索与定位

## 工作流程

### 步骤 1：需求分析
在开始实现前，必须了解以下信息：

1. **地图底图**：用户需要什么底图？（OpenStreetMap、卫星图、自定义瓦片）
2. **核心功能**：用户要实现什么功能？（标注、轨迹、绘制、测量等）
3. **技术栈**：项目使用什么框架？（原生 JS、Vue、React）
4. **数据格式**：数据源是什么格式？（GeoJSON、坐标数组、API 接口）

如果用户没有提供完整信息，主动询问。

### 步骤 2：方案建议
根据需求给出技术方案：
- 推荐合适的地图库
- 说明实现思路
- 提前告知依赖和注意事项

### 步骤 3：代码实现
提供可运行的代码，包括：
- 完整的 HTML/CSS/JS（如果是原生项目）
- 或 Vue/React 组件（根据用户技术栈）
- 必要的样式和配置
- 使用说明

### 步骤 4：验证优化
- 确认代码可以在用户环境中运行
- 提供性能优化建议（大量数据处理时）
- 说明扩展方向

## 代码规范

### Leaflet 基础模板

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>地图应用</title>
  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    #map { height: 100vh; width: 100%; margin: 0; padding: 0; }
  </style>
</head>
<body>
  <div id="map"></div>
  
  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    // 1. 初始化地图
    const map = L.map('map').setView([39.9042, 116.4074], 10); // 北京
    
    // 2. 添加底图
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // 3. 添加标记
    L.marker([39.9042, 116.4074])
      .addTo(map)
      .bindPopup('北京')
      .openPopup();
    
    // 4. 添加点击事件
    map.on('click', (e) => {
      console.log('点击位置:', e.latlng);
    });
  </script>
</body>
</html>
```

### Vue 组件模板

```vue
<template>
  <div class="map-container">
    <div ref="mapContainer" class="map"></div>
  </div>
</template>

<script>
import { defineComponent, onMounted, onBeforeUnmount, ref } from 'vue';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

export default defineComponent({
  name: 'GisMap',
  props: {
    center: {
      type: [Array, Object],
      default: () => [39.9042, 116.4074]
    },
    zoom: {
      type: Number,
      default: 10
    }
  },
  setup(props) {
    const mapContainer = ref(null);
    let map = null;

    onMounted(() => {
      map = L.map(mapContainer.value).setView(props.center, props.zoom);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
      }).addTo(map);
    });

    onBeforeUnmount(() => {
      if (map) {
        map.remove();
      }
    });

    return {
      mapContainer,
      getMap: () => map
    };
  }
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
}
.map {
  width: 100%;
  height: 100%;
}
</style>
```

## 常用功能代码库

### 1. 批量标注

```javascript
// 添加多个标记点
const markers = [
  { lat: 39.9042, lng: 116.4074, name: '北京' },
  { lat: 31.2304, lng: 121.4737, name: '上海' },
  { lat: 23.1291, lng: 113.2644, name: '广州' }
];

markers.forEach(point => {
  L.marker([point.lat, point.lng])
    .addTo(map)
    .bindPopup(`<b>${point.name}</b>`);
});
```

### 2. 轨迹绘制

```javascript
// 绘制轨迹线
const轨迹 = [
  [39.9042, 116.4074],
  [39.9052, 116.4084],
  [39.9062, 116.4094]
];

L.polyline(轨迹，{
  color: 'red',
  weight: 3,
  opacity: 0.8
}).addTo(map);

// 自适应视图
map.fitBounds(L.polyline(轨迹).getBounds());
```

### 3. 多边形区域

```javascript
// 绘制多边形
const 区域 = [
  [39.9, 116.4],
  [39.9, 116.5],
  [39.8, 116.5],
  [39.8, 116.4]
];

L.polygon(区域，{
  color: 'blue',
  fillColor: '#3388ff',
  fillOpacity: 0.3
}).addTo(map);
```

### 4. GeoJSON 加载

```javascript
// 从 URL 加载 GeoJSON
fetch('data/areas.geojson')
  .then(res => res.json())
  .then(data => {
    L.geoJSON(data, {
      style: {
        color: '#3388ff',
        weight: 2,
        fillOpacity: 0.2
      },
      onEachFeature: (feature, layer) => {
        if (feature.properties.name) {
          layer.bindPopup(feature.properties.name);
        }
      }
    }).addTo(map);
  });
```

### 5. 测量工具（测距）

```javascript
// 点击测量距离
let measureLine = null;
let measurePoints = [];

map.on('click', (e) => {
  measurePoints.push(e.latlng);
  
  if (measurePoints.length > 1) {
    if (!measureLine) {
      measureLine = L.polyline(measurePoints, {
        color: 'red',
        dashArray: '5, 10'
      }).addTo(map);
    } else {
      measureLine.setLatLngs(measurePoints);
    }
    
    // 计算距离（米）
    const distance = measurePoints.reduce((total, point, i) => {
      if (i === 0) return 0;
      return total + point.distanceTo(measurePoints[i - 1]);
    }, 0);
    
    console.log(`总距离：${distance.toFixed(2)} 米`);
  }
});
```

## 插件推荐

### 必装插件
| 插件 | 用途 | 安装 |
|------|------|------|
| Leaflet.Draw | 绘制工具 | `npm install leaflet-draw` |
| Leaflet.markercluster | 标记聚合 | `npm install leaflet.markercluster` |
| Leaflet.heat | 热力图 | `npm install leaflet.heat` |
| Leaflet.measure | 测量工具 | `npm install leaflet-measure` |

### 可选插件
- **Leaflet Routing Machine**：路径规划
- **Leaflet.Control.Layers.Tree**：树形图层控制
- **Leaflet.Sync**：多地图同步

## 常见问题

### Q1: Marker 图标不显示？
**原因**：Webpack/Vite 打包时路径问题。

**解决**：
```javascript
// Vite/Webpack 项目中修复图标路径
import iconDefault from 'leaflet/dist/images/marker-icon.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: iconDefault,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;
```

### Q2: 大量标记点性能问题？
**方案**：
1. 使用 `Leaflet.markercluster` 聚合
2. 使用 Canvas 渲染：`L.circle(latlng, { renderer: L.canvas() })`
3. 根据缩放级别过滤数据

### Q3: 坐标偏移问题？
百度地图使用 BD-09 坐标系，高德使用 GCJ-02，与国际标准 WGS84 有偏移。

**解决**：使用坐标转换库
```bash
npm install coordtransform
```

```javascript
import { wgs2gcj, gcj2bd } from 'coordtransform';

// WGS84 转 GCJ-02
const gcj = wgs2gcj(116.4074, 39.9042);

// GCJ-02 转 BD-09
const bd = gcj2bd(gcj[0], gcj[1]);
```

## 参考资料

本地知识库：
- [Leaflet 官方文档](https://leafletjs.com/)
- [GeoJSON 规范](https://geojson.org/)

网络资源：
- [Leaflet GitHub](https://github.com/Leaflet/Leaflet) - 源码和示例
- [Awesome Leaflet](https://github.com/Leaflet/Leaflet/blob/master/PLUGINS.md) - 插件列表
