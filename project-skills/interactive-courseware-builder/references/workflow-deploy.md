# Workflow Deploy Guide · Step 4 学生交互与部署 + 教学控制标准件（全量细则）

> 由 SKILL.md 外迁。**Step 4 开工前必读**。



---

## Step 4 — Student Interaction & Deployment

> **⚠ CRITICAL: Step 4 = 4A（先改HTML）→ 4B（再部署），不可跳步！**
> 用户说「部署」或「Step 4」= 默认执行完整 4A+4B。同一会话内 4A 已做过 → 只做 4B。

Skip for local-only courseware. Only when students scan QR codes.

### 执行协议

| # | Action                                                                    | Why                                           |
| - | ------------------------------------------------------------------------- | --------------------------------------------- |
| 1 | Read current HTML state; determine if 4A already applied                  | Avoid duplicate injections                    |
| 2 | Inject MQTT framework + QR generator library                              | Load before QR/submit logic; `async`          |
| 3 | ALL quiz pages with QR badges → submit mode (`unified-quiz-submit.js`)    | Collect & publish once                        |
| 4 | QR badges on ALL quiz + simulation pages (`qr-badge-injection.js`)        | Every interactive page scannable              |
| 5 | Teacher stats dashboard (`detail-modal.html` + `detail-stats.js`)         | Participation/accuracy/distribution           |
| 6 | JS syntax check + page-flip verification                                  | Catch blocking/syntax errors pre-deploy       |
| 7 | 发布到**资料库**（`scripts/publish_to_library.py`）→ `workbuddy.link/p/<node_id>` | 4B only after 4A passes；**禁用 CloudStudio 路线** |

---

## 4A · Modify the HTML

逐项注入，**每次注入后验证 JS**。

### 4A.1 提交模式（ALL quiz pages with QR badges）

[`templates/unified-quiz-submit.js`](../templates/unified-quiz-submit.js)

1. 选项**只选一次不可改**→ 提交前可改（v2026-09-29 定案，见 §4.6：`if (container._submitted) return;`）
2. 选完不显示反馈，仅标记 `answered` class
3. 点「提交本页成绩」才一次性显示正误与解析
4. 提交后按钮变灰，显示得分
5. **去掉「重做」按钮** → 改为「提交本页成绩」
6. **所有测验页统一**——前测/中测/后测全部提交模式（全部有 QR 徽章）
7. **`submitQuiz` 先写本地 `xmnAgg` 再 `xmnPublish`**（勿依赖 MQTT 回环）

Modify `initQuiz`: `var isSubmitMode = true;`（无条件，Step 4 全部提交模式）。

### 4A.2 Inject MQTT client

[`templates/mqtt-framework.js`](../templates/mqtt-framework.js)

**⚠ MQTT CDN 版本坑**：必须 `mqtt@4.3.7`（UMD）。无版本号 unpkg 会拉 v5（ESM-only）→ 普通 script 加载遇 import/export 直接 SyntaxError → 全页 JS 中止。手机扫码必须 `async`，否则阻塞卡封面。

**⚠ unpkg 在中国网络不可达**：移动/4G 常超时 → 数据只存手机本地 → 教师端永远收不到。**必须多源 fallback**（jsdelivr 优先，国内有节点）。

**⚠ broker 单点故障**：公共 broker 抖动丢包 → 须主备自动切换（`broker-cn.emqx.io` → `broker.emqx.io`），6 秒连不上主 broker 切备用。

**⚠ broker 分叉坑（最隐蔽）**：两端各自独立决策 broker → 教师端连 A、手机端切 B → 数据永不同步（「手机提交了但电脑收不到」最常见根因）。**必须按 CLASS_ID 确定性选同一 broker**：`MQTT_BROKER_INDEX = hash(CLASS_ID) % MQTT_BROKERS.length`（模板 `xmnBrokerHash` 已实现），重试**环形切换** `(idx+1) % len`。国内课堂优先 `broker-cn.emqx.io`。

**MQTT 多源 fallback + 状态指示器（完整代码，复制到 `<head>`）**：

```html
<script>
(function(){
  var mqttSources = [
    'https://cdn.jsdelivr.net/npm/mqtt@4.3.7/dist/mqtt.min.js',
    'https://fastly.jsdelivr.net/npm/mqtt@4.3.7/dist/mqtt.min.js',
    'https://unpkg.com/mqtt@4.3.7/dist/mqtt.min.js'
  ];
  var mIdx = 0;
  function tryLoadMqtt() {
    if (mIdx >= mqttSources.length) { console.warn('[MQTT] 所有CDN源均加载失败'); return; }
    var s = document.createElement('script');
    s.src = mqttSources[mIdx];
    s.async = true;
    s.onload = function() { console.log('[MQTT] 加载成功，源:', mqttSources[mIdx]); };
    s.onerror = function() { console.warn('[MQTT] 加载失败:', mqttSources[mIdx]); mIdx++; tryLoadMqtt(); };
    document.head.appendChild(s);
  }
  tryLoadMqtt();
})();
</script>
```

状态指示器 CSS（`<style>`）：`#mqttStatus` 固定左下角 + `#mqttDot`（绿#4CAF50 在线 / 红#f44336 离线）；HTML（`</body>` 前）：`<div id="mqttStatus"><span class="dot" id="mqttDot"></span><span id="mqttText">数据同步: 等待连接</span></div>`。connect/offline/error 事件更新 `mqtt-framework.js` 已内置；手工实现须对齐。

### 4A.3 QR badges（ALL quiz + simulation pages）

[`templates/qr-badge-injection.js`](../templates/qr-badge-injection.js)

- 每个前测/中测/后测/仿真页都要 QR badge（不只是后测）
- 默认 `display:none`，`onPageEnter` 时 `display:flex`

**⚠ QR `src=""` 坑**：`<img src="">` 时浏览器把 `element.src` 解析为当前页 URL。判断必须用 `!qrImg.getAttribute('src')`，不能用 `!qrImg.src`。

**⚠ QR API 慢/blocked**：`api.qrserver.com` 在中国网络慢或不可达。**必须本地生成**（`qrcode-generator` data URI），仅本地库失败才 fallback 图片 API：

```html
<script async src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"
        onerror="console.warn('QR generator CDN failed')"></script>
```

