# DESIGN.md — B2B SaaS 后台仪表盘

> **Style Reference 路径**：用户未指定品牌或 UI Kit，本文按"干净专业"语义方向生成。  
> 不抓取 Linear / Vercel / Stripe 的具体色值或 Logo，只复用其设计语言（信息层级、密度、留白）。  
> 所有色值、字号、间距均为本次设计的原创 token。

---

## 1. Visual Theme

- **Design Intent**: 为企业客户构建的**已认证后台仪表盘主视图**（非营销页）。传达三件事——**信息密度高、可信赖、不喧宾夺主**。整体调性偏"基础设施感"：像 IDE、像运维面板、像电子表格，而不是像消费级 app。
- **Style Keywords**: `clean` · `information-dense` · `restrained` · `neutral-dominant` · `engineered` · `zero-decoration`
- **Reference Notes**:
  - 受 Linear / Vercel Dashboard / Stripe Dashboard / Datadog 等 B2B 工具的"内容优先"语言启发
  - **明确避免**：Tailwind 默认 indigo（`#6366f1`）、紫→蓝双色渐变、emoji 图标、圆角卡 + 彩色左边条、装饰性插画、虚拟数据（"10× faster" / "99.9% uptime"）
  - **不做**：营销首页那种 hero + features + pricing 序列。本文档只覆盖一个 app shell 视图 + 主仪表盘

## 2. Color Palette

**Palette structure（按像素占比分配）**：
- Neutrals 占比 85% · Accent 占比 8% · Semantic 占比 5% · Effect < 1%

### Token 定义（CSS 变量形式，色值待与品牌对齐）

| Token | Light 角色 | 色值 | 用途 |
|---|---|---|---|
| `--bg` | 全局背景 | `#fafafa` | 画布底色（非纯白，避免眩光） |
| `--surface` | 卡片/面板表面 | `#ffffff` | 卡片、表格、弹层 |
| `--surface-2` | 次级表面 | `#f4f4f5` | hover 态、嵌套容器、表格斑马行 |
| `--fg` | 主要文字 | `#111111` | 标题、正文 |
| `--fg-muted` | 次要文字 | `#52525b` | 辅助说明、占位、label |
| `--fg-subtle` | 三级文字 | `#a1a1aa` | 禁用、placeholder |
| `--border` | 默认边框 | `#e4e4e7` | 1px 描边 |
| `--border-strong` | 强调边框 | `#d4d4d8` | 表格内边、聚焦容器 |
| `--accent` | 唯一强调色 | `#0f766e` (teal-700) | 主要 CTA、关键状态高亮、聚焦环 |
| `--accent-fg` | 强调色上的文字 | `#ffffff` | 按钮文字、激活 tab 文字 |
| `--success` | 成功 | `#15803d` | 成功状态、在线指示 |
| `--warn` | 警告 | `#a16207` | 待处理、过期提醒 |
| `--danger` | 危险 | `#b91c1c` | 失败、删除确认 |
| `--focus-ring` | 键盘聚焦环 | `rgba(15,118,110,0.4)` | focus-visible 外环 |

### Usage Rules

1. **Accent 配额**：每屏 `--accent` 可见使用 **≤ 2 处**。典型组合 = 1 个主 CTA + 1 个选中态 tab / 高亮 KPI。**禁止**全屏高亮、禁止"凡 primary 都涂强调色"。
2. **Link 处理**：若同屏已有 `--accent` CTA，则链接降级为 `--fg` + 下划线，避免与 CTA 抢焦点。
3. **状态色**：`--success` / `--warn` / `--danger` **只用于语义场景**（操作结果、徽章、状态指示）。**禁止**作为装饰色或 hover 态。
4. **对比度门槛**（强制门禁）：
   - 正文（≤16px）在 `--bg` / `--surface` 上 ≥ **4.5:1**
   - 大字（>18px 或 14px 粗体）≥ **3:1**
   - UI 控件（按钮、输入框边框、图标）相对相邻表面 ≥ **3:1**
5. **暗色主题**：待 v2 提供。当前仅 light，但所有 token 必须以 CSS 变量引用，方便未来切主题。

> 详见 `references/craft/color.md` 的 4 层结构 + accent 配额 + 暗色 token 规范。

## 3. Typography

### Type System（type scale = 1.25 倍数，6 个尺寸）

