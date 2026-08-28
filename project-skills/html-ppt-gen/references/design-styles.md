# Design Style System v2.0

Style is defined by 4 independent dimensions that combine to create custom visual personalities. Choose each dimension based on your industry, audience, and content type.

---

## Style Dimensions

### Dimension 1: Texture

Visual texture and background treatment.

| Option | Description | Best For |
|--------|-------------|----------|
| **clean** | Pure solid color, no texture | Corporate, executive, minimal |
| **grid** | Subtle grid overlay, technical feel | Tech, SaaS, architecture, data |
| **organic** | Soft textures, natural shapes | Wellness, lifestyle, education |
| **paper** | Paper-like texture, tactile feel | Creative, editorial, vintage |

**Implementation**:
```html
<!-- clean -->
<div class="slide-content" style="background:#ffffff;">

<!-- grid -->
<div class="slide-content" style="background:#ffffff;">
  <svg width="100%" height="100%" style="position:absolute;top:0;left:0;opacity:0.05;pointer-events:none;">
    <defs>
      <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#000000" stroke-width="1"/>
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)"/>
  </svg>
  <!-- content -->
</div>

<!-- organic -->
<!-- Use soft shadows, rounded shapes, natural imagery -->

<!-- paper -->
<!-- Use warm off-white backgrounds, subtle noise texture -->
```

---

### Dimension 2: Mood

Color temperature and emotional tone.

| Option | Color Characteristics | Best For |
|--------|----------------------|----------|
| **professional** | Cool-neutral, navy/gray/gold | Corporate, finance, B2B |
| **warm** | Earth tones, friendly colors | Education, lifestyle, wellness |
| **cool** | Blues, grays, analytical feel | Tech, data, science, medical |
| **vibrant** | High saturation, bold colors | Creative, youth brands, gaming |
| **dark** | Deep backgrounds, high contrast | Entertainment, gaming, tech products |
| **neutral** | Balanced, minimal color emotion | Minimal, versatile, safe choice |

**Color Palette Guidance**:

| Mood | Primary Colors | Accent Colors |
|------|---------------|---------------|
| professional | Navy, Gray, Charcoal | Gold, Silver, Accent Blue |
| warm | Terracotta, Sage, Cream | Coral, Olive, Amber |
| cool | Blue, Teal, Gray | Cyan, Indigo, Silver |
| vibrant | Purple, Orange, Pink | Yellow, Green, Turquoise |
| dark | Black, Dark Gray, Navy | Neon, White, Gold |
| neutral | White, Light Gray, Black | Single accent color |

---

### Dimension 3: Typography

Headline and body text personality.

| Option | Font Character | Best For |
|--------|---------------|----------|
| **geometric** | Modern sans-serif, clean lines | Tech, corporate, modern brands |
| **humanist** | Friendly, readable, organic | Lifestyle, wellness, education |
| **handwritten** | Marker/brush feel, organic | Creative, education, playful |
| **editorial** | Magazine style, dramatic | Fashion, lifestyle, editorial |
| **technical** | Monospace-inspired, precise | Developer tools, technical docs |

**Font Recommendations**:

All presentations use a **Chinese-first font system** for optimal bilingual rendering:

| Element | Primary Font | Fallback Stack |
|---------|-------------|----------------|
| **标题 / 大字**（h1-h3, hero titles） | `Noto Serif SC` | `'Noto Serif SC', 'Times New Roman', 'SimSun', serif` |
| **正文 / 段落**（p, li, caption） | `Noto Sans SC` | `'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif` |
| **英文 / 数字**（自动兼容） | Noto Sans SC 内置 Latin | 英文数字自然显示为无衬线体，如需衬线风格回退到 `'Times New Roman', Georgia` |
| **代码 / 技术内容** | `'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace` | 等宽字体固定宽度渲染 |

Typography dimension applied through weight, spacing, and hierarchy:

| Typography Style | How to Apply with Chinese Font System |
|------------------|-----------------------------------|
| geometric | Noto Sans SC Bold (700), tight letter-spacing, uppercase/en numbers |
| humanist | Noto Sans SC Regular (400), comfortable line-height, mixed case |
| handwritten | Noto Serif SC Italic + decorative accents (use sparingly) |
| editorial | Noto Serif SC Bold (700-900) large titles, high contrast sizes, dramatic hierarchy |
| technical | JetBrains Mono / Fira Code for code labels, Noto Sans SC for body |

**Size Hierarchy**:

| Typography Style | Title Size | Subtitle | Body | Caption |
|------------------|-----------|----------|------|---------|
| geometric | 96-120px | 32-40px | 16px | 12px |
| humanist | 72-96px | 28-36px | 15px | 11px |
| editorial | 100-120px | 30-40px | 14-16px | 10-12px |
| technical | 64-80px | 24-32px | 14px | 10px |

---