```js
if (qrImg && !qrImg.getAttribute('src')) {
  if (typeof qrcode !== 'undefined') {
    try {
      var qr = qrcode(0, 'L'); qr.addData(qrUrl); qr.make();
      qrImg.src = qr.createDataURL(4, 0);
    } catch(e) {
      qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(qrUrl);
    }
  } else {
    qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(qrUrl);
  }
}
```

**本地优先时序坑**：qrcode-generator 以 async 引入而 `injectBadge()` 同步调 `renderQrInto()` → 当帧库未就绪 → 恒走远端且库到位后 src 非空、本地生成永不执行。**修法**：先挂远端图，再轮询（≤4000ms）换 `createDataURL()`，`data-qrdone` 防重复。验收：线上 `#qrImg_*` 须 `data:image/...` 且长度 >500。

**每页徽章制 + 加入弹窗（v2026-10-13）**：`build_body` 为**每个页面 section** 注入一枚徽章——活动页（测验/仿真）带 `data-activity`（弹窗含统计），其余页（封面/讲授/总结）为无 `data-activity` 的「加入」徽章，点击走 `openJoinPopup(pageId)`：共用 `#qrPopup_join` 弹窗，二维码**按当页动态重建**（`#page=pN&class=CLASS_ID`，迟到学生当场扫码即入课堂并跟随同步）。加入弹窗无统计数据，不需要 `xmnClear`（prepublish-check 按 `qrPart_/qrAvg_` 豁免）。onPageEnter 的「全部下架+当前页上架」逻辑不变，天然每页有且仅有一枚可见徽章。回归：deploy-state-test「每个页面均有 QR 徽章」+「加入徽章弹出加入弹窗」。

> ⛔ **Step 3 产物恒无二维码徽章（硬规约 #17）**：二维码徽章**只在 Step 4 由注入器生成**，Step 3 静态 HTML 中不得预先埋入 `.qr-badge` 元素/加入弹窗/`_xmnBadgeSync`/`IS_DEPLOYED` 闸门。禁止「先埋进静态页再用闸门藏起来」的写法。

**IS_DEPLOYED 部署闸门（注入后生效）**——确保 `file://` 或未部署预览态**永不显示**二维码徽章：

```js
var IS_DEPLOYED = (function(){ try { return location.protocol!=='file:' && /^https?:\/\//.test(PUBLISH_BASE||''); } catch(e){ return false; } })();
// 初始化时：document.body.classList.toggle('deployed', IS_DEPLOYED);
// 徽章 CSS：body.deployed .qr-badge.on{display:flex}
// 徽章切换：onPageEnter 开头（守卫之前）remove all + add 当前页；另见下方 DOMContentLoaded 同步
```

模板见 [`qr-badge-injection.js`](../templates/qr-badge-injection.js)（已含 `body.deployed` 前缀 CSS 与 `IS_DEPLOYED` 示例）。

**每页徽章切换的两个必守点位（v2026-10-13，step4_inject.py 已按此注入，勿手改回退）**——实现「每页都有且只有一枚可见徽章（含首页）」，缺一即出现真实缺陷：

1. **toggle 必须插在 `onPageEnter` 函数开头（`if (pageEntered[id]) return;` 守卫之前）**。若插在函数末尾，会被守卫拦截：回访某页时守卫提前 return → 徽章停在上一页（**「回访错显」**；gene-protein 实测 `→ p1 回访显示 p5`）。
2. **徽章 HTML 追加在文档末尾**（晚于初始 showPage 与 JS 块），故加载时 onPageEnter 查不到徽章 → 必须在 **DOMContentLoaded 后**再同步一次「当前页徽章」（build_js_block 注入的 `_xmnBadgeSync`）。否则首屏（含首页加入徽章）**永不显示**（**「首屏无徽章」**；gene-protein 实测 `加载后 (none)`）。

回归：`deploy-state-test.js` 已加两条断言（加载后仅首页徽章 ON / 回访切回当前页），未部署模式则断言 0 枚 ON。

**教师操作层层级（v2026-10-13）**：页码指示器是教师唯一入口，`#navBtns` 与 `.qr-badge` 统一定 z-index **500** 恒顶层；`#mqttStatus`/`#teacherExit` 降为 **250**（信息层，移动端经注入样式媒体查询上移至 `bottom:84px` 让位导航行）；页面内容元素 z-index ≤99。完整层级表见 workflow-dev.md §3.6④。

### 4A.4 Teacher stats dashboard（每题选项分布条形图 · v2026-10-13 增强）

直接复制 [`templates/detail-stats.js`](../templates/detail-stats.js)（完整 openDetail/closeDetail + 数据映射，只改 `DETAIL_QUIZ_MAP` 活动→测验映射）。

HTML 侧：复制 [`detail-modal.html`](../templates/detail-modal.html) 的 CSS + 面板 HTML；每个 QR 弹窗加按钮：

```html
<button class="btn-sim" onclick="openDetail('post');closeQRPopup('post')"
  style="margin-top:8px;display:block;width:100%">查看每题详情</button>
```

**视觉层级（选项统计为视觉重点、选项文字为非重点）**：每题 A/B/C/D 选项行 = 加粗放大的百分比数字（20px / font-weight 800）＋ 条形图（高 18px；绿=正确 / 橙=错选 / 灰=无人选）；**选项文字默认完全隐藏、不占版式高度**——鼠标移到该行（A/B/C/D 标签或条形图）时以浮窗 `.opt-tip`（深藏青底白字、纯 CSS `:hover` 淡入，`position:absolute` 定位于该行上方）显示该选项内容，**浮窗文本最前以加粗字母（`<b>A</b>`/`<b>B</b>`…）标注选项序号**便于教师一眼识别，移开即隐。无数据显示「暂无提交数据」。

**v2026-10-13 四项增强/修复**：

1. **选项文字从 DOM 读取**：`_dsGetOptText(qEl, idx)` 取 `.opt[data-idx]` 克隆后剥掉 `.badge` 字母——`QUIZZES` 数据只存 `answer`/`explain`，**故无需改数据模型，向后兼容全部已发布课件**。
2. **修复多选题统计**：`chosen` 为数组，旧代码 `chosen >= 0` 恒 false → 多选统计全 0；改为数组遍历计数。
3. **修复多选正确项标记**：旧 `oi === q.answer` 对数组恒 false → 正确项不显 ✓/绿；改用 `_dsIsCorrectIdx(q, idx)`（兼容 number / array）。
4. **题干清理 + 压缩高度**：题干剥 `.q-type` 徽章并去重复题号；删除「参与人数」「正确率」两行；bar 高 28→18px、卡片内边距 16→12px、选项行 padding 9→5px。

