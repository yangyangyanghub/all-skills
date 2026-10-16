# Pitfalls · 坑表全集（附录 A/B/D 合编）

> 由 SKILL.md 外迁。**执行时按需查阅**；20 条最高频坑（即 SKILL.md 硬规约速查表）已内联，此处是全集。
下方 A2~A5 为同属「A」的子表：
> - A · Common Pitfalls（症状 → 修复）
> - B · Full Checklist（全流程总览，交付前复核）
> - D · Template Synchronization Checklist（改模板后必查）

---

## A · Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Canvas CSS vars don't work | Use hex values (`'#FF8F00'`) directly |
| Particles overlapping | Calculate by actual radii + gap |
| State jump (no animation) | Use `requestAnimationFrame` |
| Canvas click offset on mobile | Scale coords with `getBoundingClientRect` |
| Inline onclick in innerHTML breaks | Use `addEventListener` |
| Pre-test tests new content | 前测只测已有经验，不测未学知识。**绝对禁止**在题干/选项/答案中使用本课术语（如矩阵课用「系数方阵」作答案）。设计方法：先列本课核心概念 → 反推已有经验 → 设计对应前测题。题干情境还须取自学情画像经验域（四要素④，喜闻乐见）。见 workflow-design.md §1.3.1 |
| 手机端页码被通信状态/背景图盖住，教师点不到控制端入口 | 页码指示器必须恒在顶层：`#navBtns`/`.qr-badge` z-index **500**、`#mqttStatus`/`#teacherExit` 降 **250**（v2026-10-13 实测 `#mqttStatus` 原 2900 盖住导航）。移动端通信状态上移 `bottom:84px`、揭示提示条 124px；页面内容元素 z-index ≤99。层级表见 workflow-dev.md §3.6④；回归 deploy-state-test 三条 z-index 断言 |
| 非测验页（首页/讲授页）没有二维码，迟到学生无法当场扫码加入 | 每页徽章制（v2026-10-13）：build_body 解析全部 page section 注入徽章——活动页带 `data-activity`，其余页无该属性走 `openJoinPopup`（共用 `#qrPopup_join`，二维码按 data-page 动态重建、禁用 src 缓存）。加入弹窗无统计故免 `xmnClear`；回归 deploy-state-test「每个页面均有 QR 徽章」+「加入徽章弹出加入弹窗」 |
| 每页徽章「首屏不显示（含首页加入徽章）/ 回访徽章停在上一页」 | 两个必守点位（v2026-10-13，gene-protein 实测 `加载后 (none)`、`回访 p1 显示 p5`）：① onPageEnter 的 toggle 必须插在函数**开头**（`if(pageEntered[id])return;` 守卫**之前**），插在末尾会被守卫拦截 → 回访错显；② 徽章 HTML 追加在 `</body>` 前（晚于初始 showPage），加载时 onPageEnter 查不到 → 必须 **DOMContentLoaded** 后再同步当前页徽章（build_js_block 的 `_xmnBadgeSync`），否则首屏无徽章。回归 deploy-state-test 两断言（部署态：仅首页 ON / 回访切回；未部署：0 枚 ON） |
| 情境与知识「两张皮」/为情境而情境/课件变讲故事/前沿做成独立页 | 硬规约 #16：① 经验锚点是每页必填项，0 锚点页 = 不合格；② 现象导入单页 ≤30% 篇幅，随即进入知识本身（经验是入口、知识是目的地）；③ 禁杜撰假情境（"小明"式）；④ 悬念/认知冲突当模块内解开；⑤ 前沿连接编织进引入/讲解/总结，禁独立页或挂件卡。配套：学情画像（§1.1）+ 经验域库 [`experience-anchors.md`](experience-anchors.md) |
| Quiz double-submit | `_submitted` guard + button disabled |
| 同一测验内正确答案全集中在同一选项位置（如「全 A」） | 硬规约 #19（防呆）：同一测验（前测/各中测/后测各算一个）内，正确答案不得全部集中在同一位置；多选题也不得每题都含同一位置。出题时**主动打散选项顺序并同步改 `answer`**（多选为数组）。出题后**必须**跑 `node scripts/quiz-answer-check.js <课件.html>` 须 `RESULT: PASS`（FAIL=某测验单选答案 100% 同位置；WARN=高占比 ≥80% 或多选每题均含同一位置）。案例：`double-integral` 19 题全 A。见 workflow-design.md §1.3.2 规则三 |
| IMG_PREFIX 残留 `deploy/` 前缀导致发布后图片 404 | `var IMG_PREFIX = 'img/';` + 全局替换 `src="deploy/` → `src="img/` + grep 验证 0 残留 |
| MQTT retain accumulates | Always provide "clear data" button |
| 多人进入后学生端闪跳（多广播源打架） | 闪跳唯一必要条件=**存在第二个广播源且两端不同页**。四类来源：教师第二设备（曾连点过→localStorage 永久教师身份）/ 机房残留教师身份 / 并行课堂 / 学生误入。**控制端唯一**方案（2026-10-12 定案）：租约制（`CLAIM_TTL=6000` 心跳续租、**在位者优先**、仅失联超时或带 `force` 的显式接管才易主）+ MQTT 遗嘱（崩溃/关页即释约）+ 观察态横幅 + 一键接管。⛔ **禁用「最新 ts 恒赢」**——双端各 2s 心跳必然心跳级易主=确定性振荡。集成点⑦ `xmnConnect` 回填 `myClientId`(=clientId)+`will`。回归 pagesync **S15~S18**。详见 workflow-deploy.md §4A.2 / 【C】 |
| 页面浮现「连点页码 3 次进教师模式」提示 → 学生照做**夺取控制端权限** | 硬规约 #20：页面内**零**此类提示（含 `xmnTeacherHint` 浮条 / toast / 文案），**任何时刻都不得出现**；教师入口只靠**线下交付话术**（§4B【教师必看】第 2 条）。多端抢控制权时的观察态提示窗须带 **3 秒倒计时**（含「接管控制」按钮，超时自动收起、不夺权）。回归 pagesync **S13 / S19**。2026-10-14 定案 |
| Variable scope bug | Shared data → module-level `var` |
| Canvas draw function deleted | Never mass-delete; one-at-a-time removal |
| Edit deletes global utility functions | After any edit that replaces a code block, verify `drawArrow`, `drawLabel`, `drawDashedLine` still exist — shared by ALL Canvas pages |
| MQTT CDN v5 breaks entire page | Always use `mqtt@4.3.7` (UMD build) + `async`。v5 ESM kills JS; blocking script freezes mobile on slow networks |
| MQTT broker 两端分叉导致数据不同步 | 手机和电脑必须连同一 broker。必须按 CLASS_ID 确定性选 broker：`MQTT_BROKER_INDEX = hash(CLASS_ID) % len`（`xmnBrokerHash`），优先 `broker-cn.emqx.io`，重试环形切换 `(idx+1) % len`。详见 workflow-deploy.md §4A.2 |
| Mobile QR stuck on cover, can't flip | MQTT script tag is blocking — add `async` |
| QR `<img src="">` never generates | Browser resolves `element.src` to current page URL when attribute empty. Use `getAttribute('src')`, not `.src` |
| QR image API slow / blocked in China | Generate QR locally with `qrcode-generator` data URI; fallback to image API only if library fails |
| Teacher stats don't update after phone submit | 最可能根因是 broker 两端分叉（见上）。其次：1) `submitQuiz` 未写本地 `xmnAgg`；2) CLASS_ID 不一致；3) 学生端 MQTT CDN 加载失败。排查顺序：MQTT 状态点颜色 → F12 控制台 → workflow-deploy.md 排错指南 |
| Clear data without confirmation | 优先 `showConfirmModal`（`mqtt-framework.js` 内置；iframe 沙箱常禁原生对话框），缺失时才退回 `confirm()` |
| Clear data only clears current activity | `xmnClear` must iterate `Object.keys(ACTIVITY_QUIZ_MAP)` and clear every quiz activity's `xmnAgg`, `localStorage`, retained MQTT messages, and UI state |
| Clear data doesn't clear other students | Collect all known `sid`s across ALL activities, publish empty retained message for every `sid`+activity combination |
| Step 4 only deploys, skips HTML mods | Step 4 = 4A (modify HTML) + 4B (deploy)。「部署」= 完整 4A+4B |
| Post-test still has retry button | Submit mode: 所有有 QR 的测验页改提交按钮+去重做。`grep retryQuiz` 确保无残留（Step 4 范围） |
| QUIZZES 缺失测验页导致 initQuiz 报错 | `QUIZZES` 必须包含 `ACTIVITY_QUIZ_MAP` 中全部测验 ID（缺项则该页 `QUIZZES[quizId]` undefined 报错、测验全挂）。分数元素 ID 由 `quizScoreId()` 动态生成，无需手工 scoreMap |
| MQTT CDN unpkg.com 在中国网络不可达 | 单一 unpkg 在移动/4G 常超时。必须多源 fallback：jsdelivr → fastly.jsdelivr → unpkg。见 workflow-deploy.md §4A.2 代码 |
| 图片全部堆在页面底部 | 有图有文页面禁止图片堆底。宽幅信息图→紧跟段落全宽居中；机制图→`.fig.float-l/r` 浮动并排；每图配 caption。见 workflow-design.md §2.3.3 |
| AI 生成图片含英文解释/标注 | 除英语课外，AI 生图内文字必须 100% 纯中文（含装饰性英文也不行）。提示词显式声明；生成后逐图检查，发现即重生成 |
| 清空数据后平均分未重置 | `updateBadgeStats` 必须给 avgEl 加 else 分支重置为 `'-'`（subs.length=0 时也更新） |
| 点「清空数据」确定后毫无反应（静默失效） | `showConfirmModal` 确认回调必须传参：`onOk && onOk(true)`——调用方 `xmnClear` 是 `function(ok){ if(ok) xmnClearDo(...) }`，不传参则 ok 恒 undefined，清空永不执行。**不得同时注入两份 `showConfirmModal`**（teaching-control 自带版必须删）。验收必须真机走完「弹窗→确定→归零」全程。回归：pagesync S14 |
| 图片路径含 deploy/ 前缀 | 发布后 zip 根平铺无 deploy/ 目录。IMG_PREFIX='img/'，发布前 grep 验 0 残留 |
| 揭示动画顺序混乱 | setupReveal 数组严格按阅读顺序（第1段→第2段→…，图片按版面位置参与排序） |
| teach-title 被隐藏等待揭示 | 标题常驻，不加入 revealQueue |
| 内容动画无脑全开 | 只对讲授页配置 `setupReveal`；测验/仿真/封面页直接可见；总结页用框架内置交互 |
| 图片与图注分离揭示 | `<img>` 与 caption 用 `<div class="reveal-img-group">` 包裹，一步揭示 |
| prevReveal 回退后 typewriter/数字滚动残留 | `prevReveal` 必须清 `.count-num`（归零+清 data-counted）和 `.typewriter`（中断 `_twTimer`）。setInterval 存到 `span._twTimer` |
| 键盘箭头在测验/仿真页报 TypeError | 无 reveal 队列时 `pageRevealQueues[pid]` undefined。键盘处理先 `typeof` + `&&` 短路检查 |
| 点击图片放大不响应 | 三重根因：① `.reveal-hidden.reveal-done` 缺 `pointer-events:auto`；② reveal 点击器未排除 `tag === 'IMG'`；③ 灯箱内图片 `stopPropagation` 阻止关闭冒泡 |
| 总结页未选框架，仍用旧版要点卡片 | Step 1 必须输出「总结页框架推荐」给用户确认；Step 3 从 summary-vN 模板复制 |
| 总结页宽度受 max-width 限制 | 统一 `width:100%;max-width:none`（4 套模板已内置） |
| 封面页翻走后不消失 | `display:flex` 必须写为 `.page.active .cover-page`（级联选择器）。**禁止写 `.cover-page.active`**——showPage() 只给 `<section class="page">` 加 active，嵌套元素永远没有该类 |
| 点「清空数据」弹窗被关闭 | 清空按钮 onclick 只调 `xmnClear('xxx')`，**不要追加 closeQRPopup** |
| 总结页字号太小 | 标题/关键字 ≥24px bold，正文 ≥20px |
| 扫码跳转被初始封面覆盖 | URL 跳转 IIFE 执行后末尾 `showPage(0)` 把它覆盖。修复：跳转统一放脚本末尾合并执行——`var _p=getPageParam('page'); var _i=(_p&&PAGE_IDS.indexOf(_p)>=0)?PAGE_IDS.indexOf(_p):0; showPage(_i);`。**禁止 URL 跳转后再单独 `showPage(0)`** |
| 浮动图被揭示文字框背景盖住（揭示后"有时"消失） | 揭示动画末帧保留 transform 使元素永久建立堆叠上下文，块级背景画在浮动图之上。修复：`.fig.float-r/.float-l{position:relative;z-index:5}`。**不要**用 `transform:none` 覆盖（会破坏滑动动画） |
| 课件需要图像却未询问来源、直接默认生成乱扣费 | 硬规约 #18：非知识图表类图像**必须弹 question 工具交互选择**——**复选**来源类别（搜索网络图片 / 内联 SVG 手绘 / AI 生图，**可多选**）。勾「AI 生图」走 image-service 技能。知识图表类恒走内联 SVG、不进弹窗。默认兜底=三项全允许，须声明 |
| 「内联 SVG」被误当 Canvas / 场景图被要求用 SVG | 术语澄清：**内联 SVG = `<svg>` 标签手绘矢量图**（零成本、不支持写实场景）；**Canvas（`<canvas>`+JS）= 可交互数学模型图**（§1.5 五类图片 b 类）。二者不同技术，勿混称「canvas 画 svg」；写实/场景图必须走 AI 生图或网络图片 |
| 勾「AI 生图」却因未配置 API 导致生成失败/静默空白 | 生图前先自检 image-service 的 `config/settings.json` 是否已配置（只判存在、不回显密钥）；未配置则引导用户填入 OpenAI 兼容图像 API 地址与密钥。**密钥只存该配置文件，禁止写进课件 HTML / 课件 JS / 任何随课件分发的文件** |
| 把生图密钥写进 SKILL.md / config.json / 随技能分发 | 硬规约 #18：密钥一律存环境变量（Windows `setx DUOMI_API_KEY`）；技能文件、config.json、课件 HTML 内**不得出现任何明文密钥**；发布会把技能外泄 |
| 封面背景图 404 导致封面破损 | 三层 background 优雅降级：`linear-gradient(暗化遮罩), url(主视觉), linear-gradient(主题兜底)` + `background-size:cover,cover,cover`。见 workflow-dev.md §3.1.1 |
| 知识理解图做成纯文字海报 | 提示词显式要求 infographic 形态（图文结合、文字精简）+ 英文撰写 + 声明图内文字全中文 |
| 发布目录含中文导致整体失败 | 发布目录用**纯 ASCII 路径**（复制到 `C:/deploy_xxx` 等）。不要指望工具链兼容中文路径 |
| 重发未带 `--node-id` 导致闲置节点 | 改动重发一律带 `--node-id <原 id>`，链接不变 |
| 教师身份/壳内 URL 参数不可靠 | 外壳 302→iframe 白名单剥掉 query 与 hash → `?teacher=1`/`#teacher=1` 失效。教师身份走三连点 + localStorage；⛔ **对外交付链接一律裸链**。学生手机扫码直开属另一场景（hash 可解析） |
| 二维码内容为 `nullsrcdoc?page=...` 坏码 | 预览面板 srcdoc 沙箱下 `location.origin` 为 `"null"`。QR 地址一律走 `getQrBase()`：`PUBLISH_BASE` 优先 → http(s) 且 origin!=='null' 时回落 `origin+pathname` → 否则提示「请先发布」，绝不生成坏码 |
| 学生扫码直达靠 hash 参数 | QR 链接一律 hash 传递 `#page=<页id>&class=<CLASS_ID>`；`getPageParam` 按 hash → search → parent（try/catch 抗跨域）解析 |
| 教师端出现「跟随老师」按钮 / 徽章不显示 | 教师身份未生效。三连点页码指示器切教师模式；控制台确认 `IS_TEACHER=true` |
| 教师翻页学生不跟随 | 广播权未常驻。`connect` 回调 `if(IS_TEACHER) startBroadcast();`（§G） |
| 学生扫码进入后跳页要等 5 秒以上 | ① 纯被动等心跳；② 公共 emqx 浏览器 connect 4.9–5.9s + 跨节点再 5–7s。先落【H】主动请求 + 2s 心跳；仍慢 = broker 基础设施延迟，换低延迟 broker |
| 为「学生不跟随/跳页慢」反复改代码无效 | 未分层定位。先 Node 直连探针（`mqtt-latency-probe.js`）测往返（正常 ≈0.5s）；代码对而端到端慢 = broker 问题 |
| 关二维码弹窗后同步静默断掉 | `closeQRPopup` 里调了 `stopBroadcast()`。教师端关弹窗**不停广播** |
| 伪全屏后顶部菜单被盖住、点不了 | `#pageContainer` 铺满 + `#topNav` 半透明 hover 恢复 → 覆盖层拦截指针。正确：`body.fs-pseudo #topNav{z-index:10001}` 不透明置顶；禁止半透明+hover |
| Edit 工具假报成功、改动没落盘 | 每次 Edit 后必须 Grep 复核目标标记；批量修改用脚本直改 + 回读比对 |
| `build.py` 复原常量导致线上 SYNC_TOPIC 退化 | 片段化课件顺序固定：写 `_build/const.json` → `build.py` → 核产物常量非空 → 再发布 |
| 资料库 zip 导入通道故障 | zip 报「上传凭证响应缺少 uploadUrl 或 cosKey」时，脚本自动降级单 html 直传（已内联图片为 base64）。**含 img/ 多文件时降级即内联**；发布后必须实测 `naturalWidth > 0` |
| 发布导入报「上传凭证响应缺少 uploadUrl 或 cosKey」→ 线上仍是旧版本 | 后端按扩展名分流：`.zip` → drive 通道（无 cosKey）→ import_html.py 只实现 cos 分支 → 报错；且失败也 exit 0。脚本已内置单文件回退。**不要**改用 `drive/upload_drive_file.py` 顶替（建的是网盘节点非 page） |
| 迁移漏补 `getPageParam`、仍直读 `location.search` | 全部 `new URLSearchParams(location.search)` 直读替换为 `getPageParam(key)`（含 `?page=` 跳转 IIFE）；替换后课件内 `new URLSearchParams` 计数必须为 0；发布后 `verify-library-online.js` 复核线上真身 |
| 模板自带原生 `confirm()`/裸 `scrollIntoView` | iframe 沙箱可禁原生对话框 → 确认静默失效；缺 `scrollIntoView` → showPage 初始化抛错、脚本块后半段全不执行。三模板已修；勿从 2026-09-29 前旧课件复制这三段 |
| 答题锁定升级漏层（L4 确认按钮陷阱） | 只改 L1~L3/L5 漏 L4（`.quiz-q.answered .opt-confirm{display:none}`）→ 多选重选后点不到「确认本题」；jsdom `click()` 穿透 display 测不出。用 `quiz-unlock-patch.py` 六层一次升级 + `quiz-modify-test.js` A3/A4 源码断言兜底 |
| 批量替换锁定代码时静默漏改（空格差异） | 用容忍空格的正则 `if\s*\(\s*container\._chosen\[qi\]\s*>=\s*0\s*\)\s*return;` + 替换条数计数断言 |
| jsdom 断言 CSS 的两个假象 | ① `getComputedStyle` 可能抛异常/样式表解析失败；② `element.click()` 穿透 `display:none`。CSS 断言直接扫 HTML 源码；真实渲染用 playwright 兜底 |
| 孤儿 CSS 声明块静默吞掉下一条规则 | 删元素只删选择器行、留裸声明块 → CSS 解析器把后续规则并成无效规则整体丢弃 → navBtns 挤左下。删 CSS 按完整规则删；受害课件用 `orphan-css-fix.py`；验收必测 navBtns 计算样式 `position==fixed` |
| 末页芯片写成 `chip-end` 缺 `chip` 类 | 绑定与高亮选择器都是 `#topNav .chip`。写 `class="chip chip-end"`；验收用 `querySelectorAll('#topNav .chip[data-page="N"]')` 精确断言（`class="chip` 子串计数会误判 OK） |
| 分页引擎当前页变量漏 `var` | `curPage = i;` 漏 var → 严格模式 ReferenceError → 广播页码 undefined → 学生不跳页但 toast 照弹。必须 `var curPage = 0;`；沿用旧名（如 cur）补桥接 `window.xmnCurIndex = function(){ return cur; }` |
| 发布常量固化点搞错 | 片段化课件常量唯一固化点 = `_build/const.json`；4A 注入发生在 build 之后，改 build.py 产出无效 |

