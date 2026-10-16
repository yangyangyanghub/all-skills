# Workflow Dev Guide · Step 3 HTML 开发 + 动画/灯箱/总结页（全量细则）

> 由 SKILL.md 外迁。**Step 3 开工前必读**。

---

## Step 3 — HTML Development

**Deliverable**: Single `.html` file，通过质量自检。执行提示：告诉用户「现在开始编写 HTML 课件，从骨架模板复制基础结构，填入 Step 2 确认的内容。」

### 3.1 Start from Skeleton

复制 [`templates/courseware-skeleton.html`](templates/courseware-skeleton.html) 作为起点，已含：全部页面类型 CSS、响应式断点、导航 chip、进度条、页面容器与翻页按钮、配色 `:root` 块（替换为所选方案）。

页面模板：[`templates/page-templates.html`](templates/page-templates.html) 提供每种页面类型完整 HTML（封面/前测/讲授/仿真/中测/后测/总结/知识结构图），直接复制到 `<section>` 改数据，不需从零写。

**What you fill in**: `PAGE_IDS`/`PAGE_LABELS` 数组、`<nav>` chip（正确 data-page 索引与类型 class）、每页 `<section>` 内容、`QUIZZES` 数据、Canvas draw 函数与仿真逻辑、`onPageEnter` 回调。

**分工规则**：
- **复制不改**：page-flip-system.js、quiz-engine.js 核心逻辑（showPage、initQuiz 等）
- **复制+改数据**：QUIZZES、onPageEnter、仿真参数
- **新写**：Canvas draw 函数、每页 HTML content

#### 3.1.1 封面背景图优雅降级（推荐）

不要用单一 `background:url(...)`（404/加载慢时封面破损）。用**三层 background**：

```css
#p0{
  background:
    linear-gradient(135deg, rgba(26,58,92,.72), rgba(13,40,66,.88)), /* 暗化遮罩 */
    url('img/封面主视觉.png'),                                        /* 主视觉图 */
    linear-gradient(135deg, var(--primary), var(--primary-light));    /* 兜底渐变 */
  background-size:cover,cover,cover;
  background-position:center;
}
```

图片 404 时 url 层被浏览器自动跳过，仍显示兜底渐变。遮罩 rgba 用主题色对应 RGB 微调（保证标题白字可读）。

### 3.2 Template Files to Copy Into `<script>`

> `courseware-skeleton.html` 的 script 中已含所有文件引用注释，复制骨架即获得框架；以下文件也可单独复制进已有 HTML。

| Template | Provides | When |
|----------|-----------------|------|
| [`page-flip-system.js`](templates/page-flip-system.js) | **`getPageParam`（hash→search→parent 解析，全技能唯一 URL 参数入口）** + showPage/prev/next/keyboard(含reveal优先)/touch/URL jump/onPageEnter | **Always 且最先复制** |
| [`quiz-engine.js`](templates/quiz-engine.js) | initQuiz, showFeedback, updateQuizScore, retryQuiz, QUIZZES 结构 | **Always** |
| [`matching-quiz.js`](templates/matching-quiz.js) | initMatching（连线/配对）、initClassification（分类拖桶），Pointer Events 兼容触屏 | When 连线/配对/分类题存在（须在引用注释加行） |
| [`canvas-engine-patterns.js`](templates/canvas-engine-patterns.js) | 变量规则、draw guards、3D projection、drag rotation、共享绘图工具（drawArrow/drawLabel/drawDashedLine） | When Canvas sims exist |
| [`infographic-generator.js`](templates/infographic-generator.js) | Prompt 写作规则、双路径生成命令、验证清单 | When infographics exist |

### 3.3 Configuration Block

所有常量集中在 `<script>` 顶部：

```js
// getPageParam() 在 page-flip-system.js 定义（必须最先复制），所有 URL 参数读取一律走它，
// 禁止 new URLSearchParams(location.search)。
var PAGE_IDS = [...];       // Page section IDs
var PAGE_LABELS = [...];    // Display labels for chips
var IMG_PREFIX = 'img/';    // Image path prefix
var curPage = 0;            // 固定命名 curPage；沿用旧名（如 cur）必须补桥接：
                            //   window.xmnCurIndex = function(){ return cur; }
var QUIZZES = {...};        // All quiz data
```

