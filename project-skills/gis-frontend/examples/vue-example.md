# Vue 3 + Leaflet 集成示例

## 基础地图组件

```vue
<!-- components/GisMap.vue -->
<template>
  <div class="gis-map">
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// 修复 Vite/Webpack 图标路径问题
import iconDefault from 'leaflet/dist/images/marker-icon.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: iconDefault,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [0, -41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const props = defineProps({
  center: {
    type: Array,
    default: () => [39.9042, 116.4074]
  },
  zoom: {
    type: Number,
    default: 10
  },
  markers: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['map-ready', 'map-click']);

const mapContainer = ref(null);
let map = null;

onMounted(() => {
  map = L.map(mapContainer.value, {
    center: props.center,
    zoom: props.zoom,
    zoomControl: true,
    attributionControl: true
  });

  // 添加底图
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // 添加标记
  if (props.markers && props.markers.length > 0) {
    props.markers.forEach(marker => {
      L.marker([marker.lat, marker.lng])
        .addTo(map)
        .bindPopup(marker.popup || '');
    });
  }

  // 地图点击事件
  map.on('click', (e) => {
    emit('map-click', e.latlng);
  });

  emit('map-ready', map);
});

watch(() => props.center, (newCenter) => {
  if (map) {
    map.panTo(newCenter);
  }
}, { deep: true });

watch(() => props.zoom, (newZoom) => {
  if (map) {
    map.setZoom(newZoom);
  }
});

watch(() => props.markers, (newMarkers) => {
  if (map) {
    // 清除旧标记
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });
    
    // 添加新标记
    newMarkers.forEach(marker => {
      L.marker([marker.lat, marker.lng])
        .addTo(map)
        .bindPopup(marker.popup || '');
    });
  }
}, { deep: true });

onBeforeUnmount(() => {
  if (map) {
    map.remove();
    map = null;
  }
});

defineExpose({
  getMap: () => map
});
</script>

<style scoped>
.gis-map {
  width: 100%;
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}
</style>
```

## 使用示例

```vue
<template>
  <div class="page">
    <GisMap
      ref="gisMapRef"
      :center="mapCenter"
      :zoom="12"
      :markers="markers"
      @map-ready="handleMapReady"
      @map-click="handleMapClick"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import GisMap from '@/components/GisMap.vue';

const gisMapRef = ref(null);
let leafletMap = null;

const mapCenter = ref([39.9042, 116.4074]);

const markers = ref([
  { lat: 39.9042, lng: 116.4074, popup: '<b>北京</b><br>首都' },
  { lat: 39.9052, lng: 116.4084, popup: '测试点' }
]);

const handleMapReady = (map) => {
  leafletMap = map;
  console.log('地图已就绪');
};

const handleMapClick = (latlng) => {
  console.log('地图点击:', latlng);
  // 添加点击标记
  markers.value.push({
    lat: latlng.lat,
    lng: latlng.lng,
    popup: '新标记点'
  });
};
</script>
```

## 轨迹绘制组件

```vue
<!-- components/TrackLayer.vue -->
<template>
  <div></div>
</template>

<script setup>
import { watch, onMounted } from 'vue';
import L from 'leaflet';

const props = defineProps({
  map: {
    type: Object,
    required: true
  },
  trackData: {
    type: Array,
    default: () => []
  }
});

let polyline = null;

const drawTrack = () => {
  if (!props.map || !props.trackData.length) return;

  // 清除旧轨迹
  if (polyline) {
    props.map.removeLayer(polyline);
  }

  // 绘制新轨迹
  polyline = L.polyline(props.trackData, {
    color: 'red',
    weight: 3,
    opacity: 0.8
  }).addTo(props.map);

  // 自适应视图
  props.map.fitBounds(polyline.getBounds(), {
    padding: [20, 20]
  });
};

onMounted(() => {
  drawTrack();
});

watch(() => props.trackData, () => {
  drawTrack();
}, { deep: true });

watch(() => props.map, () => {
  drawTrack();
});
</script>
```

## 测量工具 Hook

```javascript
// composables/useMeasure.js
import { ref, onUnmounted } from 'vue';

export function useMeasure(map) {
  const isMeasuring = ref(false);
  const measurePoints = ref([]);
  let measureLine = null;
  let markerGroup = null;
  const totalDistance = ref(0);

  const startMeasure = () => {
    if (!map) return;
    
    isMeasuring.value = true;
    measurePoints.value = [];
    totalDistance.value = 0;
    
    markerGroup = L.layerGroup().addTo(map);
    
    map.on('click', handleMapClick);
  };

  const handleMapClick = (e) => {
    if (!isMeasuring.value) return;

    measurePoints.value.push(e.latlng);

    // 添加点标记
    L.circleMarker(e.latlng, {
      radius: 6,
      color: '#ff3300',
      fillColor: '#ff3300'
    }).addTo(markerGroup);

    if (measurePoints.value.length > 1) {
      if (!measureLine) {
        measureLine = L.polyline(measurePoints.value, {
          color: '#ff3300',
          dashArray: '5, 10',
          weight: 2
        }).addTo(map);
      } else {
        measureLine.setLatLngs(measurePoints.value);
      }

      // 计算距离
      const points = measurePoints.value;
      const segmentDistance = points[points.length - 1].distanceTo(
        points[points.length - 2]
      );
      totalDistance.value += segmentDistance;

      // 添加距离标注
      const midPoint = L.latLng(
        (points[points.length - 1].lat + points[points.length - 2].lat) / 2,
        (points[points.length - 1].lng + points[points.length - 2].lng) / 2
      );
      
      L.tooltip({
        permanent: true,
        direction: 'center',
        className: 'measure-tooltip'
      })
      .setContent(`${segmentDistance.toFixed(2)}米`)
      .setLatLng(midPoint)
      .addTo(markerGroup);
    }
  };

  const stopMeasure = () => {
    isMeasuring.value = false;
    map.off('click', handleMapClick);
    
    if (measureLine) {
      map.removeLayer(measureLine);
      measureLine = null;
    }
    
    if (markerGroup) {
      map.removeLayer(markerGroup);
      markerGroup = null;
    }
    
    measurePoints.value = [];
    totalDistance.value = 0;
  };

  onUnmounted(() => {
    if (isMeasuring.value) {
      stopMeasure();
    }
  });

  return {
    isMeasuring,
    totalDistance,
    startMeasure,
    stopMeasure
  };
}
```

## 使用测量工具

```vue
<template>
  <div>
    <div class="toolbar">
      <button @click="toggleMeasure">
        {{ isMeasuring ? '停止测量' : '开始测量' }}
      </button>
      <span v-if="totalDistance > 0">
        总距离：{{ totalDistance.toFixed(2) }}米
      </span>
    </div>
    <GisMap ref="gisMapRef" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import GisMap from '@/components/GisMap.vue';
import { useMeasure } from '@/composables/useMeasure';

const gisMapRef = ref(null);
const leafletMap = ref(null);

const handleMapReady = (map) => {
  leafletMap.value = map;
};

const {
  isMeasuring,
  totalDistance,
  startMeasure,
  stopMeasure
} = useMeasure(leafletMap);

const toggleMeasure = () => {
  if (isMeasuring.value) {
    stopMeasure();
  } else {
    startMeasure();
  }
};
</script>
```
