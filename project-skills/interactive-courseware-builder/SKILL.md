---
name: interactive-courseware-builder
version: "1.6.0"
description: |
  交互式单文件 HTML 课件制作全流程：教学设计 → 线框 → HTML 开发（翻页系统、
  测验、Canvas 仿真、信息图）→ MQTT 学生扫码互动 → 资料库发布。AI 生图统一走
  image-service 技能。Use when 用户提到：课件、交互式课件、HTML课件、互动教学、
  课堂答题、互动仿真、做课件、interactive courseware、teaching courseware。
  不负责：普通网页/前端开发、PPT 幻灯片（走 html-ppt-gen）、独立信息图（走 image-service）。
---

# Interactive Courseware Builder

Build production-ready interactive courseware as a **single HTML file** — from
instructional design to deployed classroom tool.

> **Design philosophy**: 「骨架不变，内容可填」— infrastructure (page-flip, navigation,
> responsive CSS, quiz engine, MQTT) is locked down in `references/templates/`;
> only content changes per courseware.

---

## ⚠️ 硬规约速查（20 条，加载后必须执行，不可跳过）

| # | 规则 | 违规后果 |
|:--:|------|----------|
| 1 | 讲授页标题（`teach-title`）**禁止加入 reveal 队列**——进入页面即见 | 标题被隐藏，学生不知当前主题 |
| 2 | 测验页/仿真页/封面页**禁止调用 `setupReveal`**——内容直接可见 | 破坏答题/仿真交互、进度感知 |
| 3 | MQTT CDN **必须钉 `mqtt@4.3.7`（UMD）+ `async` + 多源 fallback** | v5 ESM 导致全页 JS 崩溃；手机扫码卡封面 |
| 4 | **AI 生图统一走 `image-service` 技能**（`core/text_to_image.py` 等），禁止调用其他生图引擎、禁止把 API 密钥写进课件 HTML / 技能文件；执行细节见 workflow-design.md §2.3 | 引擎混乱、密钥泄露 |
| 5 | 有图有文的页面**禁止图片堆底部**——宽幅全宽居中、机制图浮动并排 | 图文脱节，教学效果差 |
| 6 | **Step 4 = 4A（改 HTML）→ 4B（部署），不可只做 4B** | 学生扫码后无提交按钮、无 QR 徽章 |
| 7 | Canvas 三要素同步：`<canvas id>` ↔ `drawXxx()` ↔ `onPageEnter` 调用 | Canvas 白屏、仿真不运行 |
| 8 | `submitQuiz` **先写入本地 `xmnAgg`，再 `xmnPublish`** | MQTT 延迟/丢包→教师端看不到数据 |
| 9 | 前测题目**只考已有经验、暴露前概念**——绝不出现本课任何新术语/新概念 | 前测变成「教新课」而非「摸底」 |
| 10 | MQTT broker 必须按 CLASS_ID **确定性选择**（`xmnBrokerHash`），禁止两端各自独立 fallback | 手机/电脑落到不同 broker→数据永不同步 |
| 11 | **图片全屏灯箱**：所有课件图片必须支持点击放大/再点击收回（骨架已内置） | 教学图片无法细看 |
| 12 | **总结页必须从 4 套框架选 1 套**（V1 全景关系图/V2 链式问题/V3 双栏知识树/V4 模块卡片），不再用旧版要点卡片。见 [workflow-dev.md 总结页](references/workflow-dev.md) | 总结页缺乏结构化交互 |
| 13 | **Step 0 教学环节选择不可跳过**：question 工具**复选（multiple: true）**问「您需要哪些教学环节？」——内容讲解 / 互动测试 / 互动仿真（封面+总结恒有）；用户已指定则跳过；「全自动执行」或无效选择 → **三项全选** | 课件缺环节或页面构成错误 |
| 14 | **AI 生成图片内文字必须 100% 纯中文**（英语课除外），杜绝任何装饰性英文 | 中英混杂干扰理解 |
| 15 | **AI 生图的知识理解图必须是信息图形态**（图文结合、文字精简、忌纯文字海报）；提示词须显式声明「图内文字全部简体中文」 | 纯文字海报、图内中文乱码 |
| 16 | **经验锚点与情感连接**：每课件 Step 1 必须产出「经验-情感主线」+ 学情画像；**每页 ≥1 个经验锚点**（学生已知/可感/关心的具体事物或现象）；全课件 ≥1 处前沿连接——**编织进引入/讲解/总结，禁做独立页或挂件**（2026-10-12 定案）；引入页禁止定义/公式开头；举例与巩固题情境须取自经验域；禁杜撰假情境。细则见 [workflow-design.md](references/workflow-design.md) §1.1/§1.2.1/§2.1.1~§2.1.3 | 情境与知识两张皮、为情境而情境、课件变讲故事 |
| 17 | **Step 3 静态产物零二维码徽章**：不得含 `.qr-badge` 元素/加入弹窗/`_xmnBadgeSync`/`IS_DEPLOYED` 闸门（均属 Step 4 注入专属）；只需保证 `#navBtns{z-index:500}`（页码恒顶层）。见 Step 3 段 | 静态页误导扫码；与 Step 4 注入冲突 |
| 18 | **图片来源弹窗（单阶段）**：课件需要图像时，**必须用 question 工具弹交互选择**——**复选（multiple: true）**允许的来源类别：搜索网络图片 / 内联 SVG 手绘 / AI 生图（**可多选、允许混用**）；勾「AI 生图」→ 直接走 **image-service**（本地已配置，无需选引擎）；**知识图表类恒走内联 SVG（规则0），不进弹窗**；生图前确认 image-service 的 `config/settings.json` 已配置 | 图片来源不明、乱扣费 |
| 19 | **答案位置分布防呆**：同一测验（前测 / 各中测 / 后测**各算一个测验**）内，**正确答案不得全部集中在同一选项位置**（典型：全 A / 全 B）；多选题也不得每题都含同一位置。出题后**必须**跑 `node scripts/quiz-answer-check.js <课件.html>` 须 `RESULT: PASS`；命中则**逐题打散选项顺序并同步改 `answer`** 后复跑。见 [workflow-design.md](references/workflow-design.md) §1.3.2 规则三 | 学生看出规律「全蒙 A 即满分」，测验失去甄别力 |
| 20 | **页面零「教师入口」提示 + 观察态提示窗 3 秒倒计时**：① 任何页面内 UI（浮条/toast/banner/文案）**一律不得**出现「连点页码进教师模式」类提示——学生看到会自行连点夺取控制端权限；教师入口只靠**线下交付话术**（§4B【教师必看】第 2 条）。② 多端抢控制权时弹**观察态提示窗**：含「接管控制」按钮 + **3 秒倒计时**，3 秒内不接管则自动收起（不夺权）。回归 pagesync **S13 / S19** | 学生自行获得控制端权限、课堂翻页混乱 |