---

## A2 · Silent-Failure Class（静默失效类 · 2026-10-02 提炼，共性=语法全绿但功能已死）

| 坑 | 症状 | 根因 | 拦截 |
|---|---|---|---|
| **测验容器漏 id** | 页面渲染/翻页/语法全正常，点选项毫无反应 | `initQuiz` 的 `getElementById` 返回 null 直接 return；骨架复用时 `<div class="quiz-page">` 不带 id | prepublish-check 判据①（QUIZZES 键↔id）；deploy-state-test B 组 |
| **仿真弹窗缺清空按钮** | 仿真页提交的数据永远清不掉，教师端无感知 | step4_inject 的 sim_popup 模板原本只给二维码不给 xmnClear（2026-10-02 已修模板+回填产物） | prepublish-check 判据②；deploy-state-test 弹窗组 |
| **QR 恒走远端** | 扫码图慢/不可达（国内 qrserver 慢），本地库永不生效 | qrcode-generator async 引入而 toggleQRPopup 同步调库；库就绪后 src 非空 | qr-badge-injection.js 模板已内置「本地优先+轮询换码+data-qrdone」（2026-10-02 起） |
| **注入器锚点失配** | probe 报 retry btn MISS ×N | 旧正则要求 class 与 onclick 紧邻，按钮多写 type="button" 即失配（已放宽为属性无关） | step4_inject.py 2026-10-02 起容忍任意属性顺序 |