| Role | Size (px) | Line-height | Letter-spacing | Weight | 用途 |
|---|---|---|---|---|---|
| Display | 32 | 1.1 | `-0.02em` | 590 | 仪表盘顶部欢迎语（极少用） |
| H1 | 24 | 1.2 | `-0.015em` | 590 | 视图标题 |
| H2 | 20 | 1.25 | `-0.01em` | 590 | 区块标题 |
| H3 | 16 | 1.4 | `-0.005em` | 550 | 卡片标题、表格列头 |
| Body | 14 | 1.5 | `0` | 400 | 正文、表单输入、表格内容 |
| Small | 13 | 1.5 | `0.01em` | 450 | 辅助说明、label、meta |
| Caption / All caps | 11 | 1.4 | `0.08em` | 550 | 区块 eyebrow、表头小标签 |

> Display/H1/H2 用**负字距**（标题压紧），Caption/全大写用**正字距 ≥ 0.06em**（全大写必加 tracking，否则就是 AI slop）。  
> 详见 `references/craft/typography.md` 的 letter-spacing 强规则。

### Font Guidance

- **Display + UI 一体**：`Inter` 是**最后选择**（默认 AI 字体），本设计改用 **`IBM Plex Sans`** 作主字体，理由：(1) 几何但保留工程感，(2) 与表格/数字搭配时有 monospace 旁支，(3) 数字 `0`/`O`/`1`/`I` 区分度高，更适合 B2B 仪表盘。
- **数字 / 表格 / 代码**：`IBM Plex Mono`（同一家族，覆盖 monospace 需求）
- **不使用 emoji 字符**作为 UI 文字（包括 `·`、`→` 之外的所有 unicode emoji）
- **Fallback 链**：`'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif`

### Text Rules

1. **三权重体系**：`400` (Read) / `550` (Emphasize) / `590` (Announce)。**避免** 700+ 加粗——通常意味着其它权重没拉够。
2. **行长**：正文最长 **65ch**（`max-width: 65ch`）；表格列不设行长限制。
3. **数字对齐**：表格数字列统一 `font-variant-numeric: tabular-nums`，右对齐。
4. **All caps 强制**：`text-transform: uppercase` 必须配 `letter-spacing: 0.06em~0.1em`，缺一即视为缺陷。

## 4. Components

### 4.1 核心组件清单

| 组件 | 关键变体 | 关键状态 |
|---|---|---|
| Button | primary / secondary / ghost / danger | default / hover / active / focus / disabled / loading |
| Input | text / number / search / password | default / focus / error / disabled |
| Select | single / multi | default / open / disabled |
| Data Table | sortable / paginated / selectable rows | loading / empty / error / partial |
| Card | flat / bordered / interactive | default / hover (interactive only) |
| Sidebar Nav Item | default / active / hover | — |
| Tab | underline / pill | default / active / hover |
| Modal | sm / md / lg | open / closing |
| Toast | success / warn / danger / info | 4s 自动消失，可手动关闭 |
| Skeleton | text / row / card | — |
| Empty State | illustration-less + single CTA | — |
| Pagination | numbered / load-more | — |

### 4.2 状态覆盖

数据驱动型 UI 必须覆盖：`loading`（skeleton，非 spinner 铺满）/ `empty`（一句话 + 一个 CTA，不放图）/ `error`（含 retry）/ `partial`（部分加载成功）。  
详见 `references/craft/state-coverage.md`。

### 4.3 Behavior Notes

- **Button primary** = `--accent` 实心 + `--accent-fg` 文字。**每屏最多 1 个**。
- **Card**：默认 `bg=--surface`，`border=1px --border`，`radius=6px`（**不**用 12-16px 大圆角）。**绝不**用"圆角卡 + 彩色左边条"组合——那是 AI dashboard tile 的标志。
- **Table**：行高 40px；hover 行 `bg=--surface-2`；选中行左侧 2px `--accent` 边（**不**是彩色左边条，而是选中态标识）。
- **Icon**（详见 §7）：统一 1.6px stroke monoline，16/20/24 三档。

## 5. Layout

### 5.1 页面结构（App Shell）

```
┌─ Top bar（56px，高 56，bg=--surface，border-bottom=1px --border）
│  ┌── 左侧：Logo（24px 高）+ Workspace Switcher
│  ├── 中部：Search trigger（⌘K 占位，placeholder="Search…"）
│  └── 右侧：Notifications icon + Avatar dropdown
│
├─ Sidebar（240px，可折叠到 56px icon-only，bg=--surface，border-right=1px --border）
│  ├── Nav items（每项 36px 高，左侧 2px 选中条）
│  └── 底部：User card + Help link
│
└─ Main canvas
   ├── Breadcrumb（H3，--fg-muted）
   ├── Page H1（24px，--fg）
   ├── Action bar（右上角，水平排列）
   └── Content area（max-w 1280px，水平 padding 32px）
```

