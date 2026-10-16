# Content Animation Rules — 内容进入动画规则

> **用途**：Step 3 编写讲授页动画前必读。逐页面类型的动画模式决策 + `setupReveal` 使用规范 + 代码模板。
> 加载即生效，不用再到 SKILL.md 长文中搜索。

---

## 1. 分页动画模式决策表

> **总原则**：不同页面类型的交互模型不同，动画模式不可一刀切。

| 页面类型 | 动画模式 | 如何实现 | 原因 |
|----------|:--:|------|------|
| **封面页** (cover) | 不启用揭示 | 不调用 `setupReveal`，内容直接可见 | 封面信息一次性呈现，不需要逐步点击 |
| **讲授页** (teach) | 点击逐段展开 | `setupReveal(pageId, items)` —— 页面进入时全部隐藏，教师每次点击 ▶ 展开一项 | 教师控制讲授节奏 |
| **测验页** (pre/mid/post) | 直接可见 | 不调用 `setupReveal`，所有题目立即可见 | 测验引擎自有交互（选/答/交），不应叠加内容动画 |
| **仿真页** (sim) | 直接可见 | 不调用 `setupReveal`，控件+Canvas 立即可见 | 仿真已有滑块/自动演示等交互，不应叠加内容动画 |
| **总结页** (summary) | 直接可见 | 不调用 `setupReveal`，所有内容立即可见 | 总览信息直接呈现 |

---

## 2. `setupReveal` 调用规范

### 2.1 何时调用

```js
// ✅ 仅在讲授页的 onPageEnter 中调用
if (id === 'p2') setupReveal('p2', [...]);   // 数列定义与通项
if (id === 'p3') setupReveal('p3', [...]);   // 极限直观描述
// ...
```

### 2.2 何时不调用

```js
// ❌ 测验页 —— 不调用
// ❌ 仿真页 —— 不调用
// ❌ 封面页 —— 不调用（内容直接可见）
// ❌ 总结页 —— 不调用
```

### 2.3 标题规则（硬规则）

```
✅ 每个页面的标题行（teach-title / sim-title / summary-title / 封面标题）：页面进入即常驻显示，
   绝不加入 setupReveal 队列，绝不做任何进入动画
❌ 标题出现在 setupReveal 数组中
❌ 标题被 reveal-hidden 隐藏
❌ 标题做进入动画（淡入/上滑/滑入等）
```

> 理由：标题是页面锚点，学生须第一时间知道当前在讲什么，必须立即常驻可见。

---

## 3. `setupReveal` 代码模板

### 3.1 基本用法（讲授页）

```js
// onPageEnter 中（标题 teach-title 不加入队列，进入页面即显示）:
if (id === 'p2') setupReveal('p2', [
  // ⚠ 队列顺序 = 读者阅读顺序（从上到下、从左到右），图片按其版面位置插入
  // 第1步: 第一段正文
  { sel: '#p2s1', anim: 'reveal-fade-up' },
  // 第2步: 夹在段1与段2之间的浮动图（图 + caption 用 reveal-img-group 包裹，作为一步）
  { sel: '.fig.float-r', anim: 'reveal-float-in-r' },
  // 第3步: 第二段正文
  { sel: '#p2s2', anim: 'reveal-fade-up' },
  // 第4步: 关键概念框
  { sel: '.key-box', anim: 'reveal-slide-left' },
  // 第5步: 并列卡片逐张（组内 seqDelay）
  { sel: '.card', anim: 'reveal-card-pop', seqDelay: 150 }
]);
// ⚠ 顺序 = 阅读顺序：图夹在哪两段之间，就排在它们之间；图在全宽段之后，就排该段之后。
//   严禁图先于其说明文字、严禁后置段落提前、严禁时上时下时左时右。
```

### 3.2 动画类型速查

| `anim` 值 | 视觉 | 适用 |
|-----------|------|------|
| `'reveal-fade-up'` | 淡入 + 上滑 20px | 正文段落、卡片、列表项 |
| `'reveal-fade-up-seq'` | 多段落依次淡入上浮 | 多段正文逐段揭示 |
| `'reveal-slide-left'` | 从右滑入 | 高亮框、公式框、关键概念 |
| `'reveal-focus-in'` | 框入聚焦 | Canvas、图片、重点图表 |
| `'reveal-card-pop'` | 卡片弹入 | 并列概念卡片 |
| `'reveal-li-slide'` | 列表逐条滑入 | `<li>` 特征列表 |
| `'reveal-pulse'` | 高亮脉冲 | 核心术语、易错点 |
| `'reveal-sepia'` | 底片显影 | 历史照片、老照片 |

完整 24 种动画目录见 SKILL.md「Progressive Reveal Animation System」章节。

### 3.3 封面页
封面页**不调用 `setupReveal`**，所有内容直接可见（与测验/仿真/总结页一致）。

### 3.4 键盘交互

| 按键 | 行为 |
|------|------|
| **→ / ↓ / Space** | 有隐藏内容 → 展开下一步；全部展开 → 翻到下一页 |
| **← / ↑** | 有已展开内容 → 撤回上一步（`prevReveal`）；第0步 → 翻到上一页 |

---

## 4. 实现检查清单

完成 Step 3 后逐条验证：

- [ ] 每个讲授页在 `onPageEnter` 中调用 `setupReveal`，标题不在队列中（标题页面进入即常驻显示、不做动画）
- [ ] 测验页 / 仿真页 / 总结页 / **封面页**均**未调用** `setupReveal`
- [ ] 揭示队列顺序严格等于**阅读顺序**（第1段→第2段→第3段…），图片按其版面位置插入（夹在两段之间则排在它们之间）
- [ ] 图片与其 caption 用 `<div class="reveal-img-group">` 包裹，作为一步
- [ ] 键盘处理中先检查 `pageRevealActive[pid]` 是否存在（非揭示页为 `undefined`）

---

## 5. 常见坑

| 坑 | 原因 | 修法 |
|----|------|------|
| 讲授页标题消失/标题做动画 | `teach-title` 被加入队列或做了进入动画 | 从队列删除；标题常驻、绝不做任何动画 |
| 动画顺序乱（元素出现顺序 ≠ 阅读顺序） | 队列未按阅读顺序排、图片位置未参与排序 | 重排数组 = 阅读顺序（第1段→第2段→…），图夹两段之间则排其间 |
| 点击页面无反应 | `onPageEnter` 未调用 `setupReveal` | 检查 `pageEntered` 守卫是否阻止 |
| 测验页/仿真页点不动 | 误调用了 `setupReveal` 导致内容隐藏 | 删除对应页面的 `setupReveal` 调用 |
| 键盘箭头报错 | 非揭示页 `pageRevealActive[pid]` 为 `undefined` | 先 `typeof` 检查 |