**⚠ IMG_PREFIX 硬规则**：图片统一放 `deploy/img/` 子目录，`IMG_PREFIX='img/'`，路径写 `<img src="img/xxx.jpg">`。写好后 `grep -c 'src="deploy/'` 验证 0 残留——资料库发布后 zip 根平铺，`deploy/` 目录不存在。（备选：图与 index.html 同目录时 `IMG_PREFIX = ''`、裸文件名 `src="xxx.jpg"`，但推荐 img/ 子目录保持 deploy 整洁。）

### 3.3.1 测验容器 id 硬规约（v2026-10-02）

每个测验页的容器必须显式携带 id，且与 QUIZZES 键完全同名：

```html
<div class="quiz-page" id="quizPre">  <!-- id 必写：quizPre / quizMid1 / ... -->
```

⛔ **漏写后果是静默失效**：`initQuiz(quizId)` 内部 `getElementById(quizId)` 拿到 null 直接 return——
页面照常渲染、语法全绿、翻页正常，但**所有选项点击无反应**，且静态自检与人工浏览都极难发现。
（2026-10-02 实战：复用骨架时 `<div class="quiz-page">` 不带 id，四页测验全废。）

**拦截网**：`prepublish-check.py` 判据①（QUIZZES 键 ↔ id 一一对应）+ `deploy-state-test.js` 结构组 B-2。

### 3.4 Canvas Simulations

遵循 [`canvas-engine-patterns.js`](templates/canvas-engine-patterns.js)：
- **Module-level variables** — 多个 draw 函数共享的数据放脚本顶部
- **diagramDrawn guard** — 防页面重入重绘
- **Hex colors only** — Canvas 不支持 CSS 变量
- **getBoundingClientRect** — 鼠标/触屏坐标校准
- **Math.max(0.5, value)** — 防零/负半径

**Canvas 三要素同步**：`<canvas id="xxx">` ↔ `drawXxx()` ↔ `onPageEnter('pN')` 调用。任何修改后三者必须保持同步。

### 3.5 Five Image Types Implementation

| Type | Embed | Notes |
|------|-------|-------|
| a 真实照片 | `<img src="img/photo.jpg">` | Web search 下载到 deploy/img/ |
| b 数学模型图 | `<canvas id="math-xxx">` + draw | 交互优先 |
| c 示意图 | **知识图表类→内联 SVG（首选）**；写实感才 img | 见 workflow-design.md 规则0 |
| d 信息图 | **含中文标签→内联 SVG（首选）**；写实艺术感才 img | 规则0 / 规则D |
| e 知识结构图 | Inline HTML collapsible tree | `toggleBranch()` |

All images: `max-width:100%; height:auto`；`img/` 前缀，0 个 `deploy/`。

> **非知识图表类图像（写实/艺术/照片）来源（硬规约 #18）**：落地前必须已按 §2.3 **弹窗**定好来源——question 工具复选类别（搜索网络图片 / 内联 SVG 手绘 / AI 生图，可多选）；勾「AI 生图」→ 走 **image-service** 技能（先确认 `config/settings.json` 已配置），产物落 `deploy/img/`。知识图表类（c/d/e/b）**恒走内联 SVG / Canvas，不受弹窗影响**。

> **引入页现象图（硬规约 #16）**：引入页的「可感知现象」优先用 a 类真实照片（Web search CC0）或写实 AI 生图——现象必须是**学生一眼认得出**的东西（学情画像经验域内），禁用以抽象图形充当"现象"。

### 3.6 Responsive Layout — 版芯硬规则

**① 版芯必须占满 100% 屏幕宽高（严禁缩小版芯）**
- `.page{position:absolute;inset:0}` 占满容器（骨架已内置）
- **禁止**给 `.page` / `#pageContainer` / `body` 加 `max-width`/`max-height`/`width:xx%` 收缩；禁止固定宽度居中留白
- 页面仅保留正常内边距（PC 32px 36px / 移动 20px 16px）