### Dimension 4: Density

Information density per slide.

| Option | Content per Slide | Best For |
|--------|------------------|----------|
| **minimal** | One focus point, maximum whitespace | Executive briefings, key messages |
| **balanced** | 2-3 key points, comfortable spacing | General presentations, mixed audiences |
| **dense** | Multiple data points, compact layout | Technical docs, detailed analysis |

**Content Guidelines**:

| Density | Bullet Points | Images/Charts | Whitespace |
|---------|--------------|---------------|-----------|
| minimal | 1-3 | 1 hero visual | 60%+ of slide |
| balanced | 3-5 | 1-2 supporting visuals | 40-60% of slide |
| dense | 5-7 | 2-3 visuals, data tables | 30-40% of slide |

**Margin Guidelines**:

| Density | Min Margins | Content Block Spacing |
|---------|------------|----------------------|
| minimal | 0.75" (72px) | 0.5" (48px) |
| balanced | 0.5" (48px) | 0.3-0.5" (29-48px) |
| dense | 0.4" (38px) | 0.25" (24px) |

---

## Style Presets

Pre-configured dimension combinations for common use cases.

### Corporate & Professional

**Preset**: `corporate`
- Texture: **clean**
- Mood: **professional**
- Typography: **geometric**
- Density: **balanced**

**Best For**: Investor decks, B2B proposals, annual reports, executive presentations