**正确答案标记规则**：正确选项旁只加 **✓** 符号，不单独写「正确」二字；反馈文本可用完整句子，避免单独突出「正确」标签。

### 4A.5 Clear data behavior

`mqtt-framework.js` 的 `xmnClear` 已清**全部**测验活动：

- **优先自建模态确认**：`showConfirmModal(msg, onOk)`（mqtt-framework.js 内置；iframe 沙箱可能禁原生对话框，**不得只写 `confirm()`**）。消息：「确定要清空本课件中全部测验题的数据吗？此操作不可恢复。」
- Clear retained messages for every known `sid` across every activity in `ACTIVITY_QUIZ_MAP`；clear `xmnAgg`/`localStorage`/UI；refresh badge stats
- ⚠ 清空按钮 onclick **只调 `xmnClear('xxx')`，不要追加 `closeQRPopup`**（否则清完关弹窗，用户「离开二维码页面」——《价格理论》踩坑）
- ⛔ **确认回调必须传 `true`**：`showConfirmModal` 确定按钮必须写 `onOk && onOk(true)`（原生 confirm 兜底同理），不得写 `onOk()`——调用方 `function(ok){ if(ok) xmnClearDo(...) }`，不传参则 ok 恒 undefined → **清空静默不执行**（2026-09-30 诺尔斯实机踩坑）。`teaching-control.js` 自带的旧版 `showConfirmModal`/`showToast` 与 mqtt-framework 重复定义且漏传参——**注入时必须删除 teaching-control 自带的两份，全课件只保留 mqtt-framework 一份**。回归：pagesync S14

`updateBadgeStats` 已内置在 `mqtt-framework.js` 末尾（含 avgEl 清空重置 '-'）。手写参考：

```js
function updateBadgeStats(activity) {
  var subs = xmnAgg[activity] || [];
  var partEl = document.getElementById('qrPart_' + activity);
  if (partEl) partEl.textContent = subs.length;
  var avgEl = document.getElementById('qrAvg_' + activity);
  if (avgEl) {
    if (subs.length > 0) {
      var total = subs.reduce(function(s, x) { return s + x.score; }, 0);
      avgEl.textContent = (total / subs.length).toFixed(1);
    } else { avgEl.textContent = '-'; }   // ⚠ 必须有 else 分支，清空后旧值残留
  }
  if (typeof populateMiniStats === 'function') populateMiniStats(activity);
}
```

**⚠ 映射一致性规则**：`ACTIVITY_QUIZ_MAP` 以 `mqtt-framework.js` 为单一事实来源；`unified-quiz-submit.js`/`detail-stats.js` 检测到已存在时 `typeof` 复用，不得重定义。三处活动名（pre/mid1/…/post）必须与页面实际测验页数一致，否则统计面板打不开或清空不完整。

### 4A.6 Quality check after modifications

**首选自动化验收（v2026-10-02 起）**：注入完成后一条命令跑完结构+行为+常量+教师链路四组断言（≈105 项，随课件测验/仿真数浮动）：

```bash
NODE_PATH=<含 jsdom 的 node_modules> node scripts/deploy-state-test.js <课件.html> --config step4.json [--node-id <id>]
```

- config 复用 4A 的 `step4.json`（quizzes/sims 清单），**答案序列运行时从课件自身 QUIZZES 读取**，任何课件通用；
- 模式自动识别：源码 NODE_ID/PUBLISH_BASE 已回写 → 部署后模式（含常量组 D）；未回写 → 部署前模式；
- 内置 jsdom 四坑的正确解法（canvas stub、禁 window.close、双轮 JSDOM 测三连点、看门狗+同步日志）——这四个坑在 2026-10-02 之前每次现写测试都要重新踩一遍；
- ⛔ 每组断言中「每个 QR 弹窗 innerHTML 含 xmnClear」是 **sim_popup 缺清空按钮缺陷的唯一探测器**——pagesync 40 项、prepublish-check、线上核验都测不出这一类「模板少给一个按钮」的缺陷。


| Check | Criterion |
|-------|-----------|
| JS syntax | 0 errors（`node scripts/syntax-check.js <课件.html>`） |
| Page flip | ALL pages work（desktop + 手机扫码；MQTT script 必须 async） |
| Quiz submit | 答完→提交→得分；选项锁定；提交后按钮禁用 |
| MQTT publish | Console retained message（devtools network/websocket） |
| QR scan | 手机→正确位置；URL = `PUBLISH_BASE + '#page=pN&class=CLASS_ID'`（**hash 传参**） |
| QR image | 点击徽章 1 秒内出码（本地生成） |
| Stats update | 第二设备提交→教师视图更新 |
| Clear data | 确认→全部活动归零；badge 0 人、avgEl '-' |

**验收测试三层分工（v2026-10-02 定案，各层抓不同缺陷，缺一层漏一类）**：

| 层 | 工具 | 抓什么 | 抓不到什么 |
|---|---|---|---|
| 静态自检（源码 grep） | `prepublish-check.py` / `syntax-check.js` / `scan_braces.py` | 标记缺失、字面量残留、括号不平衡 | 运行时行为、数学表述错误 |
| 行为测试（jsdom 驱动） | `deploy-state-test.js` / `pagesync-test-mqtt.js` | 提交流程、导航焊死、教师链路、弹窗内容 | Canvas 渲染效果、jsdom 不支持的能力 |
| 纯数学验证 | 课件自带 `_math-verify.js`（每课现写，模板见 pitfalls） | 公式数值、下界成立性、构造性反例 | 与前两层无关 |

> ⚠ jsdom 层测 Canvas 只能验证「不抛错」，渲染效果须真机目视；数学层能抓出前两层全绿时的表述错误（实例：区间抽屉「距离小于 1」实为「不超过 1」，见 pitfalls）。


### 4A 注入顺序清单（执行用，①→⑨）

每步完成后 `node scripts/syntax-check.js` 验证；任何一步失败停下修复。**⑨ 是历史上最容易漏的一步**——只按 ①~⑧ 走会漏掉整个教学控制（A~H），线上表现为「教师翻页学生不跟随 / 学生扫码跳页 >5s / 关弹窗同步静默断」。