## A3 · Math-Statement Class（数学表述类 · 2026-10-02 提炼，共性=前两层测试全绿、数学验证层才抓得到）

| 坑 | 实例 | 规约 |
|---|---|---|
| **抽屉数与结论强度不匹配** | 「6 人中必有两人距离小于 1 米」——6 米路分 6 段时 6 人 6 抽屉原理失效；且抽屉法只能给「不超过段长」，等距摆放时距离恰为 1，「小于」不成立。正解：6 人站 5 米路 → 分 5 段 → 距离 ≤1 | 凡带「<」「至少」「必有」的命题，必须同时核「抽屉数够不够」与「下界是否取得到」 |
| **蒙特卡洛无法证伪必然性** | 5000 次随机全成立 ≠ 必然成立（连续分布随机点几乎必有近邻） | 证伪必然性必须用**构造性反例**（本题：6 米路等距 1.2 摆放即反例），不能用随机模拟 |
| **把平均当下界** | ⌈20/6⌉ 答成 3 或 3.33 | 下界=上取整；干扰项设计保留这两个经典误答 |

> 每课数学验证件（`_math-verify.js`）三件套：① 大样本随机验「下界不被违反」+ 验「界紧可达」（slack=0）；② 最坏策略步数恰等于公式值；③ 关键常数逐一对账（组合数/概率解析式）。