**② 内容多 → 扩展页面高度；严禁拉伸页面宽度**
- 字/图多时页面**纵向滚动**（`.page{overflow-y:auto;overflow-x:hidden}` 已内置）
- **严禁**缩小字号/压缩行距/裁内容塞一屏；**严禁横向拉伸**、出现横向滚动条

**③ 全屏（v2026-09-28e 定案：默认不放按钮）**
- 新课件默认不放全屏/放大按钮：资料库外壳 iframe 无 `allow-fullscreen`，网页代码达不到 F11 式真全屏
- 需要全屏时引导用户按键盘 F11，或下载 HTML 直开
- 存量课件全屏三件套（HTML/CSS/JS）应整体移除；**骨架模板已不含全屏三件套**；三级降级实现抽离在 [`fullscreen-fallback.js`](templates/fullscreen-fallback.js) 仅供特殊场景按需复制（详见 workflow-deploy.md 全屏节）
- PC (≥769px): font ≥20px, title 32–40px；Mobile (≤768px): single column, touch targets ≥44px

**④ z-index 预留层级表（v2026-10-13，硬约束）**

页码指示器是教师端唯一入口（1.5s 连点 3 次进控制端），必须恒在顶层可点击——实测手机端曾被通信状态条（z-index 2900）与背景图盖住。全技能统一预留以下层级，**页面内容元素 z-index 一律 ≤99，禁止与导航层（500）争层级**：

| 层级 | 元素 | 说明 |
|------|------|------|
| 0–99 | 页面内容（含背景图/装饰层） | 作者可用的唯一区间 |
| 140 | `#revealHint` 揭示提示条 | 移动端 bottom:124px（骨架媒体查询） |
| 250 | `#mqttStatus` 通信状态 / `#teacherExit` 退出教师按钮 | 信息层，低于导航层；移动端上移至 bottom:84px |
| 300 | `.reveal-spotlight` 揭示聚光遮罩 | 全屏变暗属刻意聚焦 |
| **500** | **`#navBtns`（页码+翻页）** | **教师操作层，恒顶层（属 Step 3）** |
| 500 | `.qr-badge`（二维码徽章） | ⚠ **Step 4 注入元素**，Step 3 不存在；层级值同 500 由 step4 注入样式保证（见 workflow-deploy.md §4A.3） |
| 999 | `.qr-popup` / `.detail-overlay` | 弹窗 |
| 3000+ | toast / 观察态提示窗 | 提示层 |
| 9999 | `#imgLightbox` 图片灯箱 | |
| 10000+ | `body.fs-pseudo` 伪全屏三件套 | |

> **Step 3 改模板同步点（仅导航层）**：骨架 `#navBtns{z-index:500}` + 移动端媒体查询。
> **Step 4 另有同步点**（二维码徽章 500 / `#mqttStatus` 250 / `#teacherExit` 250 及 `!important` 覆盖旧骨架 150）：见 workflow-deploy.md §4A.3 与 step4_inject.py 注入样式。回归：deploy-state-test.js 三条 z-index 断言。

### 3.7 Quality Self-Check

**自检规约（写完 HTML 后逐条验证）**：
- [ ] 每个讲授页在 `onPageEnter` 调用 `setupReveal(pageId, [...])`，且标题（`teach-title`）**不在**队列
- [ ] 测验/仿真/封面页均**未调用** `setupReveal`
- [ ] 总结页按选定框架实现，不使用 `setupReveal`
- [ ] 揭示队列严格按**阅读顺序**排列
- [ ] `grep retryQuiz`：定义存在 + HTML 调用存在（Step 3 即时模式**保留重做按钮**；「0 处调用」是 Step 4 提交模式要求）