**首选路线（2026-10-02 起）**：`python scripts/step4_inject.py --config step4.json --html <课件.html> --probe` 先探针（报告 9 步锚点齐不齐），修齐后 `--apply`。驱动已固化 ①②④⑥⑦⑨ 模板件与 7 集成点——函数边界由 `scan_braces.py` 定位（免疫字符串/注释/正则里的括号），每个 rep() 带计数+括号平衡双断言，写盘后自动复扫、失败回滚 .bak。每课只需写小 config（`{"quizzes":[{"act","quizId","page","hasAvg"}],"sims":[{"act","page"}],"extraReps":[]}`）。手写注入仅作 config 覆盖不到时的兜底，且**每个 rep() 的 OLD/NEW 括号净值必须相等**（2026-10-02 事故：rep 把 onPageEnter 闭合 `}` 当 OLD 文本吃掉 → 全脚本 unclosed brace）。

| Step | What to Copy | Where | Modify |
|------|-------------|-------|--------|
| ① | MQTT CDN + QR generator CDN | `<head>` | 都加 `async`；MQTT 钉 `@4.3.7`；QR 钉 `@1.4.4` |
| ② | `mqtt-framework.js` 全部 | `<script>` | `ACTIVITY_QUIZ_MAP` 改为项目映射 |
| ③ | quiz-engine.js → isSubmitMode | 已有 script | `var isSubmitMode = true;`；删所有 retryQuiz HTML 调用 |
| ④ | `unified-quiz-submit.js` | `<script>` | ACTIVITY_QUIZ_MAP 与 ② 一致 |
| ⑤ | 提交按钮+分数 | 各测验 `<section>` | `id="quizXxx_submitBtn"` + `id="xxxScore"` |
| ⑥ | `qr-badge-injection.js` + `detail-modal.html` | `<style>`+`<script>`+`<section>`+`</body>`前 | 一次性注入 QR 徽章与详情面板；**每页徽章制（v2026-10-13）**：build_body 按 HTML 全部 page section 注入徽章，活动页带 `data-activity`、其余页为加入徽章 + 共用 `#qrPopup_join` |
| ⑦ | `detail-stats.js` + updateBadgeStats + onPageEnter QR 逻辑 | `<script>` | 合并一次注入 |
| ⑧ | 语法+功能验证 | 命令行+浏览器 | `python scripts/scan_braces.py <课件.html>` 必须 **BALANCED**（秒级定位 unclosed brace，免疫正则/模板串误报）+ `syntax-check.js` 0 err；见 4A.6 |
| ⑨ | **`teaching-control.js` 整文件 + 其文件头 7 个集成点** + 伪全屏兜底 CSS 三条（`body.fs-pseudo …`，**保留勿删**，删了 S7 FAIL） | `<script>` + 5 处函数 | **必做**：逐条对齐 7 集成点；注完**必跑** `node scripts/pagesync-test-mqtt.js <课件.html>` **ALL PASS 才可发布** |

7 个集成点（teaching-control.js 文件头有完整说明）：① connect 回调（教师）`setTimeout(function(){ xmnEnterTeacherRole(); },600)`【C/G】② message 回调 `handleControlMessage`/`handleSyncMessage` 分支 ③ showPage 末尾 `if(isBroadcaster && !syncing) xmnBroadcastPage()` + 手动翻页 `lastManualNav`【D】④ next/prev 导航闸门【E】⑤ closeQRPopup 教师端不停广播、学生端 `if(!IS_TEACHER) stopBroadcast()`【A】⑥ 学生 connect 后 `requestCurrentPage()`【H】⑦ `xmnConnect` 回填 `myClientId`(=clientId) + `will` 遗嘱【C】。

---

## 资料库发布 & 教学控制标准件（第四代硬规则）

课件跑在资料库外壳的 iframe 内（302 + iframe 白名单 + sandbox）。以下是所有第四代课件**必须内置**的能力。

### 0 · 环境事实

| 事实 | 影响 | 对策 |
|---|---|---|
| 外壳 302 → iframe 白名单，**内嵌课件 iframe 内 query 与 hash 都拿不到** | 教师身份不能靠 `?teacher=1`/`#teacher=1`（壳内一律失效） | 教师身份走三连点 + localStorage；学生翻页走 MQTT 广播。⚠ 学生手机扫码直开是另一场景，课件自身仍能解析 hash |
| iframe sandbox 无 `allow-fullscreen` | `requestFullscreen()` 被静默拒绝 | 默认不放全屏按钮（见下 §3） |
| 课件与外壳可能跨源 | 无法读写父文档 | 伪全屏兜底 |
| 外壳在登录墙后，自动化浏览器核验不了渲染 | 无法截图确认 | 发布后请用户真机目视；AI 侧保证源码标记 + 管道成功 |

### 1 · 页码同步（教学控制：A~H）

关键常量（**节点/班级双重隔离**）：

```js
var NODE_ID        = '';                                        // 发布时由脚本回写
var PUBLISH_BASE   = '';                                        // 发布时回写为 https://workbuddy.link/p/<NODE_ID>
var SYNC_TOPIC     = 'xmn-sync/' + (NODE_ID || CLASS_ID);       // 页码同步：按「节点」隔离（派生式，勿写字面量）
var SYNC_CTL_TOPIC = SYNC_TOPIC + '/ctl';                       // 广播权仲裁
var XMN_BASE       = 'xmn/' + CLASS_ID + '/answers';            // 答题数据：按「班级」隔离
var CLASS_ID       = getPageParam('class') || 'wb-' + NODE_ID;  // ⚠ 绝不留 'DEFAULT-CLASS'
```

**⚠ CLASS_ID 铁律**：留 `'DEFAULT-CLASS'` 字面量 → 所有课件共享话题 → **答题数据跨课件串台**。**全文件任何位置（含注释）都不得出现该字面量**——线上核验是全文件 grep，注释照样 FAIL。模板默认派生式写法；发布脚本会显式化为 `|| 'wb-<node_id>'` 字面量。新建课件直接用模板写法，不要手改。

**跳页/跟随问题完整修复（A/B/C/D/E/F/G/H）**：