完整坑表（80+ 条症状→修复）见 [`references/pitfalls.md`](references/pitfalls.md)。

---

## ⚡ 加载完成 · 必须告知（首次交付总结原样包含）

**① 告知话术（原样发送）**：
> 每当课件需要图像时，我会请您在「允许的图像来源类别」中**勾选**（**可多选**）：① 搜索网络图片（零成本，真实照片/真实场景）② 内联 SVG 手绘（零成本、自包含、中文精确，但不支持写实/场景图）③ AI 生图。
> 若勾选了「AI 生图」，我直接调用本机已配置的 **image-service** 技能生成（文生图引擎 + 中文文字渲染优化，无需额外开通任何平台）。

**② 费用**：内联 SVG / 网络图片 = 零成本；AI 生图按 image-service 所配 API 计费（费用以服务方为准，生成前告知）。图片来源的选择见 [workflow-design.md §2.3](references/workflow-design.md)；**知识图表类恒走内联 SVG（规则0），不受弹窗影响、零成本**。

---

## 🧩 环境依赖说明（OpenCode 适配版）

| 依赖 | 范围 | 说明 |
|------|------|------|
| **image-service 技能** | AI 生图（Step 1/2/3） | 本机 `.opencode/skills/image-service/`，配置在 `config/settings.json`；OCR 校验也走它 |
| **question 工具** | 全部用户门控 | OpenCode 内置交互组件，替代原 AskUserQuestion |
| **Node.js + Python3** | 脚本验收 | syntax-check / quiz-answer-check（Node）；publish / step4_inject / prepublish-check（Python） |
| **WorkBuddy 资料库 token** | **仅 4B 发布** | `publish_to_library.py --token <op_xxx>` 需要 WorkBuddy 开放平台 token；**Step 0~3 + 4A 完全不依赖 WorkBuddy**。仅做静态课件或本地部署时可跳过 4B，交付物为单文件 HTML |