| Check | Method | Criterion |
|-------|--------|-----------|
| 测验容器 id 齐全 | `python scripts/prepublish-check.py <课件.html> --allow-empty-consts` | QUIZZES 键 ↔ id 一一对应 |
| JS syntax | `node scripts/syntax-check.js <课件.html>` | 0 errors |
| Page flip | Click each nav chip | Every page renders, no ghosting |
| Interactions | Click/drag each component | All respond |
| Quiz logic | Answer all + submit | Scoring correct, options lock |
| Image paths | Check all `<img src>` | `img/` prefix, 0 `deploy/` |
| Animation queue | Enter teach page, click reveal | DOM order correct, hint bar counts right |
| Teach-title visible | Enter teach page | Title immediately visible |
| 无全屏按钮残留 | `grep -c fullscreenBtn` | 0 处 |
| 版芯占满 | Wide desktop + mobile | no max-width/width:xx% shrink |
| 高度扩展/禁拉宽 | 加大量内容 | 页面纵向滚动；无横向滚动条、无重叠 |
| 测验仅选择题 | 逐页检查 pre/mid/post | only single/multi-choice；`.q-type` badge；quiz 页 0 个 initMatching/initClassification |
| 多选题判定 | 故意少选/多选/全对 | 100% 一致才判对 |
| **答案位置分布** | `node scripts/quiz-answer-check.js <课件.html>` | `RESULT: PASS`（同一测验内答案不得全集中同一位置；硬规约 #19，见 workflow-design §1.3.2 规则三） |
| 巩固题(讲授页) | 检查含 initMatching/initClassification 的页面 | 仅 teach page 讲解后、每页 ≤1 道、内容不与讲解逐字相同 |
| 页码层级 | grep z-index | `#navBtns`=500；页面内容无 >99 的定位覆盖层（层级表见 §3.6④）。**Step 3 无 `.qr-badge`，grep 命中应为 0**（硬规约 #17） |
| 经验锚点覆盖率 | 逐页对照 workflow-design §2.1 设计 | 每页 ≥1 锚点；**0 锚点页 = 返工**（硬规约 #16） |
| 引入页形态 | 检查首个讲授页 | 现象+认知冲突问题开头；0 定义/公式开头；现象导入篇幅 ≤30% |
| 前沿连接 | 目视 + grep 独立页型 | ≥1 处且编织于引入/讲解/总结中；无独立前沿页、无挂件卡片 |
| 举例经验域 | 逐页对照学情画像 | 讲授页举例 ≥1 个来自经验域；巩固题情境已换域且在清单内 |
| Responsive | DevTools 390×844 | No overflow |
| 交付警示句原文照抄 | Step 3 交付末尾 | Markdown 警示引用块（原文照抄）为整条消息**最后一个元素**，其后零内容 |
| 用户批准门控 | Step 0~4 每步结尾 | question 工具实现，禁止纯文本提问代替；⛔ 须排在红色警示块之后的「下一轮」（基尔霍夫事故：同轮排在警示块前会令警示块漏发） |

**First render is almost never right.** Always ≥1 fix-verify cycle.

### ⚠ Step 3 交付纪律（完成 HTML 后必须醒目提示）

- Step 3 产出的是**静态 HTML 文件**，**不支持**学生扫码互动（无 MQTT 同步、无 QR 徽章、无提交上报）。
- 交付时必须用**最醒目的警示形态**（OpenCode 聊天无自定义颜色渲染，统一用 **Markdown 警示引用块**：`> ⚠️` 引用块内加粗，禁止普通正文带过）明确告知，**警示句必须原文照抄、一字不改，且警示引用块必须是整条消息的最后一个元素（其后零内容）**，不得改写、缩写或替换为自拟话术（2026-09-29 认知负荷理论课件实战教训；2026-10-02 抽屉原理课件复盘：警示句被改写属违规）：

  **「⚠ 当前生成的是静态 HTML 文件，不支持学生扫码互动！若要支持学生扫码答题与实时统计，必须执行 Step 4（4A 改 HTML + 4B 部署）。」**