| 项 | 问题 | 实现要点 |
|---|---|---|
| **★** | **connect 回调漏订阅 `SYNC_TOPIC`/`SYNC_CTL_TOPIC`** → 学生收不到广播 → 永久停首页（漏订时旧测试 S2 仍 PASS 的盲区已修） | connect 回调除 `XMN_BASE+'/#'` 外**必须再订阅** SYNC_TOPIC 与 SYNC_CTL_TOPIC；模板已内置三条订阅，照抄勿删 |
| **A** | 关二维码弹窗后仍后台广播拽学生 | `closeQRPopup` 教师端不停广播；仅学生端防御性 `stopBroadcast()` |
| **B** | 学生误点 📱 徽章变广播者 | 学生端（!IS_TEACHER）隐藏所有 `.qr-badge` |
| **C** | 多广播者打架（学生端闪跳） | **控制端唯一**：`publishClaim()` 向 `SYNC_CTL_TOPIC` 续租、`activeClaimId` 标识唯一控制端——租约仲裁（在位者优先；仅失联超 `CLAIM_TTL` 或带 `force` 的显式接管才易主）+ MQTT 遗嘱（崩溃/关页即释约）+ 观察态**提示窗**（「接管控制」按钮 + **3 秒倒计时**，超时自动收起、不夺权）+ 一键接管。⛔ 不可用「最新 ts 恒赢」——两端各 2s 心跳必然心跳级易主（2026-10-12 定案） |
| **D** | 学生端须焊死纯跟随 | **不创建**任何跟随/自由开关；学生初始化即 `setStudentNav(false)` 且**永不恢复**；`followTeacher` 恒 true，`handlePageSync` 始终应用老师页码 |
| **E** | 学生端仍能翻页 | `canStudentNavigate(){ return IS_TEACHER; }` 给 nextPage/prevPage 加闸门（键盘方向键、触屏滑动一并拦住）；学生端初始化隐藏 `#topNav`/`#btnPrev`/`#btnNext` |
| **F** | 教师身份无法用 URL 传递；⛔ 交付链接禁止 query | **1.5 秒内连点 3 次底部页码指示器**切换教师/学生；localStorage 记 `xmn_teacher_<NODE_ID>`；左下角「🚪 退出教师模式」；身份判定收敛到 `IS_TEACHER` + `console.log('[XMN] <课件名> v<版本> \| IS_TEACHER=' + IS_TEACHER)`；⛔ **页面内零提示**：不得出现任何「连点页码进教师模式」的浮条/toast/文案（学生看到会自行连点夺权），教师入口只靠**线下交付话术**（§4B【教师必看】第 2 条）。回归 pagesync **S13** |
| **G** | 教师纯翻页不广播 | **广播权随教师模式常驻**：connect 回调 `if (IS_TEACHER) startBroadcast();`；三连点切教师即 startBroadcast、切学生即 stopBroadcast；退出前 stopBroadcast 清 retain |
| **H** | 学生扫码跳页等 5 秒以上 | 学生 connect 成功后 `requestCurrentPage()` 发 `{req:'page'}`（300ms 首发 + 600ms 重试 ≤4 次）；教师端 message 回调识别 req **即时回播**；心跳 5s 缩 **2s** 兜底 |

**学生端导航纪律（焊死定案）**：学生端初始化即隐藏顶部菜单与翻页按钮，无任何恢复入口；仅页内逐步揭示、答题、仿真交互不受影响。底部页码指示器「1/N」**必须保留**——它是三连点进教师模式的唯一入口。⚠ **但页面不得附任何提示文案/浮条**（硬规约 #20；学生看到会自行连点夺权），提示只出现在**线下交付话术**里。

**⚠ 公共 broker 延迟（分层定位，勿把基础设施延迟当逻辑 bug）**：Node 直连同 broker 往返 ≈577ms（正常）；浏览器 wss 连公共 emqx 耗 4.9–5.9s + 跨节点消息再 5–7s——叠加即用户感知的「5 秒以上」。**大头是基础设施，代码改不动**；代码侧最优解 = 2s 心跳 + 主动请求。要亚秒级必须换低延迟 broker（平台云 MQTT / 自建 emqx）。诊断：`scripts/mqtt-latency-probe.js`。

### 2 · 二维码（本地优先）

- `#qrImg_*` 必须本地生成（`createDataURL()`）；qrserver 仅 fallback
- 时序坑与修法见 §4A.3；验收口径：线上 `#qrImg_*` 为 `data:image/...` 且长度 >500
- 判定已有图用 `getAttribute('src')`
- 若线上实测 hash 也被外壳剥离，改走 `parent.postMessage` 通道

### 3 · 全屏（v2026-09-28e 定案：默认不放按钮）

> **📌 全屏规则的单一事实来源**：以本节为唯一权威定义；SKILL.md 与 workflow-dev.md §3.6③ 中的全屏条目均为引用。

外壳无 `allow-fullscreen`，网页代码达不到 F11 式真全屏（浏览器安全边界）。**定案：新课件默认不放全屏/放大按钮**；需要时引导用户按 F11 或直开 HTML。

确需保留时三级降级（[`fullscreen-fallback.js`](../templates/fullscreen-fallback.js)，默认**不注入**）：

| 级 | 手段 | 结果 |
|---|---|---|
| ① | 自身 `documentElement.requestFullscreen()`（捕获 rejection 继续降级） | 直开 HTML = 真全屏 |
| ② | 同源 iframe 借外壳顶层文档 requestFullscreen | 桌面大概率真全屏 |
| ③ | 跨源沙箱伪全屏：`body.fs-pseudo` → `#pageContainer{position:fixed;inset:0;z-index:9999}` | 铺满网页区域（非 bug，安全边界） |

**⚠ 伪全屏必须给导航留 z-index**：`body.fs-pseudo #topNav{z-index:10001 !important}`（不透明置顶），`#navBtns`/`#mqttStatus` 10000。**禁止**半透明+hover 恢复（覆盖层拦截指针，菜单永远点不了）。

**⚠ 取消全屏按钮 ≠ 删掉伪全屏兜底 CSS**：`body.fs-pseudo …` 三条**保留**（骨架默认有），删了回归 S7 直接 FAIL；只删 `#fullscreenBtn` 三件套。

### 4 · 发布后必做（验收四件套 + 1 项人工教学核验）