### A4 · 拼装式开发（分片源文件 + assemble 脚本）专属坑 —— 2026-10-02《n 维向量空间》实战

| Pitfall | Fix |
|---------|-----|
| **母技能模板里的示例代码造成重复定义** | `page-flip-system.js` 带示例 `PAGE_IDS=['p0'..'p3']` 与 `PAGE_LABELS`，`quiz-engine.js` 带示例 `QUIZZES{quizPre 2题}` 且末尾 `Object.keys(QUIZZES).forEach(initQuiz)`。**后定义的会静默覆盖真数据**（页面数变 4、题目变 2）。assemble 脚本必须正则剔除三处：示例 PAGE_IDS/PAGE_LABELS、示例 QUIZZES、末尾 initQuiz 调用 |
| **配置块排在框架 JS 之后 → 整页白屏（致命）** | `page-flip-system.js` 末尾**立即**执行 `showPage(_initIdx)`。若 `PAGE_IDS` 定义在其后，`PAGE_IDS.length` 读 undefined 的 length 直接抛错。**唯一正确顺序**：① 本课配置（PAGE_IDS/PAGE_LABELS/QUIZZES）→ ② 框架 JS → ③ 本课仿真/回调 → ④ reveal 引擎 + `xmnBoot`（DOMContentLoaded 后统一 `initQuiz` + `showPage(_initIdx)`，URL 跳页仍生效） |
| `scan_braces.py` 把 CSS 当 JS 扫 → 假报 MISMATCH | 自写只取 `<script>…</script>` 段的括号检查；**先跳注释再跳字符串**（JS 注释里常有引号、括号、`<script>` 字面量） |
| 重写 `onPageEnter` 时漏掉 `pageEntered` 页面级守卫 | 漏掉后重进同一页会重跑 `setupReveal`，**把教师已逐条揭示的内容重新隐藏**。课件自己实现的 `onPageEnter` 首两行必须是 `if (pageEntered[id]) return; pageEntered[id] = true;` |
| **函数实参比形参多一个 → Canvas 画出 `undefined`** | 给内部函数加参数（如给 `panel()` 增 `names`）后，调用点遗留的多余实参会**静默错位**：`names=0`（falsy）走默认值、`names=1` 则 `names[0]` 为 undefined 并被 `fillText` 画到画布上。**改函数签名后必查全部调用点的实参个数**。Canvas 文字错位肉眼极易漏（截图缩放会掩盖负号/细字），**须用 `ctx.fillText` 打桩捕获参数序列核对** |
| **线性代数课件：判「是否在张成空间内」靠解方程组，公式写错静默失效** | 2×2 求解写成 `(2b₁−g₁b₀)/det` 之类看似合理的式子，回代才发现不成立。正解 λ=(b₀g₁−g₀b₁)/det、μ=(2b₁−b₀)/det。**验收必须做「解回代原方程」的全参数穷举自检**，不能只验独立实现 |
| 仿真观察要点写出数学上不可能的操作 | 例：二维中两个不共线向量已张成**整个平面**，却让学生「把 β 拖到张成区域之外」——该操作不存在。**写观察要点前先确认该状态在参数空间内可达**（无解只在 det=0 即两向量共线时才出现） |
| 自检脚本判定「某调用是否存在」必先剥 JS 注释 | 母技能文件注释里全是示例代码（`submitQuiz(`、`mqtt`、`initMatching` 等），不剥注释判定必假失败。判定元素存在性用原始 HTML，判定调用存在性用剥注释后的代码 |