- 「先审阅再 Step 4」提醒放在警示框**之前**：执行 Step 4 之前，请先审阅静态 HTML 的功能是否满足需求（翻页、动画、仿真、测验判分等）。
- **交付消息完整顺序（硬性，与 SKILL.md Step 3 交付纪律一致）**：正文 → 「先审阅再 Step 4」提醒 → **Markdown 警示引用块（整条消息最后一个元素，其后零内容）** → **question 工具用户批准门控置于下一轮（组件实现，禁止纯文本提问代替；⛔ 禁止同轮排在警示块前，否则门控返回结束本轮、警示块漏发）**。
- ⛔ **Step 3 产物零二维码徽章（硬规约 #17，v2026-10-13）**：静态 HTML **不得包含**任何 `.qr-badge` 元素、加入弹窗、`_xmnBadgeSync`、`IS_DEPLOYED` 闸门 —— 二维码徽章是 **Step 4 专属**，`step4_inject.py` 注入时才生成。**禁止**「先把徽章埋进静态页再用闸门藏起来」这种写法（历史错误做法，2026-10-13 大模型课件事故根源）。Step 3 唯一要预留的是 `#navBtns{z-index:500}`（页码恒顶层，属导航层，非徽章）。徽章规范见 [workflow-deploy.md](workflow-deploy.md) §4A.3 与 `templates/qr-badge-injection.js`。

> **🈲 术语统一（防 grep 误伤）**：本技能中「徽章」一词三义混用，文档一律按下表书写，禁再单用「徽章」二字：
> - **二维码徽章** = `.qr-badge`，扫码加入/活动统计，**仅 Step 4**
> - **题型徽章** = `.q-type`（单选题/多选题），**属 Step 3 测验**
> - 泛指 UI badge 一律写明具体 class

---

---

## Progressive Reveal Animation System — 渐进呈现（硬规则）

**核心原则**：讲授页不一次性展示全部内容，教师点击逐步揭示，每步 1 个元素组。动画系统内置于 `courseware-skeleton.html`。

### 使用方式

每个讲授页在 `onPageEnter` 中调用 `setupReveal(pageId, items)`：

```js
// 注意：标题 teach-title 不加入队列，进入页面即显示
if (id === 'p2') setupReveal('p2', [
  { sel: '#p2s1', anim: 'reveal-fade-up' },           // 第1段
  { sel: '#p2s1b', anim: 'reveal-fade-up' },          // 左文（先于图揭示）
  { sel: '.fig.float-r', anim: 'reveal-fade-up' },    // 右浮动图（按阅读顺序）
  { sel: '.key-box', anim: 'reveal-fade-up' },        // 关键框
  { sel: '.feature-list li', anim: 'reveal-fade-up', seqDelay: 150 }  // 列表逐条
]);
// 顺序 = 阅读顺序；讲授页统一纵向动画 reveal-fade-up（禁止横向动画造成顺序错觉）
// 图文对用 <div class="reveal-img-group"> 包裹，作为一步揭示
```

- `sel`: CSS 选择器（page section 内查找）；`anim`: 动画 class；`delay`: 该组揭示前等待 ms；`seqDelay`: 组内多元素间隔 ms

### 动画目录（24 种，按场景选用）

| 场景 | class 名 |
|------|----------|
| 段落/标题首次呈现 A1 | `reveal-fade-up` |
| 多段落依次 A3 | `reveal-fade-up-seq` |
| 打字机 A2 | `reveal-typewriter` + JS |
| 模糊聚焦 A4 | `reveal-blur-focus` |
| 高亮脉冲 A5 | `reveal-pulse` |
| 字幕展开 A6 | `reveal-slide-x` |
| 列表逐条 B1 | `reveal-li-slide` |
| 编号步骤 B2 | `reveal-step-num` |
| 帷幕揭图 C1 | `reveal-curtain` |
| 底片显影 C2 | `reveal-sepia` |
| 框入聚焦 C3 | `reveal-focus-in` |
| 浮动入位 C4 | `reveal-float-in-r/l` |
| Ken Burns C5 | `reveal-kenburns` |
| 卡片弹入 D2 | `reveal-card-pop` |
| 网格填充 D3 | `reveal-card-grid` |
| 折叠展开 D4 | `reveal-fold` |
| 关键框滑入 E1 | `reveal-slide-left/right` |
| 引用金句 E2 | `reveal-quote` |
| 表格逐行 E3 | `reveal-tr-fade` |
| 数字跳动 E4 | `reveal-count-up` + JS |
| 聚光灯 E5 | `reveal-spotlight` |
| 勾选渐现 F1 | `reveal-check` |
| 缩进展开 F2 | `reveal-indent` |
| 翻牌 F3 | `reveal-flip-card` + JS |