### 5.2 Spacing System

- **基础单位**：4px（不引入 8/16 进制争议，直接用 4 倍数）
- **Token**：`--s-1=4px` / `--s-2=8px` / `--s-3=12px` / `--s-4=16px` / `--s-5=24px` / `--s-6=32px` / `--s-7=48px` / `--s-8=64px`
- **常用**：
  - 组件内 padding：`12px` 或 `16px`
  - 区块间距：`24px` 或 `32px`
  - 页面边距：桌面 `32px` / 平板 `24px` / 手机 `16px`
- **栅格**：12 列，gutter 24px，max-w 1280px
- **对齐**：所有元素左对齐于 8px 基线网格；右对齐仅用于数字列

### 5.3 Content Flow

- **首屏优先级**：H1 → 一行描述 → KPI 行 → 主表格/主面板
- **阅读路径**：从左到右、从上到下。Sidebar 永远固定，**不**因滚动消失。
- **关键路径**：主 CTA 放右上角 action bar；次要操作放行内（"Edit" / "View"），用 `--fg-muted` ghost button。

## 6. Depth

### 6.1 表面层级（3 层，不引入更多）

| 层 | 用途 | 视觉手段 |
|---|---|---|
| L0 / Base | 画布背景 | `--bg` 实色 |
| L1 / Surface | 卡片、表格、Top bar、Sidebar | `--surface` + 1px `--border` |
| L2 / Elevated | Modal、Popover、Tooltip、Dropdown | `--surface` + shadow + 1px `--border-strong` |

### 6.2 Borders and Surfaces

- **默认分层靠 1px 边框**，不靠阴影。阴影仅给浮层（modal / popover）用。
- 嵌套容器（卡片里再放卡片）≤ 2 层。**禁止** 3+ 层嵌套——视觉噪声。
- 表格：行间用 `--surface-2` 斑马（**不**用 border-collapse 加内边）。

### 6.3 阴影（仅 2 档）

- `--shadow-sm`: `0 1px 2px rgba(0,0,0,0.04)` — chip、tag
- `--shadow-md`: `0 4px 12px rgba(0,0,0,0.08)` — modal、popover

### 6.4 Motion Cues

- 默认 transition：`150ms ease-out`（hover / focus / active 状态切换）
- 模态进入：`200ms ease-out`（fade + translateY 4px）
- 表格排序 / 加载：`120ms ease-in-out`
- **全部遵守 `prefers-reduced-motion: reduce`**：上述动效在用户系统设置启用降低动效时降为 0ms。  
详见 `references/craft/animation-discipline.md`。

## 7. Icon System

### 7.1 Icon Source