### A5 · 数学表述类坑（数学自证层专属）—— 只有「纯数学自证」能抓

| Pitfall | Fix |
|---------|-----|
| 题目解析里的**秩**算错 | 断言「三个向量线性无关，秩=3」前必须实算。实例：(1,0,1),(0,1,1),(1,1,2) 实测秩=2（第3 = 第1+第2） |
| 换基坐标算错 | 断言「f=(1,1),(1,−1) 下 (3,−1) 坐标变 (1,−2)」——实测 (1, 2)。回代 1·(1,1)+2·(1,−1)=(3,−1) ✓ |
| 「全体二次多项式」这类选项表述有歧义 | 含零多项式时它是子空间，不是不空间。须改为「**次数恰好为 2** 的所有实系数多项式」 |
| 静态测试与行为测试都抓不到「数学表述错误」 | 必须加**第三层纯数学自证**：题库逐题用独立实现重算 + 页面所有算例回代 + 定理反向构造（如「n+1 个向量必相关」显式造非平凡零组合）。**答案索引须运行时从课件 `QUIZZES` 读取，零硬编码** |
| jsdom 断言 reveal 可见性用错方法 | 骨架机制是 `reveal-hidden` 与 `reveal-done` **共存**，由 CSS `.reveal-hidden.reveal-done{opacity:1;pointer-events:auto}` 提亮。断言须用 `classList.contains('reveal-done')`，**不是** `!contains('reveal-hidden')` |