（skeleton 内置全部 class，含子元素动画光标 `.tw-cursor`、`.highlight-num` 等。）

### 每页必须做的事（页面类型动画决策）

| 页面类型 | 动画模式 |
|----------|:---:|
| **封面页** | 不启用揭示，内容直接可见 |
| **讲授页** | 点击逐段展开，`setupReveal`，**全部元素纳入队列**（除标题） |
| **仿真页** | 不启用揭示 |
| **测验页** | 不启用揭示 |
| **总结页** | 按选定框架内置交互，不使用 `setupReveal` |

- **标题常驻（硬规则）**：各页标题（teach-title / sim-title / summary-title / 封面标题）绝不入 revealQueue、绝不做进入动画——页面进入即显示
- **讲授页所有内容元素（除标题）必须全部入队**——不允许任何内容直接可见
- **严格按阅读顺序（硬规则）**：队列顺序 = 读者从上到下、从左到右；图片按版面位置参与排序；禁止图片先于说明文字
- **图文合并**：`<img>` 与 caption 用 `<div class="reveal-img-group">` 包裹
- `setupReveal` 在 `onPageEnter` 首次进入时调用（`pageEntered` 守卫后）
- **⚠ `.reveal-hidden.reveal-done` 必须含 `pointer-events:auto`**（骨架已内置）

提示条：讲授页底部自动显示「点击页面继续揭示 X/N」，全部揭示后自动隐藏。

### 键盘箭头控制揭示与翻页（硬规则）

键盘箭头优先推进/回退揭示序列，揭示全部完成后才翻页：

| 按键 | 行为 |
|------|------|
| → / ↓ / 空格 | 有未揭示 → `nextReveal(pid)`；全部已揭示 → `nextPage()` |
| ← / ↑ | `pageRevealIndex > 0` → `prevReveal(pid)`；第0步 → `prevPage()` |
| 无 reveal 队列的页 | 直接翻页 |

```js
document.addEventListener('keydown', function(e) {
  var pid = PAGE_IDS[curPage];
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
    e.preventDefault();
    if (typeof pageRevealActive !== 'undefined' && pageRevealActive[pid] &&
        pageRevealQueues[pid] && pageRevealIndex[pid] < pageRevealQueues[pid].length) {
      nextReveal(pid);
    } else { nextPage(); }
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault();
    if (pageRevealQueues[pid] && pageRevealIndex[pid] > 0) { prevReveal(pid); }
    else { prevPage(); }
  }
});
```

`prevReveal` 逆向撤销：移除 anim/reveal-done → 恢复 `reveal-hidden`（opacity:0）→ index-- → 重置 `.count-num`（归零+清 data-counted）与 `.typewriter`（中断 `_twTimer`+清 data-done）。`afterRevealEffects` 中的 typewriter `setInterval` 必须存到 `span._twTimer` 以便中断。

---

## Image Lightbox — 图片全屏灯箱（硬规则）

所有课件图片必须支持点击全屏放大，再点击图片或背景收回。CSS/HTML/JS 已内置于骨架。

交互：点页面 `<img>` → 全屏居中放大（max 95vw×95vh，暗背景）；点放大图/背景/✕/ESC → 关闭。

CSS（骨架已含，单独补件时复制）：

```css
#imgLightbox{
  display:none;position:fixed;inset:0;z-index:9999;
  background:rgba(0,0,0,.92);justify-content:center;align-items:center;
  cursor:zoom-out;
}
#imgLightbox.show{display:flex}
#imgLightbox img{
  max-width:95vw;max-height:95vh;object-fit:contain;
  border-radius:8px;box-shadow:0 8px 40px rgba(0,0,0,.5);
  animation:lightboxIn .3s ease;
}
@keyframes lightboxIn{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
#imgLightbox .lb-close{
  position:absolute;top:20px;right:24px;width:44px;height:44px;
  border-radius:50%;background:rgba(255,255,255,.15);color:#fff;
  font-size:24px;cursor:pointer;display:flex;align-items:center;justify-content:center;
  border:none;transition:background .2s;
}
.teach-text img, .fig img, .page-img, .card img{cursor:zoom-in;transition:opacity .2s}
```