1. `playwright-test.js <发布链接>`（iframe 感知，核对页数）；
2. iframe 内断 `NODE_ID / PUBLISH_BASE / SYNC_TOPIC / CLASS_ID` **四项非空且非 DEFAULT-CLASS**（只跑 audit 不够——常量为空时 audit 会漏）；
3. 断学生视角用 `getComputedStyle(el).display`（断 class 会漏）；
4. 断显隐必须带 `body.student-mode #el{display:block}` 一类**显式规则**断计算样式；
5. **人工教学核验（硬规约 #16，不做自动化——内容语义检查太脆弱）**：逐页核对① 经验锚点覆盖率（0 锚点页 = 不合格）；② 引入页形态（现象+认知冲突问题开头，非定义/公式开头，现象篇幅 ≤30%）；③ 前沿连接 ≥1 处且编织于引入/讲解/总结中（无独立页/挂件）。

### 4.5 · 部署完成交付话术（原文照写，v2026-10-02 修订）

> ⛔ **硬性禁令（2026-09-30）**：交付链接**必须是裸链** `https://workbuddy.link/p/<node_id>`，**禁止附加任何 query，尤其禁止 `?teacher=1`**。外壳 302 → iframe 白名单剥掉 query 与 hash → 教师点开仍是学生视角。模板 `_teacherByUrl` 只是本地直开调试兜底，**不得据此对外发链接**。
> ⛔ **链接书写铁律（2026-10-02 事故）**：URL 必须**独占一行**——禁止与后续文字同排、禁止紧贴 `**` 加粗符或任何标点，否则聊天端会把「，点击静态html文件无效！」整段 URL-encode 粘进链接产出坏链。
> **发消息前自检四问**：① 链接是否独占一行（且不带 query）；② 三条是否原文照写、且【教师必看】红色提示卡两种形态（独立 HTML 文件 + 聊天内 Markdown 警示块）都交付；③ 页码示例的 N 是否等于实际页数；④ Markdown 警示块是否为整条消息最后元素（其后零内容），且门控（question 工具）是否排在警示块之后的「下一轮」（禁止同轮排在警示块前，否则警示块漏发）。

**4B 部署成功后，交付消息结构（v2026-10-02 修订，含 2026-10-02 基尔霍夫交付事故修正）**：
- 正文在前（完成情况、验收结论、文件交付等），**纯文本裸链独占一行放在正文末尾**；
- **【教师必看】红色大字提示卡 = 两种形态缺一不可**：
  - **① 独立 HTML 文件（权威·可复盘）**：于课件工作目录生成 `教师必看_<课件名>.html`，内联样式把三条渲染为红色 #D93025、约 22px、加粗（font-weight:700）、浅红底框 #FCE8E6，链接用 `<a>` 可点；交付消息中给出文件路径。真实 HTML 文件，**样式 100% 保留、随时可打开复核**，不依赖聊天内联渲染。
  - **② 聊天内 Markdown 警示引用块（补充）**：`> ⚠️` 引用块内加粗，同三条原文，作消息最后一个元素。
- **⛔ 门控顺序铁律（基尔霍夫事故定案）**：`question 工具`门控**必须排在红色提示卡（①+②）发出之后的「下一轮」**，禁止与警示块同轮且排在其前——门控返回即结束当前轮，会令警示块漏发（2026-10-02 基尔霍夫课件实测：门控先发、红色框漏发）。正确顺序：本轮发正文 + Markdown 警示块 + 文件路径红色卡 → 下一轮再发门控。
- **独立 HTML 文件渲染为红色大字**：红色 #D93025、约 22px、加粗、浅红警示底框；裸链已前置到正文，**警示块之后零内容**；
- 以下三条【原文照写】，仅将 XXXX 整体替换为真实裸链（不带任何 query）：

**【教师必看】**
1、请务必点击如下链接进入课件，点击静态html文件无效！
XXXX
2、进入课件后，请第一时间在页面底部中间的页码处（如「1/13」，N 为本课件实际页数），用鼠标快速点击三次，即可成为控制端——此后您的翻页会自动同步到所有学生端！
3、学生扫码后，页面会跟随教师端的变化，且无法自行控制翻页。

学生扫码直达链接形如 `https://workbuddy.link/p/<node_id>#page=<页id>&class=<CLASS_ID>`（hash 传递）。

### 4.6 · 答题可改与导航条居中（v2026-09-29 定案）

规约：提交模式下**提交前可随时改答案**（单选改选、多选重选/重新确认），**提交后立即锁定**（防刷分）；页码与翻页键**恒在底部居中**。新课件由模板天然满足；存量课件升级共 3+2 层，缺一不可：

| 层 | 旧模式 | 新模式 |
|---|---|---|
| L1 单选 JS 闸门 | `if (container._chosen[qi] >= 0) return;` | `if (container._submitted) return;` |
| L2 多选 JS 闸门（toggle+confirm 两处） | `if (container._chosen[qi] !== null) return;` | `if (container._submitted) return;` |
| L3 选项 CSS 锁 | `.quiz-q.answered .opt{pointer-events:none}` | `.quiz-q.submitted .opt{…}` |
| L4 确认按钮隐藏 | `.quiz-q.answered .opt-confirm{display:none}` | `.quiz-q.submitted .opt-confirm{…}` |
| L5 submitQuiz 承接 | 只加 answered 类 | 必须补 `qq.classList.add('submitted');` |
| L6 导航条加固 | `#navBtns{position:fixed;…}` | 定位属性全部 `!important` |


**两个必知坑（价格理论实战）**：
- **只改 L3 不改 L4 的隐形陷阱**：多选确认后按钮被隐藏 → 重选后点不到「确认本题」。jsdom `click()` 穿透 display 测不出，**真实浏览器必现**。L3+L4 一起改，靠源码断言兜底。
- **批量替换须容忍空格差异的正则**：`if\s*\(\s*container\._chosen\[qi\]\s*>=\s*0\s*\)\s*return;` + 替换条数计数断言。

工具与验证链：

```bash
python scripts/quiz-unlock-patch.py <index.html> [more.html]     # 六层一次升级（幂等）
python scripts/quiz-unlock-patch.py --check <index.html>         # 只读体检，exit 2=待升级
python scripts/quiz-unlock-patch.py --selftest
NODE_PATH=<含jsdom的node_modules> node scripts/quiz-modify-test.js <课件.html>
python scripts/orphan-css-fix.py --check <index.html>            # 孤儿 CSS 检测/修复
```