- **主选**：[**Lucide**](https://lucide.dev) — 1.6px stroke monoline，CC0 license，命名 `IconName` PascalCase（`Home`, `Settings`, `ChevronDown`）
- **备选**：[**Tabler Icons**](https://tabler.io/icons) — 同类 monoline，与 Lucide 互替
- **严禁混用**：同一界面不允许同时出现 Lucide + Heroicons + Material 混搭。如需替换，必须在 DESIGN.md 记录。

### 7.2 Usage Guidelines

- **尺寸**：16px（行内）/ 20px（按钮内、列表前缀）/ 24px（独立功能入口）
- **线宽**：始终 1.6px stroke（在 20px 尺寸下的视觉重量最优）
- **着色**：`currentColor`，跟随父级文字色
- **禁止 emoji 当图标**（`✨🚀🎯⚡🔥💡` 全禁用）—— 是 P0 AI-slop 自动检查项

### 7.3 Conflict Handling

- 若项目已有现成图标库（用户提供 repo），按以下优先级复用：现成库 > Tabler > Lucide
- 命名空间冲突时加前缀：`ds:IconName`（design system 前缀）

## 8. Responsive

### 8.1 Breakpoints

| Name | Min width | 行为 |
|---|---|---|
| `sm` (mobile) | 0 | Sidebar 收为底栏；KPI 行 2 列；表格变卡片栈 |
| `md` (tablet) | 768px | Sidebar 收为 icon-only（56px）；KPI 行 3 列；表格恢复 |
| `lg` (laptop) | 1024px | Sidebar 展开为 240px；KPI 行 4 列 |
| `xl` (desktop) | 1280px | 内容 max-w 1280px；左右 32px 留白 |
| `2xl` (wide) | 1536px | 同 xl，多余空间留白，不拉伸内容 |

### 8.2 Adaptation Rules

- **Top bar**：所有断点都固定。
- **Sidebar**：`lg` 及以上常驻 240px；`md` 收为 56px icon-only；`sm` 转底部 tab bar（最多 5 项）。
- **KPI 行**：`2xl/lg` 4 列 / `md` 3 列 / `sm` 2 列。
- **Data Table**：`md` 及以上显示完整表头 + 行；`sm` 转为每行一卡（label-value 堆叠），并保留列排序的入口。

### 8.3 Priority Changes

- 桌面优先展示"最近活动 / 主表格"；手机优先展示"待办 / 提醒"——小屏场景下用户更需要"接下来做什么"。
- 主 CTA 桌面在右上 action bar；手机**sticky 在底部**（48px 高，便于拇指操作）。

## 9. Review Log

- **Review Status**: 待审查
- **Checklist Basis**:
  - Vercel Web Design Guidelines（见 `references/review-rules.md`）
  - Anti-AI Slop 10-rule checklist（同上 Section 6）
  - 通用 craft：`typography.md` / `color.md` / `accessibility-baseline.md` / `state-coverage.md`
- **Problem List**:
  - `[minor] §3 Typography — IBM Plex Sans 未在团队中确认 — 若团队偏好 Geist / Inter 需替换 — 在回写时改 `--font-sans` token 即可，结构不变`
  - `[minor] §2 Color Palette — `--accent` 选 teal-700 而非品牌色 — 待用户提供品牌主色后调整 — 替换 `--accent` 一个 token 即可，全局 `--accent-fg` 不变`
  - `[minor] §7 Icon System — 主选 Lucide — 若项目已有 Heroicons 等 — 在 `7.3 Conflict Handling` 路径下回写决策`
- **Updated Sections**:
  - 无（首次生成，尚未应用 review 修改）
- **Open Issues**:
  - 是否需要 dark mode？当前仅 light theme。
  - KPI 行的"对比期"维度（"vs 上周 / vs 上月"）是否需要？当前仅占位 Δ +x%。
  - 主表格是否需要行内编辑？当前默认跳转到详情页编辑。
- **Revision Notes**:
  - 首次交付 v1，等待用户/审稿人反馈后填入本节

---

## 10. Assumptions & Open Questions

- **Starting Point**: **全新设计**，无既有 UI Kit、无品牌仓库、无样式参考 URL。按"Style Reference"路径生成——视觉方向以"干净专业"为唯一输入，所有 token 均为本设计原创。
- **Design Decisions**（作为初级设计师向 Manager 汇报时的关键假设）:
  1. **选 light theme 唯一**：B2B 企业客户后台主流仍是浅色，dark mode 可作为 v2 follow-up。
  2. **选 teal-700 作 accent 而非 indigo**：`#6366f1` 已是 AI 设计的"指纹色"，选一个被低估的 teal 既能与"专业"气质匹配，又规避 slop 自查命中。
  3. **选 IBM Plex Sans 而非 Inter**：Inter 虽好但已成 default；Plex 同样工程化、表格/数字细节更优。
  4. **放弃大圆角**（卡片 6px 而非 12-16px）：B2B 信息密度优先，圆角过大= 消费级 app 感。
  5. **保留 4 个 KPI 而非 1 个 hero metric**：企业用户更希望"一眼看到全貌"，而不是被一个数字"教育"。
- **Open Questions**:
  - Q1: 真实产品主色是什么？需替换 `--accent` 哪个 token？
  - Q2: 暗色主题是必须还是 v2？影响 token 体系是否要做双轨。
  - Q3: 表格是否需要行内编辑？影响 Data Table 组件的 state 集合。
  - Q4: 主对象是 "项目 / 订单 / 客户 / 工单 / 报表" 哪一类？影响 KPI 与表格列设计——目前用占位。
  - Q5: 是否需要导出（CSV / PDF）？影响 Toolbar 组件布局。
- **Context Notes**:
  - 本文档**只覆盖主仪表盘视图**。其他视图（详情页、表单、设置、空状态页）需独立 DESIGN.md 复用本 token 体系。
  - 所有占位文案（如 `[Name]`、`KPI 1`）必须由产品/PM 在交付前替换；**不**用 lorem ipsum，也**不**编造数据。
  - 实施阶段建议用 Tailwind + CSS Variables 双轨：token 用 `:root` 变量，工具类用 Tailwind，但 Tailwind `indigo-500/600` 等默认色**全部禁用**。