**Color Palette**: Navy (#2b2d42), Gray (#8d99ae), White (#edf2f4), Red accent (#ef233c)

**Layout**: Hero-Centric, Section Dividers with Accent Blocks, Clear Visual Hierarchy

---

### Technical & Data-Focused

**Preset**: `technical`
- Texture: **grid**
- Mood: **cool**
- Typography: **technical**
- Density: **dense**

**Best For**: Architecture reviews, system design, technical documentation, data analysis

**Color Palette**: Dark Blue (#023047), Teal (#219ebc), Light Blue (#8ecae6), Orange accent (#ffb703)

**Layout**: Data-Dense, Grid Layouts, Code/Diagram Focus

---

### Creative & Bold

**Preset**: `creative`
- Texture: **clean** or **organic**
- Mood: **vibrant**
- Typography: **editorial**
- Density: **minimal**

**Best For**: Product launches, creative portfolios, marketing presentations, brand showcases

**Color Palette**: Bold primaries, high contrast, vibrant accents

**Layout**: Full-Bleed Images, Large Typography, Minimal Text

---

### Education & Tutorial

**Preset**: `education`
- Texture: **organic**
- Mood: **warm**
- Typography: **humanist**
- Density: **balanced**

**Best For**: Training materials, tutorials, educational content, workshops

**Color Palette**: Warm earth tones, friendly colors, soft accents

**Layout**: Step-by-Step, Visual Examples, Clear Instructions

---

### Executive & Minimal

**Preset**: `executive`
- Texture: **clean**
- Mood: **neutral**
- Typography: **geometric**
- Density: **minimal**

**Best For**: C-level briefings, board presentations, strategic overviews

**Color Palette**: Black, White, Gray, Single Accent

**Layout**: Minimal Text, Bold Headlines, Maximum Impact

---

### Startup & Pitch

**Preset**: `startup`
- Texture: **clean**
- Mood: **vibrant**
- Typography: **geometric**
- Density: **balanced**

**Best For**: Pitch decks, investor presentations, product demos

**Color Palette**: Brand colors, bold accent, clean backgrounds

**Layout**: Conversion-Optimized, Problem-Solution Structure, Social Proof

---

### Healthcare & Wellness

**Preset**: `healthcare`
- Texture: **clean** or **organic**
- Mood: **warm** or **cool**
- Typography: **humanist**
- Density: **balanced**

**Best For**: Medical presentations, patient education, wellness programs

**Color Palette**: Soft Blue (#006d77), Sage (#83c5be), White (#edf6f9), Coral (#e29578)

**Layout**: Trust-Building, Clear Information, Calming Visuals

---

### Financial & Banking

**Preset**: `finance`
- Texture: **clean**
- Mood: **professional**
- Typography: **geometric**
- Density: **balanced**

**Best For**: Financial reports, investment analysis, banking presentations

**Color Palette**: Navy, Gray, Gold accent, Conservative tones

**Layout**: Data-Focused, Professional, Trust-Building

---

### Lifestyle & Consumer

**Preset**: `lifestyle`
- Texture: **organic**
- Mood: **warm**
- Typography: **humanist** or **editorial**
- Density: **minimal**

**Best For**: Brand storytelling, consumer products, lifestyle brands

**Color Palette**: Warm, inviting, emotional connection

**Layout**: Storytelling-Driven, Large Imagery, Emotional Appeal

---

## 36 CSS 主题速查

通过一行代码一键切换完整主题：

```html
<link rel="stylesheet" href="../assets/themes/THEME_NAME.css">
```

### 极简 | 高管汇报・学术・数据

| # | 主题名 | 一句话 |
|---|--------|--------|
| 1 | `minimal-white` | 纯白画布，极致留白，万无一失 |
| 2 | `editorial-serif` | 杂志级排版，暖白底+衬线字体 |
| 3 | `japanese-minimal` | 禅意克制，不对称留白 |
| 4 | `corporate-clean` | 经典商务蓝白灰，安全百搭 |
| 5 | `academic-paper` | 论文质感，脚注风格标注 |

### 柔和与粉彩 | 教育・生活・品牌

| # | 主题名 | 一句话 |
|---|--------|--------|
| 6 | `soft-pastel` | 低饱和粉彩，亲和圆润 |
| 7 | `sunset-warm` | 日落蜜桃色，黄金时刻氛围 |
| 8 | `arctic-cool` | 冰蓝配色，凛冽清爽 |
| 9 | `y2k-chrome` | 千禧年金属光泽，Z世代风格 |
| 10 | `vaporwave` | 粉紫赛博复古，霓虹迷幻 |

### 开发者 / 终端 | 技术分享・代码

| # | 主题名 | 一句话 |
|---|--------|--------|
| 11 | `catppuccin-latte` | 浅色 Catppuccin，柔和粉彩 |
| 12 | `catppuccin-mocha` | 深色摩卡，现代开发者首选 |
| 13 | `dracula` | 经典吸血鬼暗色，紫色点缀 |
| 14 | `tokyo-night` | 深蓝都市，柔和蓝紫高光 |
| 15 | `terminal-green` | 复古终端绿，黑客文化 |
| 16 | `blueprint` | 蓝图蓝靛，工程图纸质感 |

### 暗色与高对比 | 发布会・舞台

| # | 主题名 | 一句话 |
|---|--------|--------|
| 17 | `nord` | 北极暗色，冰霜蓝灰 |
| 18 | `solarized-light` | 暖亮色，文献密集阅读舒适 |
| 19 | `gruvbox-dark` | 复古暖暗色，Linux 极客款 |
| 20 | `rose-pine` | 深色玫瑰粉，安静舒缓 |
| 21 | `cyberpunk-neon` | 霓虹攻击性，赛博朋克 |
| 22 | `retro-tv` | CRT 琥珀橙，老电视复古 |

### 商务与专业 | 融资・对 B・企业

| # | 主题名 | 一句话 |
|---|--------|--------|
| 23 | `sharp-mono` | 纯黑白编辑风，极简力量 |
| 24 | `pitch-deck-vc` | 深蓝+活力点缀，投资人就绪 |
| 25 | `news-broadcast` | 新闻直播红白蓝，权威紧急 |
| 26 | `magazine-bold` | 高对比杂志风，大字报冲击 |

### 艺术设计流派 | 作品集・设计分享

| # | 主题名 | 一句话 |
|---|--------|--------|
| 27 | `neo-brutalism` | 粗野主义，大胆撞色边框 |
| 28 | `glassmorphism` | 毛玻璃模糊，现代 UI 展示 |
| 29 | `bauhaus` | 包豪斯三原色，几何网格 |
| 30 | `swiss-grid` | 瑞士网格国际主义，精确排版 |
| 31 | `memphis-pop` | 孟菲斯孟菲斯图案，80 年代派对 |
| 32 | `midcentury` | 50年代现代主义，胡桃木+芥末黄 |

### 活力与渐变（纯色替代） | 营销・社交

| # | 主题名 | 一句话 |
|---|--------|--------|
| 33 | `rainbow-gradient` | 彩虹色带（纯色模拟渐变） |
| 34 | `aurora` | 极光绿紫交错，自然科技感 |
| 35 | `xiaohongshu-white` | 小红书风，软粉+白+暖橙 |
| 36 | `sharp-mono` | （复用纯黑白，哲学/极简场景） |

---

## Audience-Aware Design

Adjust style dimensions based on target audience.

### Executives
- **Density**: minimal (3-5 key points max)
- **Typography**: large, bold headlines (80-120px)
- **Mood**: professional or neutral
- **Focus**: High-level insights, strategic overview
- **Avoid**: Dense details, technical jargon, playful elements

### Experts/Professionals
- **Density**: balanced to dense
- **Typography**: standard hierarchy (36-44px titles)
- **Mood**: cool or professional
- **Focus**: Technical depth, detailed analysis
- **Include**: Data visualization, detailed explanations

### Beginners/Learners
- **Density**: balanced
- **Typography**: larger body text (16-18px)
- **Mood**: warm or neutral
- **Focus**: Clear explanations, step-by-step structure
- **Include**: Visual examples, simple language

### General Audience
- **Density**: balanced
- **Typography**: standard hierarchy
- **Mood**: depends on topic
- **Focus**: Broad appeal, accessible content
- **Balance**: Information and engagement

---

## Industry Recommendations

### Tech & SaaS
- **Presets**: technical, corporate, startup
- **CSS Themes**: `catppuccin-mocha`, `dracula`, `tokyo-night`, `blueprint`
- **Mood**: cool or professional
- **Texture**: grid or clean
- **Avoid**: Playful elements, neon colors, handwritten fonts

### Finance & Banking
- **Presets**: finance, corporate
- **CSS Themes**: `corporate-clean`, `pitch-deck-vc`, `sharp-mono`, `editorial-serif`
- **Mood**: professional
- **Texture**: clean
- **Avoid**: AI purple/pink gradients, playful icons, informal language

### Healthcare & Medical
- **Presets**: healthcare
- **CSS Themes**: `soft-pastel`, `arctic-cool`, `minimal-white`
- **Mood**: warm or cool
- **Texture**: clean or organic
- **Avoid**: Dark backgrounds, harsh animations, scary imagery

### Education & Training
- **Presets**: education
- **CSS Themes**: `soft-pastel`, `academic-paper`, `editorial-serif`, `solarized-light`
- **Mood**: warm
- **Texture**: organic
- **Avoid**: Corporate stiffness, dense text blocks, cold colors

### Creative & Design
- **Presets**: creative, lifestyle
- **CSS Themes**: `neo-brutalism`, `bauhaus`, `memphis-pop`, `vaporwave`
- **Mood**: vibrant or warm
- **Texture**: clean or organic
- **Avoid**: Generic templates, boring stock photos, safe layouts

### Legal & Consulting
- **Presets**: corporate, executive
- **CSS Themes**: `sharp-mono`, `corporate-clean`, `editorial-serif`, `japanese-minimal`
- **Mood**: professional or neutral
- **Texture**: clean
- **Avoid**: Bright/vibrant colors, playful elements

### Marketing & Advertising
- **Presets**: creative, startup
- **CSS Themes**: `magazine-bold`, `sunset-warm`, `xiaohongshu-white`, `rainbow-gradient`
- **Mood**: vibrant
- **Texture**: clean
- **Avoid**: Dull palettes, overly conservative layouts

---

## Component Style Mapping

How to apply style dimensions to common components.

### Buttons & CTAs

| Texture | Mood | Style |
|---------|------|-------|
| clean | professional | Solid color, subtle shadow |
| clean | vibrant | Bold color, larger size |
| organic | warm | Rounded corners, soft shadow |
| grid | cool | Minimal style, technical feel |

**Radius Guidelines**:
- minimal density: 4-8px
- balanced density: 8-12px
- dense density: 4px (sharp, efficient)

### Cards & Containers

| Texture | Style |
|---------|-------|
| clean | Flat background, clear borders |
| grid | Subtle grid overlay inside |
| organic | Soft shadows, rounded corners |
| paper | Textured background, tactile feel |

**Padding Guidelines**:
- minimal density: 16-24px
- balanced density: 12-20px
- dense density: 8-16px

### Icons & Graphics

| Texture | Icon Style |
|---------|-----------|
| clean | Simple line icons (Heroicons outline) |
| grid | Technical icons, data symbols |
| organic | Soft, rounded icons |
| paper | Textured or hand-drawn feel |

---

## Migration from v1.0

If you used the old 4-style system, map to dimension combinations:

| v1.0 Style | v2.0 Dimensions |
|------------|----------------|
| Sharp & Compact | clean + professional + geometric + dense |
| Soft & Balanced | clean + warm + humanist + balanced |
| Rounded & Spacious | organic + warm + humanist + minimal |
| Pill & Airy | organic + vibrant + editorial + minimal |

---

## Quick Selection Guide

| Project Type | Preset | Why |
|--------------|--------|-----|
| Investor pitch deck | startup | Conversion-focused, bold, memorable |
| Technical architecture review | technical | Data-dense, precise, analytical |
| Executive quarterly report | executive | Minimal, high-level, strategic |
| Educational workshop | education | Warm, approachable, clear |
| Product launch | creative | Bold, visual, impactful |
| Medical presentation | healthcare | Trust-building, calming, clear |
| Financial analysis | finance | Professional, data-focused, conservative |
| Brand storytelling | lifestyle | Emotional, visual, narrative |

---

## Implementation Checklist

Before finalizing style choice:

- [ ] Selected all 4 dimensions (texture, mood, typography, density)
- [ ] OR chosen appropriate preset
- [ ] Verified dimensions match industry/audience
- [ ] Checked anti-patterns for chosen mood/industry
- [ ] Confirmed color palette aligns with mood
- [ ] Validated typography hierarchy with Chinese-first font system (Noto Serif SC / Noto Sans SC)
- [ ] Applied consistent density across all slides