升级后完整验证链：`quiz-unlock-patch.py` → `syntax-check.js` → `quiz-modify-test.js` → `pagesync-test-mqtt.js` → 发布 → 线上 playwright iframe 感知实测（`#navBtns` 水平居中偏差 <5px、距底 ≈20px；选 A→改 C 生效）。

---

## 4B · 发布到资料库（强制路线，禁用 CloudStudio）

**路线铁律**：只走资料库路线，产出 `https://workbuddy.link/p/<node_id>`（微信可直接打开/分享/扫码）。**禁止 `workbuddy_sites_deploy`（CloudStudio / `*.app.workbuddy.host`）**——微信内被拦截、缺鉴权与外壳。仅用户明确要 CloudStudio/局域网自测时例外。

一键脚本：[`scripts/publish_to_library.py`](../scripts/publish_to_library.py)

**发布前强制预检（2026-10-02 起）**：`python scripts/prepublish-check.py <课件.html> [--node-id <id>]` ——在本地复演线上核验标记（DEFAULT-CLASS 全文件**含注释**、`?teacher=1`、12 项标准件标记、四常量与 node-id 一致、PAGE_IDS 无重复）。**PASS 才许发布**，省一次发布+线上核验往返（2026-10-02 事故：注释里的 DEFAULT-CLASS 直到线上核验才暴露）。

```bash
# 首次发布（新建节点）
python scripts/publish_to_library.py --dir "<课件目录>" --token <op_xxx>
# 覆盖更新（⚠ 必须带 --node-id，否则新建闲置节点）
python scripts/publish_to_library.py --dir "<课件目录>" --token <op_xxx> --node-id <node_id>
# 只体检不联网
python scripts/publish_to_library.py --dir "<课件目录>" --dry-run
```

脚本六步：① 回写常量（NODE_ID/PUBLISH_BASE/CLASS_ID 派生）→ ② 打包 zip（排除 `_backup*`/`.bak`/`.md`/`__pycache__`；**index.html 必须在 zip 根**）→ ③ import_html 导入或覆盖 → ④ 解析 `KS_IMPORT_OK` → ⑤ publish_page 发布 → ⑥ 打印链接。

**必记坑表**：

| 坑 | 现象 | 正确做法 |
|---|---|---|
| 中文路径发布失败 | 发布目录含中文 → 导入整体失败 | 发布目录用**纯 ASCII 路径**（如 `C:/deploy_xxx`） |
| 重发必须带 `--node-id` | 不带 → 每次新建节点，旧链接失效 | 改动重发一律带 `--node-id` |
| `--token` 走宿主会话鉴权 | 手工传真实 token 反而暴露凭证 | 经 `library/_common.py` 走宿主 request-pipe，传占位值 `host` 即可；**绝不把 op_ token 写进脚本或提交** |
| 备份落在课件根目录 | 备份被一起打包上传 | 备份写系统临时目录（脚本已实现） |
| **首次发布后 PUBLISH_BASE 空（两步法铁律）** | 首发不回写 PUBLISH_BASE/NODE_ID → 二维码退化拼出 `nullsrcdoc` 坏码 | 任何新课件走「新建 → 拿 node_id → 带 --node-id 重发一次」两步；重发后核线上常量非空 |
| **★ 单文件回退导致线上图片全 404（2026-10-02 实测）** | zip 通道故障 → 脚本回退单 html 导入 → 只传 HTML、img/ 不随包 → 线上图片全白 | 脚本已内置 `inline_images()`：回退时自动把 `<img src>` 与 CSS `url()` 内联为 base64。**发布后必须实测**：playwright 穿透 iframe 断言所有 `<img>` `naturalWidth > 0` |

**⚠ 脚本业务失败也可能 exit 0**：必须解析 stdout 的 `KS_IMPORT_OK` 判定导入成功。手工应急两步：`python page/import_html.py <index.html> --file-name <名字.html> --node-block-id <id> --token-stdin` → `python page/publish_page.py --token-stdin --node-id <id>`。**不要**改用 `drive/upload_drive_file.py` 顶替——它建的是网盘 drive 节点（非可发布 page）。

**⚠ 片段化课件（`_build/`）常量铁律**：跑 `build.py` 会把常量复原成空串。顺序固定：写 `_build/const.json`（NODE_ID/PUBLISH_BASE）→ `build.py` → 核产物常量非空 → 再发布。

### 存量课件批量迁移（可复用流程）

写一次性脚本 `_migrate_<课>.py`，**不要手改 HTML**：
1. 备份 `deploy/index.html.bak_premig_<日期>`；
2. 从备份读入（幂等）；新增块**锚定函数声明行插入**（如 `function startBroadcast(){` 前），**禁止**长段落匹配后替换（实测连带吃掉邻接代码 → 语法错 + 回归 FAIL）；
3. 每处替换断言 `count==1`，不符即中止打印候选；
4. 删段用正则锚定唯一短标记，避开中文圈码注释（`⑩` 等字节不一致）；
5. 写完回读比对，跑 `syntax-check.js`；
6. 跑 `pagesync-test-mqtt.js` 回归，**ALL PASS 才发布**（带 `--node-id`）。

---

## 工具链速查（scripts/ 与关键模板）

| 文件 | 用途 | 何时用 |
|---|---|---|
| `templates/teaching-control.js` | A~H 标准模板（控制端唯一版：租约+遗嘱+观察态**提示窗（3 秒倒计时自动收起）**+一键接管；**页面零「连点进教师模式」提示**） | Step 4 第⑨步必注入；集成点见文件头 |
| `scripts/pagesync-test-mqtt.js` | 教学控制行为级回归（T1~T5 + S1~S19 共 40 项） | 改教学控制后必跑；迁移验收门槛 |
| `scripts/syntax-check.js` | 校验单文件 HTML 全部内联 script 语法 | 4A 每步后 / 发布前 |
| `scripts/mqtt-latency-probe.js` | MQTT 链路分层诊断探针 | 报「跳页 5 秒以上」先跑它 |
| `scripts/deploy-state-test.js` | **4A 部署态验收标准件**（结构+行为+常量+教师链路 ≈105 项，config 驱动，双模式） | 4A apply 后必跑；取代逐课现写测试 |
| `scripts/jsdom-smoke-test.js` | 免浏览器冒烟测试（≈47 项） | 发布前最后一道关卡 |
| `scripts/sync-e2e-live.js` | 线上「学生跟随」端到端实测 | 报「学生不跟随/停首页」先跑它 |
| `scripts/audit_skill_self.py` | 技能自审（母技能 MQTT 版） | 改完 SKILL.md/模板/脚本后必跑 |
| `scripts/quiz-unlock-patch.py` / `quiz-modify-test.js` | 答题可改六层升级 + 行为级测试 | 升级旧锁定课件 |
| `scripts/orphan-css-fix.py` | 孤儿 CSS 声明块检测/修复 | navBtns 挤位等 CSS 静默失效 |
| `scripts/publish_to_library.py` | 一键资料库发布 | 4B |
| `scripts/verify-library-online.js` | 线上发布态核验（穿透外壳 iframe 聚合断言） | 发布后必跑（本地四关过≠线上生效） |