HTML（`</body>` 前）：

```html
<div id="imgLightbox" onclick="closeLightbox()">
  <button class="lb-close" onclick="closeLightbox()">✕</button>
  <img id="lbImg" src="" alt="全屏查看">
</div>
```

JS：

```js
function openLightbox(src) {
  document.getElementById('lbImg').src = src;
  document.getElementById('imgLightbox').classList.add('show');
}
function closeLightbox() {
  document.getElementById('imgLightbox').classList.remove('show');
}
document.addEventListener('click', function(e) {
  if (e.target.tagName === 'IMG' && !e.target.closest('#imgLightbox') && !e.target.closest('.qr-img-wrap')) {
    e.stopPropagation();
    openLightbox(e.target.src);
  }
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var lb = document.getElementById('imgLightbox');
    if (lb.classList.contains('show')) { closeLightbox(); e.preventDefault(); }
  }
});
```

**与 reveal 引擎集成规则**：`reveal-hidden` 含 `pointer-events:none`；`.reveal-hidden.reveal-done` 含 `pointer-events:auto`；reveal 全局点击器排除 `IMG` 标签；灯箱 click 监听器 `stopPropagation()` 防冒泡触发 nextReveal。

排障：点图无反应→查 pointer-events:auto；点图触发揭示→reveal 未排除 IMG；放大后点图关不掉→图片上误加 `stopPropagation`，移除让冒泡到 `#imgLightbox.onclick`。

---

## Summary Page — 总结页（4 套框架选 1，硬规约 #12）

设计理念：总结页不是要点罗列，而是帮助学生建立**结构化知识网络**的交互工具。旧版「要点卡片+口诀」已废除。

### 决策流程（Step 1 执行，须给用户确认推荐+理由+备选）

```
知识点呈网络/关系结构（概念节点+关联连线）？──→ V1·全景概念关系图
知识有因果/递进链（原因→过程→结果→意义）？──→ V2·链式问题驱动总结
知识点有明确分类、需公式/图示/例题说明？──→ V3·双栏交互式知识树
知识点为并列模块、需对照辨析？──→ V4·模块卡片渐进揭示
不确定？──→ 默认 V4（通用性最强）
```

| # | 框架 | 交互机制 | 模板 |
|---|------|----------|------|
| V1 | 全景概念关系图 | Canvas 知识节点+关系连线+详情浮层；拖拽平移+滚轮缩放 | [`summary-v1-panorama-graph.html`](templates/summary-v1-panorama-graph.html) |
| V2 | 链式问题驱动 | 核心问题→点击揭示答案+引出子问题→问答链总览；翻牌卡片 | [`summary-v2-question-chain.html`](templates/summary-v2-question-chain.html) |
| V3 | 双栏交互知识树 | 左栏折叠树+右栏动态详情（公式/图示/例题/易错）；颜色编码模块 | [`summary-v3-dual-panel-tree.html`](templates/summary-v3-dual-panel-tree.html) |
| V4 | 模块卡片渐进揭示 | 大卡片阵列；初始标题+摘要；点击展开翻牌卡片；逐张/全部展开 | [`summary-v4-card-reveal.html`](templates/summary-v4-card-reveal.html) |

**通用规约**：① 容器 `width:100%;max-width:none`；② 标题/关键字 ≥24px bold、正文 ≥20px；③ 字体放大同步加大 padding/gap；④ 不使用 `setupReveal`；⑤ 不设「重置视图」按钮。

**Step 3 集成要点**：① 复制模板 HTML 到总结页 `<section>`，替换占位文本；② 保留模板内 script 逻辑，合并时注意命名冲突；③ 主题色变量对齐所选配色；④ 逐框架验证交互（展开/翻面/选节点/全部展开折叠）。
