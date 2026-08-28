# DESIGN.md

> 模板说明：保留章节结构，按项目实际情况替换占位内容；不要把示例占位词原样提交到正式设计文档。

## 1. Visual Theme
- **Design Intent**: `[描述整体视觉方向、品牌气质、目标体验]`
- **Style Keywords**: `[填写 3-6 个风格关键词]`
- **Reference Notes**: `[记录参考产品、灵感来源或避免的风格]`

## 2. Color Palette
- **Primary Colors**: `[填写主色用途与角色，不直接写死颜色时可描述语义]`
- **Secondary Colors**: `[填写辅助色、强调色或状态色策略]`
- **Usage Rules**: `[说明颜色如何分配到背景、文本、边框、反馈状态]`

## 3. Typography
- **Type System**: `[说明标题、正文、辅助文字的层级结构]`
- **Font Guidance**: `[填写字体风格、字重、可读性要求]`
- **Text Rules**: `[说明字距、行高、最大行长或语言适配要求]`

## 4. Components
- **Core Components**: `[列出关键组件，例如按钮、卡片、表单、表格、导航]`
- **States**: `[说明默认、悬停、激活、禁用、加载、错误等状态]`
- **Behavior Notes**: `[记录交互反馈、一致性规则、可复用约束]`

## 5. Layout
- **Page Structure**: `[描述页面或界面的主要区域划分]`
- **Spacing System**: `[说明间距、栅格、对齐和留白规则]`
- **Content Flow**: `[记录信息优先级、阅读顺序、关键路径]`

## 6. Depth
- **Elevation Strategy**: `[说明阴影、层级、浮层与表面关系]`
- **Depth Model Choice**: `[选择填充制或阴影制，说明理由]`
- **Borders and Surfaces**: `[填写描边、分层、背景面板处理方式]`
- **Motion Cues**: `[说明通过动效或过渡体现层次的方式]`

### Depth Model Guide（深度模型选择指南）

> 选择填充制（fill-based）或阴影制（shadow-based）来区分层级。

| 维度 | 填充制（Apple 风格） | 阴影制（Material 风格） |
|------|---------------------|----------------------|
| **原理** | 通过背景色明度区分层级 | 通过 box-shadow 区分层级 |
| **层级表达** | fill-1（最浅）→ fill-2 → fill-3（最深） | elevation-1（低）→ elevation-2 → elevation-3（高） |
| **跨主题** | 简单 — 只改变明度轴 | 复杂 — 阴影颜色/模糊需重新计算 |
| **性能** | 更好 — 纯背景色，无渲染开销 | 略差 — 阴影需要额外渲染 |
| **视觉风格** | 扁平、克制、Apple/Linear | 立体、突出、Material/Gmail |
| **适用场景** | 生产力工具、仪表盘、文档 | 移动端、卡片密集、电商 |

**选择原则**：
- 项目以**生产力/信息密度**为主 → 填充制
- 项目以**卡片/内容块**为主 → 阴影制
- 项目需要**极简/克制**风格 → 填充制
- 项目需要**突出/层次分明** → 阴影制
- 不确定时 → 填充制（更现代、跨主题更简单）

**填充制示例**：
```css
:root {
  --fill-1: oklch(0.98 0.005 250);  /* 页面背景 */
  --fill-2: oklch(0.95 0.008 250);  /* 卡片/面板 */
  --fill-3: oklch(0.92 0.01 250);   /* 浮层/模态框 */
}
```

**阴影制示例**：
```css
:root {
  --elevation-1: 0 1px 2px rgba(0,0,0,0.05);  /* 卡片 */
  --elevation-2: 0 4px 8px rgba(0,0,0,0.08);  /* 浮层 */
  --elevation-3: 0 8px 16px rgba(0,0,0,0.12); /* 模态框 */
}
```

## 7. Icon System
- **Icon Source**: `[填写图标库候选、选择原则或命名空间策略]`
- **Usage Guidelines**: `[说明尺寸、线条粗细、配色和搭配规则]`
- **Conflict Handling**: `[记录多图标库并存时的冲突解决方式]`

## 8. Responsive
- **Breakpoints**: `[填写断点策略或设备范围]`
- **Adaptation Rules**: `[说明布局、导航、组件在不同尺寸下如何变化]`
- **Priority Changes**: `[记录移动端与桌面端的信息优先级差异]`

## 9. Review Log
- **Review Status**: `[填写待审查 / 已审查 / 需修订 / 已复审等状态]`
- **Checklist Basis**: `[填写审查依据，例如 Vercel Web Design Guidelines]`
- **Problem List**:
  - `[critical|major|minor] 章节名 — 问题摘要 — 影响原因 — 需要回写到 DESIGN.md 的修改动作`
  - `[critical|major|minor] 章节名 — 问题摘要 — 影响原因 — 需要回写到 DESIGN.md 的修改动作`
- **Updated Sections**:
  - `[章节名] — [已应用的修改内容] — [对应问题项状态：resolved/open]`
  - `[章节名] — [已应用的修改内容] — [对应问题项状态：resolved/open]`
- **Open Issues**: `[列出仍待确认的问题、风险或阻塞项]`
- **Revision Notes**: `[记录审查结论、修改建议、已完成修订和下一步动作]`

## 10. Assumptions & Open Questions
- **Starting Point**: `[明确设计的起点：是全新设计、基于某个 UI Kit、还是重构现有界面？如果没有设计系统，必须在此记录]`
- **Design Decisions**: `[记录作为初级设计师向 Manager 汇报时，做出的关键假设和推理逻辑]`
- **Open Questions**: 
  - `[Q1: 针对用户不明确的交互意图提出的具体问题]`
  - `[Q2: 针对变体数量、视觉风格或文案风格的确认请求]`
- **Context Notes**: `[任何有助于后续实施者理解设计意图的额外背景信息]`