---

## 🚪 门控总表（渐进披露——先读对应文件再动手）

| 时点 | 必读 | 内容 |
|------|------|------|
| Step 1/2 开工前 | [`references/workflow-design.md`](references/workflow-design.md) | 框架+详细设计全量细则（页面规划/测验分布/前测四要素/题型/五类图片五条规则/仿真模板/**图片来源弹窗（类别复选）**/image-service 生图路径/图文混排/**学情画像/经验-情感主线/经验锚点/引入页三要素/前沿连接编织式/应用真实化**） |
| Step 1 学情画像与锚点设计时 | [`references/experience-anchors.md`](references/experience-anchors.md) | 学段×学科经验域种子表 + 选用规则 + 红线（硬规约 #16 配套资料库） |
| Step 3 开工前 | [`references/workflow-dev.md`](references/workflow-dev.md) | 开发全量细则（骨架/配置块/版芯/自检表/交付纪律/渐进呈现/灯箱/总结页4框架） |
| Step 4 开工前 | [`references/workflow-deploy.md`](references/workflow-deploy.md) | 部署全量细则（4A九步注入/MQTT坑/QR坑/标准件A~H/发布坑表/验收/排障） |
| 任何时候排查坑 | [`references/pitfalls.md`](references/pitfalls.md) | 坑表全集 + 全流程清单 + 模板同步清单 |
| 配色/交互/仿真参考 | [`color-schemes.md`](references/color-schemes.md) / [`interaction-catalog.md`](references/interaction-catalog.md) / [`simulation-patterns.md`](references/simulation-patterns.md) | 6 配色 / 49 种交互（8 类） / 5 仿真模式 |

**门控是硬性的**：未读对应文件不得开始该 Step；本文件只保留骨架与铁律，细节一律以上表文件为唯一事实来源。

---

## 📍 进度指示与执行纪律

- 每次回复以 `📍【Step N/4 · Step Name — N.m Substep】` 开头；结尾「现在完成了 X，下一步做 Y。」
- **每个 Step（Step 0~4 全部，无一例外）结尾都必须提供显式用户确认门控**，且门控**必须用 question 工具（交互式选择组件）实现**——**禁止用纯文本提问、口头询问代替组件**（2026-10-02 抽屉原理课件复盘：Step 3 用文字问确认属违规）。如果用户明确要求采用“全自动模式”，可合并为一次总确认，但**绝不静默跳过**。
- Code edits：一次改一个函数，改后 `node scripts/syntax-check.js <课件.html>` 验证；替换代码块后确认全局工具函数（`drawArrow`/`drawLabel`/`drawDashedLine`）仍在。
- 交付话术是 verbatim-only：Step 3 警示句与 Step 4 三条教师须知必须**逐字原文**、红色大字号警示框，不得改写缩写。
- Bug 修复后**立即回填模板**；改任何模板后跑 pitfalls.md 附录 D 同步清单 + `python scripts/audit_skill_self.py`。

---

## Step 0 — Teaching-Elements Selection（教学环节选择，硬规约 #13）

用 **question 工具（`multiple: true` 复选）** 询问「**您需要哪些教学环节？**」，三个复选框：

| 复选框 | 对应页面类型 |
|--------|------------|
| ☑ 需要内容讲解 | `teach`（讲授页） |
| ☑ 需要互动测试 | `pre-test` / `mid-test` / `post-test` |
| ☑ 需要互动仿真 | `sim`（Canvas 仿真页） |

- **封面页（`cover`）+ 总结页（`summary`）恒有**，不入选项、不可取消。
- **勾选项 → 页面构成**：勾「内容讲解」出 teach 页；勾「互动测试」出测试页；勾「互动仿真」出仿真页；**不勾某环节则不出该类页面**。

| 组合（勾选内容） | 页面构成 | 裁剪要点 |
|------|---------|---------|
| 讲解+测试+仿真（**全勾，默认**） | 全类型 | 无裁剪 |
| 测试+仿真（不勾讲解） | 无 teach 页 | 仿真页承担测验间隔职能；前测=摸底+直接探究；reveal 规则自动失效；中测通常 1 个 |
| 仅仿真（只勾仿真） | cover/sim×N/可选简化 summary | 无测验页（MQTT 仍可用）；仿真页数不限；总结页用 V1 单页版；每仿真页附 3–5 行观察要点 |

流程：用户已指定环节/前置传入 → 跳过询问；未指定 → question 工具（文案含默认兜底说明「30 秒内未选择默认方案：三项全选」）；跳过/取消/回复「继续」等无效选择 → **三项全选**（等价旧「模式1」）并声明；「全自动」→ 直接三项全选并开场声明。
确定后输出确认：`📍 已选教学环节：内容讲解 / 互动测试 / 互动仿真（N 项）+ 页面构成影响`，然后进 Step 1。

---

## 4-Step Workflow（骨架）

### Step 1 — Framework Design → 读 [workflow-design.md](references/workflow-design.md)

产出框架级设计：① 基本信息（学科/主题/年级/课时）+ **学情画像**（学生经验域清单 + 情感激发候选，经 [experience-anchors.md](references/experience-anchors.md) 自动生成，门控时请用户确认/替换）；② 模块与页面规划（3–6 模块、全 10–18 页、仿真 1–3 个、页面列表表格**含「经验锚点」列**）+ **经验-情感主线表**（硬规约 #16）；③ 测验系统（1 前测+N 中测+1 后测；**相邻测验严禁连排**；**只用选择题**；前测四要素）；④ 仿真计划；⑤ 图片计划（**先用 question 工具弹窗定来源：复选类别——搜索网络图片 / 内联 SVG 手绘 / AI 生图（可多选）**；勾「AI 生图」→ 直接走 image-service，见 §2.3；再按五类图片+规则0/A/B/C/D 落表）；⑥ 配色（默认 Deep Blue `#1A3A5C`）；⑦ **总结页框架推荐**（V1~V4 选 1，给用户确认）。→ **用户批准门控**。

### Step 2 — Detailed Design → 读 [workflow-design.md](references/workflow-design.md)

产出逐页设计：每页 = 线框（ASCII）+ 全部文字 + 图片（来源/提示词/尺寸/位置）+ 交互（≥1个/页）+ 仿真 spec（8 字段模板）+ 测验全题（**正确答案位置须在各选项间打散、分布合规——硬规约 #19，出题后跑 `quiz-answer-check.js` 须 PASS**）；**每页必填「经验锚点」与「情感触发器」，引入页按三要素设计（硬规约 #16）；全课件含 ≥1 处编织式前沿连接；后测含 ≥1 道真实情境迁移题**。数据准确性强制（事实数字须可靠来源）；每张图逐张验证，错即重生成。→ **用户批准门控**（ 门控形式为question 工具，文案含默认兜底说明「30秒内未选择默认方案1」）。

### Step 3 — HTML Development → 读 [workflow-dev.md](references/workflow-dev.md)

从 `references/templates/courseware-skeleton.html` 复制起步（含全部 CSS/翻页/测验引擎/reveal/灯箱），页面从 `page-templates.html` 复制改数据。关键铁律：

- `getPageParam` 为 URL 参数唯一入口（禁止 `new URLSearchParams(location.search)`）
- `var curPage = 0;` 固定命名（旧名须桥接 `window.xmnCurIndex`）
- `IMG_PREFIX='img/'`；`grep 'src="deploy/'` 必须 0 残留
- 版芯占满 100% 宽高，内容多纵向滚动，严禁横向拉伸/缩小版芯
- 默认不放全屏按钮（F11 引导）；伪全屏兜底 CSS 三条保留
- 完成后跑 §3.7 质量自检全表 + ≥1 轮修复验证

**⚠ Step 3 交付纪律**：静态 HTML 不支持扫码互动。**交付消息顺序（硬性，不得调换）**：① 正文（完成情况/验收结论/文件清单/修复记录）→ ② 「先审阅再 Step 4」提醒 → ③ **红色警示块（Markdown 引用块 + 加粗，警示句原文照抄）作为整条消息的最后一个元素——警示块之后不得再有任何文字、门控或链接** → ④ **用户批准门控（question 工具）置于「下一轮」**（⛔ 见下方「门控顺序铁律」——本轮发完警示块即结束，门控必须下一轮发，否则警示块漏发）。警示句**必须原文照抄、一字不改**，放在 `> ⚠️` 引用块内加粗，禁止改写、缩写或替换为自拟话术（2026-10-02 抽屉原理课件复盘教训）。警示句原文照抄：

**「⚠ 当前生成的是静态 HTML 文件，不支持学生扫码互动！若要支持学生扫码答题与实时统计，必须执行 Step 4（4A 改 HTML + 4B 部署）。」**

 **用户批准门控**：Step 3最后需提供**用户批准门控**（门控形式为 **question 工具 组件**，文案含默认兜底说明「30秒内未选择默认方案1」；**禁止用纯文本提问代替组件**）。⛔ **门控顺序铁律（基尔霍夫事故定案）**：门控须排在红色警示框之后的「下一轮」，禁止同轮排在红框前——门控返回即结束当前轮，会令红框永不渲染。

- ⛔ **Step 3 产物零二维码徽章（硬规约 #17）**：静态 HTML **不得含** `.qr-badge` 元素/加入弹窗/`_xmnBadgeSync`/`IS_DEPLOYED` 闸门 —— 二维码徽章是 **Step 4 专属**，由 `step4_inject.py` 注入时生成。禁止「先埋进静态页再用闸门藏起来」。Step 3 只需保证 `#navBtns{z-index:500}`（页码恒顶层，属导航层）。徽章规范见 workflow-deploy.md §4A.3。




### Step 4 — Student Interaction & Deployment → 读 [workflow-deploy.md](references/workflow-deploy.md)

**Step 4 = 4A（改HTML）→ 4B（部署），用户说「部署」即完整 4A+4B。**

**4A 九步注入**（详见 workflow-deploy.md 注入顺序表）：**首选 `python scripts/step4_inject.py --config step4.json --html <课件> --probe` 探针全 OK 后 `--apply`**（模板件+7 集成点已固化，函数边界由 `scan_braces.py` 定位，写盘自动括号复扫、失败回滚；每课只写活动清单小 config；hand-wired 仅兜底）。九步：① CDN（MQTT@4.3.7 async 多源 + QR@1.4.4）→ ② mqtt-framework（改 ACTIVITY_QUIZ_MAP）→ ③ isSubmitMode=true、删 retryQuiz 调用 → ④ unified-quiz-submit → ⑤ 提交按钮+分数 → ⑥ **每页 QR 徽章**（活动页带统计弹窗 + 非活动页「加入」徽章/共用加入弹窗）+详情面板 → ⑦ detail-stats+badge刷新 → ⑧ **`scan_braces.py` BALANCED** + syntax-check 0 err → **⑨ teaching-control 标准件（7 集成点）+ 必跑 `pagesync-test-mqtt.js` ALL PASS**。

**4B 资料库发布**（唯一路线，禁 CloudStudio）：**发布前必跑 `python scripts/prepublish-check.py <课件.html> [--node-id <id>]` PASS**（本地复演线上标记：DEFAULT-CLASS 含注释、?teacher=1、标准件标记、四常量一致——省一次发布往返）。发布：`python scripts/publish_to_library.py --dir <目录> --token host`（无本地图片自动跳过 zip 尝试直走单文件）；新课件**两步法**：新建拿 node_id → 带 `--node-id` 重发一次（否则 PUBLISH_BASE 空产出坏码）；重发必带 `--node-id`；发布目录**纯 ASCII**；解析 `KS_IMPORT_OK` 判成功；单文件回退时核图片 `naturalWidth>0`。

**发布后验收四件套 + 1 项人工教学核验**：① playwright 页数核对；② 四常量（NODE_ID/PUBLISH_BASE/SYNC_TOPIC/CLASS_ID）非空且非 DEFAULT-CLASS；③ `getComputedStyle` 判学生视角；④ 显式规则断显隐；⑤ **人工教学核验（硬规约 #16）**：逐页核对经验锚点覆盖率（0 锚点页=不合格）、引入页形态（现象+冲突问题，非定义/公式开头）、前沿连接 ≥1 处且编织于引入/讲解/总结中。再跑 `verify-library-online.js` 核线上真身。

**⛔ 交付铁律（2026-09-30）**：交付链接**一律裸链** `https://workbuddy.link/p/<node_id>`。教师端**唯一入口 = 裸链打开后 1.5 秒内连点底部页码指示器 3 次**。

**⛔ 链接书写铁律（2026-10-02 事故）**：URL 必须**独占一行**——禁止与后续文字同排、禁止紧贴 `**` 加粗符或任何标点，否则聊天端会把「，点击静态html文件无效！」整段 URL-encode 粘进链接产出坏链。

**4B 成功后交付消息结构（v2026-10-02 修订，含基尔霍夫交付事故修正）**：① 正文（完成情况/验收结论/文件交付/纯文本裸链独占一行）在前；② **【教师必看】红色提示卡两种形态缺一不可**：先生成独立 HTML 文件 `教师必看_<课件名>.html`（红 #D93025/22px/加粗/浅红底框，交付消息中给出文件路径，样式 100% 保留可复盘），再在聊天内发 **Markdown 警示引用块**（同三条原文，作为整条消息最后元素）；③ **⛔ 门控顺序铁律**：question 工具验收门控**必须排在红色提示卡之后的「下一轮」**，禁止同轮排在警示块前（门控返回即结束当前轮，警示块漏发——2026-10-02 基尔霍夫课件实测）。口诀：本轮 正文 → 红色提示卡(文件路径+警示块) 收尾；下一轮再发门控。

**渲染规格（【教师必看】红色警示卡）**：OpenCode 聊天无法渲染自定义颜色/字号 HTML，两条路并行——① 独立 HTML 文件保留原始红色大字样式（权威形态）；② 聊天内用 Markdown 引用块（`> **⚠️ ...**`）呈现三条原文（补位形态）；裸链已按①要求放在警示块**之前**（正文末尾，独占一行），保证可点击可复制；**警示块之后不得再出现纯文本裸链或任何话术**。


三条文本【原文照写】，仅将 XXXX 替换为真实裸链：

> **【教师必看】**
> 1、请务必点击如下链接进入课件，点击静态html文件无效！
> https://XXXX
> 2、进入课件后，请第一时间在页面底部中间的页码处（如「1/13」，N 为本课件实际页数），用鼠标快速点击三次，即可成为控制端——此后您的翻页会自动同步到所有学生端！
> 3、学生扫码后，页面会跟随教师端的变化，且无法自行控制翻页。

---

## 模板与工具清单

**templates/**（复制不改为主）：`courseware-skeleton.html`（起步骨架）· `page-templates.html`（各页型模板）· `page-flip-system.js`（翻页+getPageParam，最先复制）· `quiz-engine.js`（测验引擎）· `matching-quiz.js`（连线/分类巩固题）· `canvas-engine-patterns.js`（绘图工具）· `infographic-generator.js`（生图提示词规则）· `summary-v1~v4-*.html`（总结页4框架）· Step 4 注入件：`mqtt-framework.js`（含 showToast/showConfirmModal/updateBadgeStats，唯一一份）· `unified-quiz-submit.js` · `qr-badge-injection.js` · `detail-modal.html` + `detail-stats.js` · `teaching-control.js`（A~H 标准件，第⑨步必注入）· `fullscreen-fallback.js`（默认不注入）

**scripts/**（执行/验收）：`publish_to_library.py`（4B 发布）· `syntax-check.js`（语法）· `pagesync-test-mqtt.js`（教学控制回归 40 项：含 S13 零连点提示 / S19 观察态 3 秒倒计时）· `jsdom-smoke-test.js`（免浏览器冒烟）· `verify-library-online.js`（线上核验）· `sync-e2e-live.js`（跟随端到端）· `mqtt-latency-probe.js`（延迟分层诊断）· `quiz-unlock-patch.py` + `quiz-modify-test.js`（答题可改升级+测试）· `quiz-answer-check.js`（**答案位置分布防呆校验**，硬规约 #19：同一测验内答案全集中即 FAIL）· `orphan-css-fix.py`（孤儿CSS修复）· `audit_skill_self.py`（技能自审）

> ⚠ 云变体技能（interactive-courseware-cloud）的 audit/migrate/verify 系列脚本规约与母技能相反，勿互相复制。

**references/**：四张「文件清单表」的分工——Step 3 起步看 §3.2 门控、模板总表看 templates/ 清单、知识库文档看 references/ 清单、可执行工具看 scripts/ 清单，四表互补不重复定义，新增文件登记到对应表即可。本目录含门控表所列 4 个 workflow/pitfalls 文件 + `color-schemes.md` / `interaction-catalog.md` / `simulation-patterns.md` / `animation-rules.md` + **`experience-anchors.md`（学段×学科经验域种子表，硬规约 #16 配套）** + `templates/`。
