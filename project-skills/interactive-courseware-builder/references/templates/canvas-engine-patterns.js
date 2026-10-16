// Canvas Engine Patterns — Canvas绘制规范与防坑模板
// 这些规范从多轮课件迭代中提炼，防止最常见的Canvas bug

// ===== 核心规范 =====

// 规范1: 变量声明 — 共享数据必须在模块（script）顶层声明，不能在函数内部
// ❌ 错误: function drawA() { var peaks = [...]; } // drawB无法访问peaks
// ✅ 正确: var peaks = [...]; // 模块顶层，drawA和drawB都能访问
// 示例:
//   var waterPeaks = [{cx:0.35, h:480, w:0.18}, {cx:0.65, h:350, w:0.2}];

// 规范2: 防重复绘制 — 用diagramDrawn对象记录已绘制的Canvas
var diagramDrawn = {};
function drawDiagramP2() {
  var c = document.getElementById('diagramP2');
  if (!c || diagramDrawn.p2) return; // 已绘制或Canvas不存在 → 跳过
  diagramDrawn.p2 = true;
  // 绘制逻辑...
}

// 规范3: Canvas函数签名 — 统一使用(ctx, W, H, state)参数传递状态
// ❌ 错误: 依赖全局变量散落各处
// ✅ 正确: function drawXSection(ctx, W, H, waterH) { ... }
// 状态对象模式:
//   var simState = { waterH: 250, angle: -0.6 };
//   function render(ctx, W, H, state) { /* 使用state.waterH, state.angle */ }

// 规范4: 颜色值 — Canvas必须使用hex字符串，不能用CSS变量
// ❌ 错误: ctx.fillStyle = 'var(--primary)'; // Canvas不支持CSS变量
// ✅ 正确: ctx.fillStyle = '#8D6E63'; // 直接用hex值
// 对应关系: --primary → '#8D6E63', --accent → '#FF8F00', --ink → '#3E2723' 等

// 规范5: Canvas坐标 — 鼠标/触摸坐标必须用getBoundingClientRect校准
function getCanvasCoords(canvas, e) {
  var rect = canvas.getBoundingClientRect();
  var clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
  var clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
  var scaleX = canvas.width / rect.width;
  var scaleY = canvas.height / rect.height;
  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY
  };
}

// 规范6: Math.max下限 — 防止零值和负值导致绘制异常
// ❌ 错误: var r = Math.sqrt(something); // something可能为0或负
// ✅ 正确: var r = Math.sqrt(Math.max(0.001, something));
// 特例: radius计算中Math.max(0.5, elev) 而非 Math.max(1, elev) — 防止阈值过粗