## B · Full Checklist（交付前总览复核）

> 执行时用各 Step 的细化清单；交付前用本总览复核。两处不一致时以 Step 细化版为准。

**Phase 1: Framework**
- [ ] Step 0 教学环节已确认（question 工具复选：内容讲解/互动测试/互动仿真）
- [ ] Modules, page list, quiz plan, simulation plan, image plan
- [ ] **图片来源已弹窗确认**（question 工具复选类别：网络图/SVG/AI 生图；硬规约 #18；知识图表类除外）
- [ ] 勾「AI 生图」时：image-service `config/settings.json` 已确认配置（未配置则已引导）
- [ ] User confirms framework；总结页框架推荐已给用户确认

**Phase 2: Detail**
- [ ] Per-page designs with wireframes, text, images, interactions
- [ ] Simulation specs using template
- [ ] Infographic prompts：image-service 路径写中文即可，末尾声明 ", all Chinese text labels" 与规则D 句
- [ ] [规则D] 知识理解类生图均为信息图形态；提示词含显式声明图内文字全中文
- [ ] 生图统一走 image-service，方案表「生图引擎」列已填 `image-service`
- [ ] 每张图已定布局（宽幅→全宽居中 / 机制图→浮动并排）
- [ ] 图片逐张验证（数值、箭头、文字准确；含中文字图用 image-service OCR 校验）
- [ ] User confirms detailed design

