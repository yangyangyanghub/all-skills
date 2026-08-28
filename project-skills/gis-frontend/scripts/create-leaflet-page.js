#!/usr/bin/env node

/**
 * GIS 前端技能 - Leaflet 快速启动脚本
 * 用于快速创建 Leaflet 地图页面模板
 */

const fs = require('fs');
const path = require('path');

const HTML_TEMPLATE = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Leaflet 地图页面</title>
  
  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""/>
  
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    #map {
      height: 100vh;
      width: 100%;
    }
    
    .toolbar {
      position: absolute;
      top: 10px;
      left: 50px;
      z-index: 1000;
      background: white;
      padding: 10px;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .toolbar button {
      padding: 8px 16px;
      margin-right: 8px;
      background: #0078A8;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .toolbar button:hover {
      background: #005a82;
    }
    
    .toolbar button.active {
      background: #005a82;
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .distance-display {
      margin-top: 10px;
      font-weight: bold;
      color: #333;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  
  <div class="toolbar">
    <button id="btnMeasure">📏 测距</button>
    <button id="btnClear">🗑️ 清除</button>
    <div class="distance-display" id="distanceDisplay">总距离：0 米</div>
  </div>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""></script>
  
  <script>
    // ==================== 初始化地图 ====================
    const map = L.map('map', {
      center: [39.9042, 116.4074], // 北京
      zoom: 10,
      zoomControl: false
    });

    // 添加缩放控制到右下角
    L.control.zoom({
      position: 'bottomright'
    }).addTo(map);

    // 添加底图
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // ==================== 测距功能 ====================
    let isMeasuring = false;
    let measurePoints = [];
    let measureLine = null;
    let markerGroup = L.layerGroup();
    let totalDistance = 0;

    const btnMeasure = document.getElementById('btnMeasure');
    const btnClear = document.getElementById('btnClear');
    const distanceDisplay = document.getElementById('distanceDisplay');

    btnMeasure.addEventListener('click', () => {
      isMeasuring = !isMeasuring;
      btnMeasure.classList.toggle('active', isMeasuring);
      btnMeasure.textContent = isMeasuring ? '✅ 测距中' : '📏 测距';
      
      if (!isMeasuring) {
        stopMeasure();
      }
    });

    btnClear.addEventListener('click', () => {
      stopMeasure();
      markerGroup.clearLayers();
      if (measureLine) {
        map.removeLayer(measureLine);
        measureLine = null;
      }
      measurePoints = [];
      totalDistance = 0;
      distanceDisplay.textContent = '总距离：0 米';
    });

    function stopMeasure() {
      isMeasuring = false;
      btnMeasure.classList.remove('active');
      btnMeasure.textContent = '📏 测距';
    }

    map.on('click', (e) => {
      if (!isMeasuring) return;

      const latlng = e.latlng;
      measurePoints.push(latlng);

      // 添加点标记
      L.circleMarker(latlng, {
        radius: 6,
        color: '#ff3300',
        fillColor: '#ff3300',
        fillColor: '#fff'
      }).addTo(markerGroup);

      if (measurePoints.length > 1) {
        // 绘制线段
        if (!measureLine) {
          measureLine = L.polyline(measurePoints, {
            color: '#ff3300',
            dashArray: '5, 10',
            weight: 2
          }).addTo(map);
        } else {
          measureLine.setLatLngs(measurePoints);
        }

        // 计算距离
        const points = measurePoints;
        const segmentDistance = points[points.length - 1].distanceTo(
          points[points.length - 2]
        );
        totalDistance += segmentDistance;
        distanceDisplay.textContent = \`总距离：\${totalDistance.toFixed(2)} 米\`;

        // 添加距离标注
        const midPoint = L.latLng(
          (points[points.length - 1].lat + points[points.length - 2].lat) / 2,
          (points[points.length - 1].lng + points[points.length - 2].lng) / 2
        );
        
        L.tooltip({
          permanent: true,
          direction: 'top',
          className: 'measure-tooltip'
        })
        .setContent(\`\${segmentDistance.toFixed(2)} 米\`)
        .setLatLng(midPoint)
        .addTo(markerGroup);
      }
    });

    // ==================== 示例：添加标注点 ====================
    const stations = [
      { lat: 39.9042, lng: 116.4074, name: '西直门' },
      { lat: 39.9542, lng: 116.4074, name: '天通苑' },
      { lat: 39.8542, lng: 116.4074, name: '宋家庄' },
      { lat: 39.9042, lng: 116.3074, name: '西二旗' },
      { lat: 39.9042, lng: 116.5074, name: '东直门' }
    ];

    stations.forEach(station => {
      L.marker([station.lat, station.lng])
        .addTo(map)
        .bindPopup(\`<b>\${station.name}</b>\`);
    });

    console.log('地图已初始化完成！');
    console.log('点击"测距"按钮开始在地图上测量距离');
  </script>
</body>
</html>
`;

// 执行脚本
if (require.main === module) {
  const args = process.argv.slice(2);
  const outputDir = args[0] || '.';
  const outputFile = args[1] || 'leaflet-map.html';
  const outputPath = path.join(outputDir, outputFile);

  fs.writeFileSync(outputPath, HTML_TEMPLATE, 'utf-8');
  console.log(\`✅ Leaflet 地图页面已创建：\${outputPath}\`);
  console.log(\`📌 使用方式：在浏览器中打开此文件即可运行\\n\`);
}

module.exports = { HTML_TEMPLATE };
