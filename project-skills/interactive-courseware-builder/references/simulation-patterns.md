# Simulation Patterns

Five reusable simulation types for interactive courseware. Choose based on the
concept you need to visualize.

> 以下各模式的示例覆盖不同学科，仅作示意——实际使用时替换为你的学科概念与数据。

⚠ **代码规范**: 所有仿真代码使用 function-based JavaScript（不用 ES6 class/箭头函数），
确保在单文件 HTML 中无需构建工具即可运行。

---

## 1. Parameter Slider

**Use when**: Exploring how changing one variable affects the system (e.g.
physical laws, mathematical relationships).

**Implementation**:
```js
// HTML: <input type="range" min="0" max="100" value="50" oninput="update()">
// On change: setParam('variable', value) → render()

var simParams = { variable: 50 }; // 模块顶层声明，所有函数可访问

function setParam(key, value) {
  simParams[key] = Math.max(0, Math.min(100, value)); // clamp防溢出
  render();
}

function render() {
  var c = document.getElementById('simCanvas');
  var ctx = c.getContext('2d');
  var W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);
  // 根据 simParams 重绘 Canvas...
}
```

**UI elements**: Slider + value display + reset button + status text.

**Example**: 欧姆定律仿真 — 拖动电压/电阻滑块，观察电流实时变化（物理）。

---

## 2. Drag & Match

**Use when**: Classification, sorting, pairing, or structural assembly tasks.

**Implementation**:
> ⚠ 交互实现**统一用 Pointer Events**（`pointerdown/move/up` + `touch-action:none`，见 SKILL.md §1.3.2 硬规则与
> `matching-quiz.js` 的 `initClassification()` 权威实现）——下方 mousedown 代码**仅为逻辑示意**，禁止直接照抄
> （只响应鼠标的 mousedown 是"假交互"，手机触屏不可用）。

```js
// Track element drag: pointerdown → pointermove → pointerup（示意：用 Pointer Events 替代 mousedown）
// On drop: check collision with target → set class .correct or .wrong
// Touch: touch-action:none + document 级 move/up 监听（见 matching-quiz.js）

var dragging = null, offsetX = 0, offsetY = 0;

element.addEventListener('mousedown', function(e) {
  dragging = element; offsetX = e.clientX - element.offsetLeft; offsetY = ...;
});
document.addEventListener('mousemove', function(e) {
  if (dragging) { dragging.style.left = (e.clientX - offsetX) + 'px'; ... }
});
document.addEventListener('mouseup', function(e) {
  if (dragging) { /* check collision with drop targets */ dragging = null; }
});
```

**UI elements**: Draggable cards + drop zones + match feedback (correct/wrong
highlight).

**Example**: 把化学元素卡片拖到对应的分类区（金属 / 非金属 / 稀有气体）。

---

## 3. Process Demo

**Use when**: Showing a time-sequenced process or mechanism (e.g. historical
events, biological processes, reaction mechanisms).

**Implementation**:
```js
var phase = 0, totalPhases = 4;
var animFrame = null;

function play() {
  phase++;
  if (phase >= totalPhases) { phase = 0; cancelAnimationFrame(animFrame); return; }
  renderPhase(phase);
  animFrame = requestAnimationFrame(function() { setTimeout(play, 2000); });
}
```

**UI elements**: Play/pause button + phase indicator + timeline scrubber.

**Example**: 有丝分裂各阶段的分步演示（生物）。

---

## 4. Compare Switch

**Use when**: Students need to compare A vs B side by side with synchronized
controls.

**Implementation**:
```js
// Dual Canvas or split-view DOM
// Shared parameter state → both views update simultaneously

function render() {
  drawViewA(canvasA, simParams);
  drawViewB(canvasB, simParams);
}
```

**UI elements**: Two views with shared control panel + `<select>` for scenarios.

**Example**: 两个函数图像并排对比（如 y=sin x 与 y=cos x），同步缩放/平移（数学）。

---

## 5. Build & Construct

**Use when**: Knowledge is assembled from parts into a whole (e.g. geometric
constructions, system architectures, hierarchical structures).

**Implementation**:
```js
// Click to add element → element appears at click position
// Elements can be connected with lines
// Real-time display of cumulative parameters

var elements = [];
canvas.addEventListener('click', function(e) {
  var coords = getCanvasCoords(canvas, e); // canvas-engine-patterns.js 的坐标校准函数
  elements.push({ x: coords.x, y: coords.y, type: currentTool });
  redraw();
});
```

**UI elements**: Tool selector + click-to-place + parameter display + undo
button.

**Example**: 搭建分子结构——点击放置原子、自动连键、实时显示分子式（化学）。

---

## Common Integration Pattern

All simulations share the same integration pattern into courseware:

```js
// 1. 模块顶层声明仿真状态
var simState = { param1: 50, param2: 0 };

// 2. drawXxx() 函数 — 使用 diagramDrawn guard 防止重复绘制
function drawXxx() {
  var c = document.getElementById('canvasXxx');
  if (!c || diagramDrawn.xxx) return;
  diagramDrawn.xxx = true;
  var ctx = c.getContext('2d');
  // ... 绘制逻辑，使用 simState 参数 ...
}

// 3. onPageEnter 回调 — 懒初始化
function onPageEnter(i) {
  var id = PAGE_IDS[i];
  if (id === 'p3') drawXxx();
  // Step 4: if (id === 'p3') document.querySelector('#p3 .qr-badge').classList.add('on');
}

// 4. slider oninput — 调用 setParam → render
// <input type="range" oninput="setParam('param1', parseInt(this.value)); render();">
```
