# Apple Design Language

> 参考来源：[agentic-island](https://github.com/suzike/agentic-island) 视觉设计系统分析提炼。
> Apple 设计语言是行业标杆，适用于需要**克制、精致、专业感**的产品。

## Design Intent

- **Mood**: 克制、精致、专业、值得信赖
- **Style Keywords**: minimal, refined, tactile, spacious, intentional
- **Reference**: Apple Human Interface Guidelines, macOS/iOS system UI
- **Avoid**: 过度装饰、强对比、卡通化、Material 风格的强阴影

## Color Palette

Apple 不使用纯黑/纯白，而是通过**墨色层级**（label hierarchy）和**填充层级**（fill hierarchy）构建视觉层次。

### iOS Label 四级墨色

```css
:root {
  /* Light theme */
  --label-primary:   oklch(0.21 0.006 270);  /* 主要文本，不是 #000 */
  --label-secondary: oklch(0.44 0.008 270);  /* 次要文本 */
  --label-tertiary:  oklch(0.62 0.010 270);  /* 辅助文本 */
  --label-quaternary:oklch(0.75 0.010 270);  /* 占位符、禁用 */
}

@media (prefers-color-scheme: dark) {
  :root {
    --label-primary:   oklch(0.92 0.006 270);  /* 不是 #fff */
    --label-secondary: oklch(0.75 0.008 270);
    --label-tertiary:  oklch(0.60 0.010 270);
    --label-quaternary:oklch(0.45 0.010 270);
  }
}
```

### Fill 填充层级（替代阴影）

```css
:root {
  /* Light theme */
  --bg:             oklch(0.99 0.003 270);  /* 页面背景 */
  --fill-1:         oklch(0.97 0.005 270);  /* 一级面板 */
  --fill-2:         oklch(0.94 0.007 270);  /* 二级面板/卡片 */
  --fill-3:         oklch(0.91 0.009 270);  /* 浮层/模态框 */
  --fill-4:         oklch(0.88 0.011 270);  /* 最高层级 */
}
```

### Hairline 发型线

Apple 使用 **0.5px 线条**（hairline）而非 1px 实线，在高 DPI 屏幕上更细腻：

```css
.separator {
  border-bottom: 0.5px solid oklch(0.85 0.005 270 / 0.5);
}

/* 暗色主题：半透明白色 */
.separator-dark {
  border-bottom: 0.5px solid oklch(1 0 0 / 0.08);
}
```

> 注意：0.5px 在 1x 屏幕上会显示为 1px（浏览器四舍五入）。在 2x/3x 屏幕上才会显示为真正的 0.5px。

## Typography

### SF Pro 字体栈

```css
:root {
  --font-display: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
  --font-body:    -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
  --font-mono:    "SF Mono", "Fira Code", "Cascadia Code", monospace;
}
```

### Type Scale

Apple 使用 **大标题（Large Title）** 和 **正文（Body）** 两级系统：

| 用途 | 字号 | 字重 | 行高 |
|------|------|------|------|
| Large Title | 34px | Bold (700) | 1.2 |
| Title 1 | 28px | Bold (700) | 1.25 |
| Title 2 | 22px | Bold (700) | 1.3 |
| Title 3 | 20px | Semibold (600) | 1.35 |
| Headline | 17px | Semibold (600) | 1.4 |
| Body | 17px | Regular (400) | 1.47 |
| Callout | 16px | Regular (400) | 1.5 |
| Subheadline | 15px | Regular (400) | 1.5 |
| Footnote | 13px | Regular (400) | 1.5 |
| Caption 1 | 12px | Regular (400) | 1.5 |
| Caption 2 | 11px | Regular (400) | 1.5 |

## Components

### Buttons

Apple 按钮使用**填充背景 + 文字色**，而非边框：

```css
.button-primary {
  background: var(--accent);
  color: white;
  border-radius: 8px;  /* 连续曲率 */
  padding: 10px 20px;
  font-weight: 600;
  font-size: 17px;
}

.button-secondary {
  background: var(--fill-2);
  color: var(--accent);
  border-radius: 8px;
  padding: 10px 20px;
}
```

### Cards

Apple 卡片**不使用阴影**，而是通过 fill 层级区分：

```css
.card {
  background: var(--fill-1);
  border-radius: 12px;  /* 连续曲率 */
  padding: 16px;
  /* 无 box-shadow */
}
```

### Modals

```css
.modal {
  background: var(--fill-3);
  border-radius: 16px;
  box-shadow: 0 20px 60px oklch(0 0 0 / 0.3);  /* 仅浮层使用阴影 */
}
```

## Layout

### Spacing Scale

Apple 使用 **8px 基准**的间距系统：

```css
:root {
  --space-1:  4px;
  --space-2:  8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}
```

### Border Radius（连续曲率）

Apple 圆角使用**连续曲率**（squircle），不是简单的 `border-radius`：

```css
/* 普通 border-radius（方形圆角） */
.square-radius {
  border-radius: 12px;
}

/* 连续曲率（Apple 风格） */
/* 需要 SVG mask 或 CSS mask-image */
.apple-radius {
  border-radius: 12px;
  /* Safari 自动应用连续曲率 */
  /* Chrome/Firefox 需要 polyfill */
}
```

> 连续曲率在视觉上更柔和，但实现复杂。对于大多数项目，普通 `border-radius` 已足够。

## Motion

Apple 使用**弹簧物理**（spring physics）而非贝塞尔曲线。快速响应（按钮/切换）用 cubic-bezier(0.2,0,0,1)@250ms，平滑过渡用 cubic-bezier(0.25,0.1,0.25,1)@350ms，弹性反馈用 cubic-bezier(0.34,1.56,0.64,1)@500ms。

> **framer-motion 预设见 `references/craft/animation-discipline.md`「React animation libraries」节**——`snappy/smooth/bouncy` 弹簧参数（stiffness/damping）和 `appleVariants` 已在那里定义，此处不重复。

## Theme System（OKLCH）

Apple 设计语言的墨色层级、填充层级天然适配 OKLCH——通过 `--hue`/`--chroma` 轴 + lightness 变化即可生成明暗两套主题。

> **OKLCH 完整语法、适用场景、主题生成模式和浏览器支持见 `references/craft/color.md`「OKLCH color space」节**——此处仅保留 Apple 风格的填说明文字，不重复 CSS 模板。

## When to Use Apple Design Language

| 场景 | 适合 | 不适合 |
|------|------|--------|
| 生产力工具 | ✅ | |
| 仪表盘/后台 | ✅ | |
| 文档/知识库 | ✅ | |
| 电商/营销页 | | ✅ 更适合 Material |
| 游戏/娱乐 | | ✅ 更适合自定义风格 |
| 移动端优先 | | ✅ Material 更成熟 |

## Anti-Patterns（避免）

- ❌ 使用纯黑 `#000` 或纯白 `#fff` — Apple 使用墨色层级
- ❌ 使用强阴影区分层级 — Apple 使用 fill 填充层级
- ❌ 使用 1px 实线边框 — Apple 使用 0.5px hairline
- ❌ 使用卡通化图标 — Apple 使用 1.6-1.8px 线条的单色图标
- ❌ 使用过度饱和的颜色 — Apple 使用低饱和度色调

## Reference Links

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines)
- [agentic-island](https://github.com/suzike/agentic-island) — 实践案例
- [OKLCH color space](https://oklch.com) — 色彩空间说明
- [framer-motion](https://www.framer.com/motion/) — React 动画库