> **⚠ 以下脚本属云变体技能（interactive-courseware-cloud），与母技能规约相反，勿复制**：`audit_courseware_spec.py`、`migrate_courseware_cloud.py`、`cloud_smoke_test.js`、`upsert-errorcode-test.js`、`verify_cloud_online.py`、云版 `audit_skill_self.py`。

---

## Troubleshooting Guide（症状速查）

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Mobile scan stays on cover | MQTT script blocking 或 v5 ESM | 加 `async`；钉 `mqtt@4.3.7` UMD |
| QR image doesn't appear | 用了 `qrImg.src` 判断 | `getAttribute('src')`；确认 qrcode-generator 加载 |
| QR image very slow | 海外 QR API blocked | 本地 data URI 生成 |
| Teacher stats don't update | broker 分叉（最多见）、CDN 失败、CLASS_ID 不一致 | ① 状态点绿色+两端 host 一致；② 学生 F12 有 `[MQTT] 加载成功`；③ QR URL `&class=` 与教师端一致 |
| Clear data 只清当前设备 | 只清了本机 retained | 收集全部已知 sid across ALL activities，逐 sid+activity 发空 retained |
| Detail panel 无选项条 | DETAIL_QUIZ_MAP 缺活动或 QUIZZES 未载 | 核对映射与测验 ID |
| Submit button 还是「重做」 | Step 3 逻辑未转换 | grep retryQuiz 替换为提交模式 |
| 点选项毫无反应（页面照常渲染） | 测验容器漏写 id，initQuiz 拿到 null 静默 return | 容器加 id="quizXxx"；prepublish-check 判据① 拦截 |
| 仿真页提交的数据清不掉 | 仿真弹窗缺 xmnClear 按钮（sim_popup 模板缺陷，2026-10-02 已修） | 检查 qrPopup_sim* 含 xmnClear；deploy-state-test 弹窗组拦截 |
| Page JS errors after Step 4 | 模板贴到 script 外或重复声明 | `node --check`；核对 script 闭合 |
| 清空后平均分旧值 | updateBadgeStats 缺 else 分支 | avgEl 逻辑包 `if (subs.length>0){...} else {'-'}` |
| 发布后图片全 404 | deploy/ 前缀或单文件回退未内联 | IMG_PREFIX='img/' + grep 验 0；实测 naturalWidth>0 |
| 讲授页标题消失 | teach-title 入了 revealQueue | 从队列删除，标题常驻 |
| 点击页面动画不触发 | revealQueue 未初始化 / pageEntered 守卫 | 检查 onPageEnter 是否调用 setupReveal |
| 前测涉及本课新知 | 题干/选项出现本课术语 | 对照 workflow-design.md §1.3.1 五条自检 |
| 教师端无徽章 / 出现「跟随老师」 | 教师身份未生效 | 三连点切教师；确认 `IS_TEACHER=true` |
| 教师翻页学生不跟随 | 广播权未常驻 | connect 回调 `if(IS_TEACHER) startBroadcast();` |
| 学生页面自动乱跳 | 多广播者打架 / 学生可见徽章 | 学生端隐藏徽章；SYNC_CTL_TOPIC 仲裁 |
| 跳页要等 5 秒以上 | broker 基础设施延迟 | 【H】+2s 心跳已落；仍慢换 broker |
| 诊断不跟随改代码无效 | 未分层 | 先跑 mqtt-latency-probe.js 隔离代码 vs 基础设施 |
| 全屏点不了 / 菜点点不了 | 外壳无 allow-fullscreen；伪全屏盖菜单 | 默认不放按钮；`body.fs-pseudo #topNav{z-index:10001}` |
| 发布报错 / 链接打不开 | 中文路径；未带 --node-id | 纯 ASCII 路径；带 --node-id；解析 KS_IMPORT_OK |
| `step4_inject.py --apply` 报 `[mqtt message routing] expected count 1, got 0` | mqtt-framework.js 模板已升级内置 C/D 路由与 G/H 连接逻辑，注入器补丁锚点失配（v2026-10-13 已修幂等化） | patch_mqtt/patch_tc 已改「先检测再补丁」：检测 `xmnEnterTeacherRole`/`handleSyncMessage`/`c._chosen` 已存在即跳过对应补丁；若手改旧版注入器照此办理 |
| pagesync S1 FAIL（startBroadcast 断言） | 测试断言停留在旧模板单行写法，模板已是 `if(IS_TEACHER){ setTimeout(...xmnEnterTeacherRole...) }` 双形态（v2026-10-13 已修） | S1 断言正则兼容双形态；prepublish-check G 项同步改双选正则 |
| 冒烟测试 mid3/quizMid3 FAIL | 模板默认 ACTIVITY_QUIZ_MAP 含 mid3，课件测验数≠5 套时误报（v2026-10-13 已修） | build_js_block 一律按 step4.json 配置精确发射映射，不再保留模板默认值；新增课件只需核对配置 |
| `verify-library-online.js` 报 `Cannot find module 'playwright'` | 脚本 require playwright，managed node workspace 未进解析路径 | `NODE_PATH="C:/Users/jowa/.workbuddy/binaries/node/workspace/node_modules"` + managed node 绝对路径重跑（勿 pip/npm install 全局） |
| 人工核验锚点全 FAIL（疑似内容缺失） | step2 设计页码 1-based（p1=封面）与 HTML 页码 0-based（p0=封面）差 1 位，且锚点常由相邻页承载（前测页承载全课锚点词） | 核验前先建映射表 step2 pN → HTML p{N-1}；按页切分取纯文本后逐页判读，勿盲信关键词表 |