**Phase 3: Development**
- [ ] Copy courseware-skeleton.html as starting point
- [ ] Fill PAGE_IDS, PAGE_LABELS, nav chips（末页芯片 `chip chip-end`）
- [ ] Copy page-flip-system.js, quiz-engine.js（+用到的 matching-quiz.js）
- [ ] All quiz HTML + QUIZZES data
- [ ] **答案位置分布合规**（硬规约 #19）：`node scripts/quiz-answer-check.js <课件.html>` 须 `RESULT: PASS`；命中则逐题打散 `answer` 后复跑
- [ ] Canvas 三要素同步（canvas id ↔ drawXxx ↔ onPageEnter）
- [ ] All `<img src>` 用 `img/` 前缀，grep `src="deploy/` = 0
- [ ] 每个讲授页 setupReveal，全部内容元素入队（标题除外），严格阅读顺序
- [ ] 测验/仿真/封面页不启用揭示
- [ ] 图文混排：非堆底、浮动图 `.clearfix` 包裹、每图 caption
- [ ] 移动端 390×844 验证通过
- [ ] 灯箱 CSS+HTML+JS 就位
- [ ] 键盘揭示优先 → 翻页回退，短路检查防 TypeError
- [ ] 总结页从 summary-vN 模板复制（100%宽、字号达标、不用 setupReveal）
- [ ] JS 语法 0 错误（syntax-check.js），所有页面渲染正常
- [ ] Step 3 交付顺序：正文 → 审阅提醒 → Markdown 警示引用块（最后元素，其后零内容）→ 门控置于下一轮（⛔ 禁止同轮把 question 工具门控排在警示块前，否则门控返回结束本轮、警示块漏发）

**Phase 4: Deployment**
- [ ] MQTT `mqtt@4.3.7` UMD + async + 多源 fallback
- [ ] `xmnBrokerHash(CLASS_ID)` 确定性选 broker，环形切换，优先 broker-cn.emqx.io
- [ ] `submitQuiz` 先写本地 `xmnAgg` 再 publish
- [ ] QR badges on ALL quiz + simulation pages
- [ ] **页面零「连点进教师模式」提示**（硬规约 #20）：grep 无 `xmnTeacherHint`/「连点 3 次」文案；观察态提示窗带 3 秒倒计时（pagesync **S13/S19** PASS）
- [ ] QR 本地生成（qrcode-generator data URI）
- [ ] 前测已核查（题干无本课术语等五条）
- [ ] ALL quiz pages submit mode + 去重做按钮（Step 4 范围）
- [ ] detail-stats.js + 每个 QR 弹窗「查看每题详情」按钮（v2026-10-13：选项统计为视觉重点，选项文字改**悬停浮窗** `.opt-tip`；已删「参与人数」「正确率」；bar 高 18px）
- [ ] 清空数据：确认弹窗（回调传 true）+ 清全部活动 + 清全部 sid + avgEl 重置 '-'
- [ ] 教学控制标准件 A~H 七集成点注入 + pagesync-test-mqtt.js ALL PASS
- [ ] 发布到资料库（publish_to_library.py，重发带 --node-id）
- [ ] 发布后验收四件套 + 线上图片 naturalWidth > 0 + verify-library-online.js
- [ ] Step 4 交付顺序：正文（含裸链独占一行）→ 生成 `教师必看_<课件名>.html`（交付消息给路径）→ Markdown 警示引用块三条（最后元素，其后零内容）→ 门控置于下一轮（⛔ 禁止同轮把 question 工具门控排在警示块前，否则警示块漏发）

---

## D · Template Synchronization Checklist（改模板后必查）

