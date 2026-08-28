# 完整工作流指南 (Authoring Guide)

> 从想法到发布，一份完整的 Deck 制作手册。

---

## 1. 快速开始 — 5 步工作流

```
1. 选模板    → 浏览 full-decks.md，选定一套风格
2. 写 outline → 用 Markdown 写出页面层级结构
3. 生成 deck  → 执行 html-ppt-gen 技能，自动套用模板
4. 调细节    → 微调文案、图片、配色
5. 导出交付  → 导出 PDF / PPTX / 直接浏览器演示
```

**从零到第一页，5 分钟搞定。**

---

## 2. 如何选择主题和布局

### 按场景选

| 你要做什么 | 推荐模板 | 理由 |
|-----------|---------|------|
| 给团队做技术分享 | `tech-sharing` | 代码块 + 架构图，工程师友好 |
| 发小红书帖子 | `xhs-post` | 9 页 3:4 竖版，开箱即用 |
| 融路演 | `pitch-deck` | 12 页标准结构，投资人熟悉 |
| 产品发布 | `product-launch` | 大视觉冲击，Keynote 级别 |
| 学术/论文答辩 | `dir-key-nav-minimal` | 纯内容，无干扰 |

### 按视觉偏好选

| 风格偏好 | 推荐模板 |
|---------|---------|
| 干净留白 | `xhs-white-editorial` |
| 科技未来感 | `graphify-dark-graph` / `hermes-cyber-terminal` |
| 优雅商务 | `obsidian-claude-gradient` |
| 工程审美 | `knowledge-arch-blueprint` |
| 柔和友好 | `xhs-pastel-card` |

---

## 3. 从 Outline 到完整 Deck

### Outline 格式

```markdown
# 演讲标题
## 副标题

---

## 问题陈述
- 当前痛点是什么
- 为什么需要解决

---

## 我们的方案
- 核心技术点
- 架构图说明

---

## 总结
- 三个关键 takeaway
```

### 生成流程

1. `---` 分隔每一页
2. 执行技能自动识别标题层级
3. 模板自动套用布局和样式
4. 需要自定义布局的页面加 layout 标记

---

## 4. 中英双语 Deck 制作

### 策略一：一页双语（上中下英）

```markdown
## 系统架构 / System Architecture

<!-- 中文在上，英文在下 -->
- 缓存层扛住热点查询
  - Cache layer handles hot queries
- 异步队列解耦写操作
  - Async queue decouples writes
```

### 策略二：逐页切换（奇数中文，偶数英文）

- 同一 outline，生成两份 deck
- 通过脚本批量翻译 speaker notes
- 适合面向国际团队

### 注意事项

- 英文文案更短，布局可能留白过多 → 适当增大字号
- 中文标题控制在 8 字内，英文控制在 5 词内
- code block 中的注释建议双语

---

## 5. 导出为 PDF / PNG

### PDF 导出

- 浏览器 `Print → Save as PDF`
- 设置：背景图形 ✓、横向 ✓、无页眉页脚
- 输出尺寸与 slide 尺寸一致

### PNG 导出

- 逐页截图或使用导出脚本
- 适合社交媒体分享（如小红书）
- 导出后压缩见 `baoyu-compress-image` 技能

### 浏览器直接演示

- 双击 `deck.html` 打开即可
- 快捷键导航、全屏、演讲者模式一应俱全
- 无需安装任何软件

---

## 6. 文件结构和命名规范

```
project/
├── deck.html              # 主 HTML（自动生成）
├── runtime.js             # 运行时引擎（自动生成）
├── theme.css              # 主题样式
├── assets/
│   ├── images/            # 图片资源
│   │   ├── cover.png      # 封面图
│   │   └── diagram-1.png  # 图表
│   └── icons/             # 图标
├── speaker-notes/         # 逐字稿（可选）
│   └── notes.md
└── outline.md             # 源文件（你写的）
```

### 命名规范

- 文件名用 `kebab-case`（小写+连字符）
- 图片描述性命名：`architecture-overview.png` 而非 `img001.png`
- 版本号可选后缀：`deck-v1.2.html`

---

## 7. 最佳实践和常见陷阱

### ✅ 最佳实践

- **一页一事** — 每页只讲一个核心观点
- **字号底线** — 正文不小于 18px，标题不小于 32px
- **图片质量** — 导出 PNG 至少 2x 分辨率
- **配色统一** — 全文不超过 3 个主色
- **演讲者模式** — 重要分享一定用 [presenter-mode.md](./presenter-mode.md) 写逐字稿
- **备份源文件** — outline.md 是源，deck.html 是产物

### ❌ 常见陷阱

- **文字太多** — 一屏超过 6 行文字，观众读不完
- **颜色爆炸** — 每个标题不同颜色，像调色盘
- **动画过度** — 每个元素都飞进来，分散注意力
- **忽略比例** — 16:9 的 deck 在小屏手机上看灾难 → 需要竖版选 `xhs-post`
- **没有演练** — 写完直接上台 → 用逐字稿 + 计时器练 2 遍
- **字体不嵌入** — 导出 PDF 时特殊字体丢失 → 用系统字体或 webfont