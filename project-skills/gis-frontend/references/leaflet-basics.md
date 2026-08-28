# Leaflet 地图库参考

## 快速开始

### 1. 基础初始化

```javascript
// 创建地图实例
const map = L.map('map', {
  center: [39.9042, 116.4074], // 中心点 [纬度，经度]
  zoom: 10, // 初始缩放级别
  zoomControl: true, // 显示缩放控制
  attributionControl: true // 显示版权信息
});

// 添加瓦片图层（底图）
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);
```

### 2. 常用底图源

```javascript
// OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OSM'
});

// Satellite (Esri)
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: '© Esri'
});

// 高德地图（需自行转换瓦片）
L.tileLayer('https://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}', {
  maxZoom: 18,
  attribution: '© 高德地图'
});
```

### 3. Marker 标记

```javascript
// 基础标记
L.marker([lat, lng]).addTo(map);

// 自定义图标
const customIcon = L.icon({
  iconUrl: 'path/to/icon.png',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

L.marker([lat, lng], { icon: customIcon }).addTo(map);

// 带 Popup 的标记
L.marker([lat, lng])
  .addTo(map)
  .bindPopup('<b>标题</b><br>内容')
  .openPopup();

// 标记事件
const marker = L.marker([lat, lng]).addTo(map);
marker.on('click', () => {
  console.log('Marker clicked');
});
```

### 4. 矢量图形

```javascript
// 折线（轨迹）
L.polyline([
  [lat1, lng1],
  [lat2, lng2],
  [lat3, lng3]
], {
  color: 'red',
  weight: 3,
  opacity: 0.8,
  dashArray: '10, 10' // 虚线
}).addTo(map);

// 多边形
L.polygon([
  [lat1, lng1],
  [lat2, lng2],
  [lat3, lng3],
  [lat4, lng4]
], {
  color: 'blue',
  fillColor: '#3388ff',
  fillOpacity: 0.2
}).addTo(map);

// 圆形
L.circle([lat, lng], {
  radius: 100, // 半径（米）
  color: 'red',
  fillColor: '#f03',
  fillOpacity: 0.3
}).addTo(map);

// 矩形
L.rectangle([[lat1, lng1], [lat2, lng2]], {
  color: '#ff7800',
  weight: 2
}).addTo(map);
```

### 5. GeoJSON

```javascript
// 加载 GeoJSON
const geojsonFeature = {
  "type": "Feature",
  "properties": {
    "name": "Foo",
    "population": 1000
  },
  "geometry": {
    "type": "Point",
    "coordinates": [116.4074, 39.9042]
  }
};

L.geoJSON(geojsonFeature, {
  // 自定义样式
  style: (feature) => {
    switch (feature.geometry.type) {
      case 'LineString':
        return { color: '#ff3300', weight: 3 };
      case 'Polygon':
        return { color: '#0033ff', fillOpacity: 0.3 };
      default:
        return {};
    }
  },
  
  // 自定义 Marker
  pointToLayer: (feature, latlng) => {
    return L.circleMarker(latlng, {
      radius: 8,
      color: '#3388ff'
    });
  },
  
  // 每个要素的弹窗
  onEachFeature: (feature, layer) => {
    let popup = '';
    for (const key in feature.properties) {
      popup += `<b>${key}:</b> ${feature.properties[key]}<br>`;
    }
    layer.bindPopup(popup);
  }
}).addTo(map);

// 从 URL 加载
fetch('data/regions.geojson')
  .then(res => res.json())
  .then(data => {
    L.geoJSON(data).addTo(map);
  });
```

### 6. 地图事件

```javascript
// 点击地图
map.on('click', (e) => {
  console.log('坐标:', e.latlng);
});

// 移动地图
map.on('moveend', () => {
  console.log('中心点:', map.getCenter());
  console.log('缩放:', map.getZoom());
});

// 缩放变化
map.on('zoomend', () => {
  console.log('当前缩放:', map.getZoom());
});

// 移除事件监听
const handler = (e) => console.log(e);
map.on('click', handler);
map.off('click', handler);
```

### 7. 地图控制

```javascript
// 飞行动画到指定位置
map.flyTo([newLat, newLng], newZoom, {
  duration: 2
});

// 适应边界
const bounds = L.latLngBounds([
  [lat1, lng1],
  [lat2, lng2]
]);
map.fitBounds(bounds, {
  padding: [50, 50]
});

// 获取当前视图
const center = map.getCenter();
const zoom = map.getZoom();
const bounds = map.getBounds();

// 设置最大/最小缩放
const map = L.map('map', {
  minZoom: 3,
  maxZoom: 18
});
```

## 常用插件使用

### Leaflet.Draw（绘制工具）

```javascript
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';

// 初始化绘制控制
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const drawControl = new L.Control.Draw({
  draw: {
    polyline: true,
    polygon: {
      allowIntersection: false,
      showArea: true
    },
    circle: false,
    rectangle: true,
    marker: true,
    circlemarker: false
  },
  edit: {
    featureGroup: drawnItems
  }
});
map.addControl(drawControl);

// 监听创建事件
map.on(L.Draw.Event.CREATED, (e) => {
  const layer = e.layer;
  drawnItems.addLayer(layer);
  
  // 获取 GeoJSON
  const geojson = layer.toGeoJSON();
  console.log(geojson);
});
```

### Leaflet.markercluster（标记聚合）

```javascript
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

// 创建聚合组
const markers = L.markerClusterGroup();

// 添加大量标记
for (let i = 0; i < 1000; i++) {
  const lat = baseLat + (Math.random() - 0.5) * 0.1;
  const lng = baseLng + (Math.random() - 0.5) * 0.1;
  markers.addLayer(L.marker([lat, lng]));
}

map.addLayer(markers);

// 添加单个标记并刷新
markers.addLayer(L.marker([lat, lng]));
markers.refreshClusters();
```

### Leaflet.heat（热力图）

```javascript
import 'leaflet.heat';

// 热力图数据格式：[[lat, lng, intensity], ...]
const heatData = [
  [39.9, 116.4, 0.5],
  [39.91, 116.41, 0.8],
  [39.92, 116.42, 1.0]
];

L.heatLayer(heatData, {
  radius: 25,
  blur: 15,
  maxZoom: 10,
  gradient: {
    0.4: 'blue',
    0.6: 'lime',
    0.8: 'red'
  }
}).addTo(map);
```

## 性能优化

### 1. 大量标记点
- 使用 `markercluster` 聚合
- 使用 Canvas 渲染代替 SVG
- 视口内渲染（只渲染可见区域）

```javascript
// Canvas 渲染
L.circle(latlng, {
  radius: 10,
  renderer: L.canvas()
});
```

### 2. 图层管理

```javascript
// 创建图层控制
const baseMaps = {
  "街道图": streetLayer,
  "卫星图": satelliteLayer
};

const overlayMaps = {
  "标记点": markerLayer,
  "轨迹线": polylineLayer
};

L.control.layers(baseMaps, overlayMaps).addTo(map);
```

### 3. 栅格化瓦片

对于大规模数据，考虑使用矢量切片或后端栅格化。