- [ ] `CLASS_ID` 只在 `mqtt-framework.js` 定义一次；`qr-badge-injection.js` 直接复用
- [ ] `ACTIVITY_QUIZ_MAP` 单一事实来源在 `mqtt-framework.js`；`unified-quiz-submit.js` / `detail-stats.js` 通过 `typeof ACTIVITY_QUIZ_MAP !== 'undefined'` 复用
- [ ] `detail-modal.html` 关闭按钮 class 与 `detail-stats.js` 一致（`detail-close-btn`）
- [ ] `detail-stats.js` 的 `.opt-tip` 悬停浮窗依赖 `detail-modal.html` 里 `.bar-row{position:relative}`；旧 `.opt-text` 常驻行必须已移除（否则重复显示、白占高度）
- [ ] `qr-badge-injection.js` 用 `getAttribute('src')` + 本地 QR 生成
- [ ] `qr-badge-injection.js` toggleQRPopup 为「本地优先+轮询换码+data-qrdone」版（2026-10-02 起，勿回退为纯同步版）
- [ ] `unified-quiz-submit.js` 先写 `xmnAgg` 再 `xmnPublish`
- [ ] All templates assume single-file HTML with inline CSS/JS（CDN 除外）
- [ ] 坑表、模板注释、模板行为三者同步
- [ ] `quiz-engine.js` has `isSubmitMode = false`（Step 3 default）with clear Step 4 change comment
- [ ] `quiz-engine.js` 单选/多选闸门为 `if (container._submitted) return;`（无旧锁残留）
- [ ] 答题锁定 CSS 全部挂 `.submitted` 前缀；submitQuiz 内每个 `answered` 后紧跟 `submitted`
- [ ] `courseware-skeleton.html` 的 `#navBtns` 定位属性带 `!important` 加固
- [ ] `QUIZZES` keys cover all quiz IDs in `ACTIVITY_QUIZ_MAP`
- [ ] `retryQuiz` retained in quiz-engine.js but marked "Step 3 only; Step 4 must remove"
- [ ] `xmnClear` iterates `Object.keys(ACTIVITY_QUIZ_MAP)`（清全部活动）
- [ ] `step4_inject.py` 的 `quiz_popup` 与 `sim_popup` 均含 `xmnClear` 按钮 + `qrPart_*` 读数（sim_popup 2026-10-02 起对齐，勿回退）
- [ ] `step4_inject.py` retry 按钮正则为属性无关版（容忍 class/onclick 之间夹任意属性）
- [ ] `updateBadgeStats` 含 avgEl else 分支重置 '-'
- [ ] `canvas-engine-patterns.js` 通用工具函数与领域示例函数分区明确（领域示例标注「须替换」）
- [ ] `simulation-patterns.md` uses function-based JS (no ES6 class/arrow functions)
- [ ] `page-templates.html` 与 skeleton 的 CSS class 匹配
- [ ] `playwright-test.js` 为完整可运行脚本
- [ ] skeleton 含完整 24 动画 CSS + revealQueue 引擎 + 提示条 UI
- [ ] 所有 setupReveal 序列严格 DOM 顺序；teach-title 不入任何队列
- [ ] 图+caption 用 `.reveal-img-group` 包裹
- [ ] `SYNC_TOPIC` 保持派生式 `'xmn-sync/' + (NODE_ID || CLASS_ID)`；发布脚本只回写 NODE_ID/PUBLISH_BASE，不改写 SYNC_TOPIC
- [ ] `CLASS_ID` 为派生式 `getPageParam('class') || 'wb-' + NODE_ID`，全文件（**含注释**）无 `'DEFAULT-CLASS'` 字面量——注释里写了该词也会被线上核验判 FAIL（2026-10-02 事故，现由 prepublish-check 发布前拦截）
- [ ] `NODE_ID` / `PUBLISH_BASE` 初始为空串，发布脚本回写，发布后非空
- [ ] 跳页修复八项齐备（A~H）
- [ ] 答题可改六层齐备（L1~L6）；清空数据须同时清 `submitted` 类
- [ ] 发布后实测线上图片 `naturalWidth > 0`
- [ ] 教师身份判定收敛到 `IS_TEACHER` + `[XMN] ... IS_TEACHER=` 诊断日志
- [ ] 默认不含全屏按钮；伪全屏 CSS 中 `body.fs-pseudo #topNav{z-index:10001}` 保留
- [ ] 发布走资料库路线（publish_to_library.py → workbuddy.link/p/<node_id>），无 CloudStudio 残留
- [ ] 发布后完成验收四件套
- [ ] `teaching-control.js` 模板与已发布课件实现保持同步（以线上验证版为准互填）
- [ ] `pagesync-test-mqtt.js` 对本技能产出的课件 ALL PASS（40 项）
- [ ] `syntax-check.js` 纳入 4A.6 推荐执行方式
- [ ] 母技能 scripts/ 与云变体 scripts/ 互不复制（云版 audit/migrate/verify 系列规约相反）