// ===== 3D地形投影模板 =====
// ⚠ 这是等高线课件的领域特定示例。通用项目中需要替换 terrainFunc 和 elevColor
// 保留的结构模式（可用于任何 3D 投影场景）:
//   1. 构建网格 → 2. 旋转投影 → 3. 从远到近填充面片 → 4. 颜色映射
// 替换要点: terrainFunc() → 你的地形/函数; elevColor() → 你的颜色映射
function draw3DProjection(canvas, terrainFunc, angle, tilt) {
  var ctx = canvas.getContext('2d');
  var W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  var cx = W / 2, cy = H / 2 + 15, scale = 360;
  var cosA = Math.cos(angle), sinA = Math.sin(angle);
  var cosT = Math.cos(tilt), sinT = Math.sin(tilt);

  // 构建网格
  var grid = 40, pts = [];
  for (var iz = 0; iz <= grid; iz++) {
    var z = -0.7 + (iz / grid) * 1.4;
    var row = [];
    for (var ix = 0; ix <= grid; ix++) {
      var x = -0.7 + (ix / grid) * 1.4;
      var hVal = terrainFunc(x, z);
      var rx = x * cosA - z * sinA;
      var rz = x * sinA + z * cosA;
      var sx = cx + rx * scale;
      var sy = cy - hVal * 0.55 * cosT - rz * scale * 0.4 * sinT;
      row.push({ sx: sx, sy: sy, h: hVal });
    }
    pts.push(row);
  }

  // 填充面片（从远到近）
  for (var iz = 0; iz < grid; iz++) {
    for (var ix = 0; ix < grid; ix++) {
      var p00 = pts[iz][ix], p10 = pts[iz][ix+1];
      var p01 = pts[iz+1][ix], p11 = pts[iz+1][ix+1];
      var avgH = (p00.h + p10.h + p01.h + p11.h) / 4;
      ctx.fillStyle = elevColor(avgH);
      ctx.strokeStyle = 'rgba(0,0,0,0.06)'; ctx.lineWidth = 0.3;
      ctx.beginPath();
      ctx.moveTo(p00.sx, p00.sy); ctx.lineTo(p10.sx, p10.sy);
      ctx.lineTo(p11.sx, p11.sy); ctx.lineTo(p01.sx, p01.sy);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
  }
}

// ===== 高程颜色映射模板 =====
// ⚠ 等高线课件领域特定 — 绿→黄→棕→白的高度色带
// 通用项目中需替换为你自己的颜色映射逻辑
// 保留的模式: 用 t (0→1) 分段插值 RGB
function elevColor(h, maxH) {
  var t = Math.min(1, Math.max(0, h / (maxH || 450)));
  if (t < 0.2) { var s = t/0.2; return 'rgb('+Math.floor(180+40*s)+','+Math.floor(220-30*s)+','+Math.floor(140-40*s)+')'; }
  else if (t < 0.5) { var s = (t-0.2)/0.3; return 'rgb('+Math.floor(220-40*s)+','+Math.floor(190-40*s)+','+Math.floor(100-20*s)+')'; }
  else if (t < 0.8) { var s = (t-0.5)/0.3; return 'rgb('+Math.floor(180-40*s)+','+Math.floor(150-30*s)+','+Math.floor(80-10*s)+')'; }
  else { var s = (t-0.8)/0.2; return 'rgb('+Math.floor(140+80*s)+','+Math.floor(120+60*s)+','+Math.floor(70+100*s)+')'; }
}

// ===== 高斯山峰模型 =====
// ⚠ 等高线课件领域特定 — 用于地形高度计算
// 通用项目中可替换为任何参数化曲面函数
// 保留的模式: var dx = x - cx; var dz = z - cz; return h * Math.exp(-d2/(2*sigma*sigma));
function gaussianPeak(cx, cz, h, sigma, x, z) {
  var dx = x - cx, dz = z - cz;
  var d2 = dx * dx + dz * dz;
  return h * Math.exp(-d2 / (sigma * sigma * 2));
}

// ===== 等高线半径计算（2D俯视图） =====
// ⚠ 等高线课件领域特定 — 给定高程计算等高线圆的半径
function contourRadius(peak, elev) {
  if (elev >= peak.h || elev <= 0) return 0;
  var safeElev = Math.max(0.5, elev); // 防止阈值过粗
  if (safeElev >= peak.h) return 0;
  return peak.sigma * Math.sqrt(-2 * Math.log(safeElev / peak.h));
}

// ===== 拖拽旋转事件模板 =====
function setupDragRotation(canvas, stateObj, renderFunc) {
  var dragging = false, lastX = 0, lastY = 0;
  canvas.style.cursor = 'grab';

  canvas.addEventListener('mousedown', function(e) {
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    canvas.style.cursor = 'grabbing'; e.preventDefault();
  });
  canvas.addEventListener('mousemove', function(e) {
    if (!dragging) return;
    stateObj.angle += (e.clientX - lastX) * 0.008;
    stateObj.tilt += (e.clientY - lastY) * 0.008;
    stateObj.tilt = Math.max(-0.6, Math.min(1.0, stateObj.tilt));
    lastX = e.clientX; lastY = e.clientY;
    renderFunc(); e.preventDefault();
  });
  canvas.addEventListener('mouseup', function() { dragging = false; canvas.style.cursor = 'grab'; });
  canvas.addEventListener('mouseleave', function() { dragging = false; canvas.style.cursor = 'grab'; });

  // 触摸事件
  canvas.addEventListener('touchstart', function(e) {
    dragging = true; lastX = e.touches[0].clientX; lastY = e.touches[0].clientY;
    e.preventDefault();
  }, { passive: false });
  canvas.addEventListener('touchmove', function(e) {
    if (!dragging) return;
    stateObj.angle += (e.touches[0].clientX - lastX) * 0.008;
    stateObj.tilt += (e.touches[0].clientY - lastY) * 0.008;
    stateObj.tilt = Math.max(-0.6, Math.min(1.0, stateObj.tilt));
    lastX = e.touches[0].clientX; lastY = e.touches[0].clientY;
    renderFunc(); e.preventDefault();
  }, { passive: false });
  canvas.addEventListener('touchend', function() { dragging = false; });
}

// ===== onPageEnter与Canvas三要素同步规则 =====
// Canvas三要素必须同步：① HTML中<canvas id="xxx"> ② JS中drawXxx()函数 ③ onPageEnter中调用
// 任何修改都必须检查三者是否仍然对齐
// ❌ 错误: 删除了drawXxx()函数体但保留onPageEnter调用 → 空白页
// ❌ 错误: 修改了canvas的id但忘记更新getElementById → null错误
// ✅ 正确: 每次修改Canvas后，验证三者: canvas id → draw函数名 → onPageEnter调用

// ===== 共享绘图工具函数模式 =====
// ⚠ 重要教训：绘图工具函数（drawArrow, drawLabel, drawDashedLine 等）
//   是跨多个Canvas页面的共享资源，绝不能在编辑某个页面时误删！
//
// 规范:
//   1. 共享绘图函数放在 <script> 顶层（所有Canvas页面的drawXxx()都能调用）
//   2. 不要在某个页面的drawXxx()函数内部重定义共享函数
//   3. 编辑后验证: grep "function drawArrow\|function drawLabel\|function drawDashedLine"
//      确保所有共享函数仍然存在
//   4. 绝不批量删除Canvas函数 — 逐个移除，每次移除后验证

// 通用绘图工具函数示例（可直接复制到项目 <script> 中）:

// drawArrow — 画带箭头的线段（物理/化学/流程图通用）
function drawArrow(ctx, fromX, fromY, toX, toY, color, lineWidth, headLen) {
  var dx = toX - fromX, dy = toY - fromY;
  var angle = Math.atan2(dy, dx);
  var len = Math.max(headLen || 10, 5); // Math.max 防零值
  ctx.save();
  ctx.strokeStyle = color || '#333';
  ctx.lineWidth = lineWidth || 2;
  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.lineTo(toX, toY);
  ctx.stroke();
  ctx.fillStyle = color || '#333';
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - len * Math.cos(angle - Math.PI/6), toY - len * Math.sin(angle - Math.PI/6));
  ctx.lineTo(toX - len * Math.cos(angle + Math.PI/6), toY - len * Math.sin(angle + Math.PI/6));
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// drawLabel — 在Canvas上写文字标签（通用）
function drawLabel(ctx, text, x, y, color, fontSize, align) {
  ctx.save();
  ctx.fillStyle = color || '#333';
  ctx.font = (fontSize || 16) + 'px "Microsoft YaHei", sans-serif';
  ctx.textAlign = align || 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x, y);
  ctx.restore();
}

// drawDashedLine — 虚线（通用，用于回路标注、参考线等）
function drawDashedLine(ctx, x1, y1, x2, y2, color, lineWidth, dashPattern) {
  ctx.save();
  ctx.strokeStyle = color || '#999';
  ctx.lineWidth = lineWidth || 1;
  ctx.setLineDash(dashPattern || [6, 4]);
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
}
