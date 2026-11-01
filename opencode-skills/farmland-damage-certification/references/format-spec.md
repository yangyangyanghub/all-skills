# 格式规范（逐项对齐既有文书）

所有数值取自 2026 年邯郸市已定稿文书原件（磁县、冀南新区、经开区），
四份文书的论证意见、三份认定意见在以下参数上完全一致。

## 文档默认格式（docDefaults）

原件的 `styles.xml` 里 `docDefaults` 是**空的 pPrDefault**：

```xml
<w:docDefaults>
  <w:rPrDefault>
    <w:rPr><w:rFonts w:asciiTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi"
                     w:eastAsiaTheme="minorEastAsia" w:cstheme="minorBidi"/></w:rPr>
  </w:rPrDefault>
  <w:pPrDefault/>
</w:docDefaults>
```

python-docx 默认模板不是这样，它塞了三样原件没有的东西：

| python-docx 默认 | 后果 |
|---|---|
| `pPrDefault/w:pPr/spacing after="200" line="276" auto` | 未显式设 spacing 的段落多出 10pt 段后距、行距变 1.15 倍 |
| `rPrDefault/w:rPr/w:sz="22"` | 默认字号变 11pt |
| `rPrDefault/w:rPr/w:lang eastAsia="en-US"` | 中文字体解析错，回退成 Arial Unicode MS |

**文头段（P00）和文号段（P01）都没有显式 spacing**，全部受影响。

实测后果：**文号段整体下移 23.2pt，红头反线跟着下移 21.85pt**（红线锚定在文号段上）。
表现就是「红线离文头太远 / 压住文号」。

正文段都显式设了 `lineRule="exact"` 和 `space_after=0`，不受影响——所以问题只出现在红头区，容易误判成红线参数错。

用 `reset_doc_defaults()` 清掉这三项。

## 文号段的字体回退

原件文号 run 不写字体名，只有 `<w:rFonts w:hint="eastAsia"/>`，靠主题回退：

- `hint="eastAsia"` → 中文字符按东亚字体解析
- `eastAsiaTheme="minorEastAsia"` → 主题 minorFont 的 `<a:ea>`，原件为空
- 空值时的回退策略各渲染器不同：WPS/Word 落到宋体，**LibreOffice 落到 Arial Unicode MS**

行高度量不同 → 文号段高度差约 2pt → 后续段落整体偏移。

修复：文号 run 显式写 `w:eastAsia="宋体"`，**不写 ascii**，让数字继续走主题的 Calibri（与原件一致）。

主题文件本身也要从原件复制（`word/theme/theme1.xml`）——原件 `majorFont latin="Calibri Light"` / `minorFont latin="Calibri"`，python-docx 默认是 `Calibri` / `Cambria`，数字字体会不同。

## 页面设置

| 项 | 论证意见 | 认定意见 |
|---|---|---|
| 纸张 | A4 21.0 × 29.7 cm | A4 21.0 × 29.7 cm |
| 上边距 | 2.54 cm | 2.54 cm |
| 下边距 | 2.54 cm | 2.54 cm |
| 左边距 | **3.175 cm** | **2.499 cm** |
| 右边距 | **3.175 cm** | **2.499 cm** |
| 页眉距 | 42.55 pt（851 twip） | 同 |
| 页脚距 | 49.6 pt（992 twip） | 同 |
| 分栏 | `<w:cols w:space="425" w:num="1"/>` | 同 |
| 文档网格 | `<w:docGrid w:type="lines" w:linePitch="312" w:charSpace="0"/>` | 同 |

**两份文书的左右边距不同，这是原件事实，不要统一。** 这是最容易出错的一项。

### 文档网格不能忽略

`docGrid` 的 `linePitch` 决定网格每行高度（312 = 15.6pt）。7 份原件全部是 `type="lines" linePitch="312"`。

python-docx 默认模板是 `linePitch="360"` 且没有 `type`。**不改会出现两个问题：**

1. 正文段落用的是 `lineRule="exact"`（精确行距），不受网格影响，看起来正常
2. **多倍行距段落受影响**——认定意见的文号段落是 `line="600" lineRule="auto"`（2.5 倍），行高会被网格约束。行高变了，锚定在段落上的红色反线偏移 5.4pt 就会落到文字上，**压住文号**

这个问题的表现是「红线遮字」，容易被误判成红线位置参数错了。实际是节属性（网格）不一致。

页眉页脚距离、分栏间距同理——原件 7 份完全统一，不要用 python-docx 的默认值。

## 对齐方式（样式层，最容易漏）

原件的正文对齐**不在段落属性里**，而是设在 **Normal 样式**上：

```xml
<w:style w:type="paragraph" w:styleId="a">
  <w:pPr><w:jc w:val="both"/></w:pPr>   <!-- 两端对齐 -->
</w:style>
```

正文段落自身**不设** `<w:jc>`，靠继承 Normal 得到两端对齐。

**这意味着：**

- 只比对段落的 `alignment` 属性，参考件和生成件都会显示"None"，看起来一致，实际一个是两端对齐、一个是左对齐
- 生成 docx 时必须显式设置 Normal 样式的对齐：

```python
doc.styles['Normal'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
```

标题（居中）、落款日期（右对齐）段落本身有显式 `jc`，不受 Normal 影响。
落款单位段落无显式 `jc`，继承 Normal 得到两端对齐——与原件一致。

`scripts/check_format.py` 已按"有效对齐"（段落 `jc` 优先，否则取 Normal）比对，不会漏这一层。

## 段落格式

| 位置 | 字体 | 字号 | 加粗 | 对齐 | 行距 | 首行缩进 |
|---|---|---|---|---|---|---|
| 论证意见标题 | 黑体 | 22pt | 是 | 居中 | 30pt 精确 | 无 |
| 标题下空行 | — | — | — | — | 28pt | 无 |
| 正文 | 仿宋 | 16pt | 否 | **两端（继承 Normal）** | 28pt 精确 | 2 字符（32pt / 640 twip） |
| 一级标题「一、基本情况」 | 黑体 | 16pt | 否 | 两端（继承 Normal） | 28pt | 2 字符 |
| 「（一）（二）」标签（论证） | 楷体 | 16pt | 否 | 两端（继承 Normal） | 28pt | 2 字符 |
| 「（一）（二）」标签（认定） | 楷体 | 16pt | **是** | 两端（继承 Normal） | 28pt | 2 字符 |
| 「综上：」（论证） | 仿宋 | 16pt | **是** | 两端（继承 Normal） | 28pt | 2 字符 |
| 「综上：」（认定） | 仿宋 | 16pt | 否 | 两端（继承 Normal） | 28pt | 2 字符 |
| 文头「耕地破坏行政认定意见」 | 方正大标宋简体 | 55pt | 否 | 居中 | 默认 | 无 |
| 红色反线（文号段落内浮动形状） | — | 2.25pt 线宽 | — | 左偏 14.8pt / 下偏 5.4pt | — | — |
| 文号 | 不指定字体 | 14pt | 否 | 右 | 2.5 倍 | 无 |
| 落款单位 | 仿宋 | 16pt | 否 | 继承 Normal | 26pt | 居中制表位 344pt |
| 落款日期 | 仿宋 | 16pt | 否 | 继承 Normal | 26pt | 同一居中制表位 344pt |

**落款用居中制表位实现上下对齐**，不要用「首行缩进 + 手打空格」。

原件就是这样写的（机关名缩进 5120 twip，日期缩进 640 twip 后跟 14 个空格），实测日期中心比机关名中心偏 **81pt**，视觉上明显错位。

正确做法：两段各自在 `Pt(344)`（相对版心左边界）设一个居中制表位，段落以 `\t` 开头：

```python
p.paragraph_format.tab_stops.add_tab_stop(Pt(344), WD_TAB_ALIGNMENT.CENTER)
p.add_run('\t邯郸市自然资源和规划局')
```

两行中心自动重合，与机关名长短无关。机关名或日期长度变化都不需要重算缩进。
| 论证意见落款日期 | 仿宋 | 16pt | 否 | 右 | 28pt | 2 字符 |

**「综上：」加粗与否，两份文书相反。** 论证意见加粗，认定意见不加粗。

## 特殊处理

### 标题软换行

- **论证意见标题是一个段落**，两行之间用软换行（`w:br`，Word 里是 Shift+Enter）
- **认定意见标题是两个独立段落**，各占一段

两份原件的处理方式不同，不要统一成一种。

### 文头颜色与字体

认定意见文头为红色 `#FF0000`，字体「方正大标宋简体」55pt（`w:sz=110`）。

**这个字体多数机器没装，必须嵌入文档**，否则 WPS/Word 用替代字体渲染，红头字形与原件明显不同。原件在 `word/fonts/` 里嵌了 5 个 `*.odttf`（黑体、Calibri、方正大标宋简体、仿宋、楷体），`settings.xml` 里开了 `embedTrueTypeFonts` 和 `saveSubsetFonts`。

用 `scripts/embed_font.py` 从参考原件提取并注入，配置里填 `meta.font_source` 指向参考原件即可自动嵌入。

注意：odttf 是字体子集，只含原件用到的字符。文头文字固定为「耕地破坏行政认定意见」9 个字，与原件相同，因此子集够用。若改文头文字，需要重新从含这些字的文档取字体。

**文头 `w:rPr` 必须与原件逐项一致**：

```xml
<w:rFonts w:hint="eastAsia" w:ascii="方正大标宋简体" w:hAnsi="方正大标宋简体"
          w:eastAsia="方正大标宋简体" w:cs="方正大标宋简体"/>
<w:color w:val="FF0000"/>
<w:spacing w:val="40"/>     <!-- 字符间距 +2pt -->
<w:w w:val="75"/>           <!-- 横向缩放 75% -->
<w:sz w:val="110"/>         <!-- 55pt -->
<w:szCs w:val="110"/>
<w:lang w:eastAsia="zh-CN"/>
```

python-docx 的 `font` API **不会**写 `w:cs`、`w:szCs`、`w:lang`，也不写 `w:hint`。缺 `w:cs` 会让复杂文种回退到其他字体；缺 `w:lang` 影响断行与字距。必须手工构造整个 `w:rPr`（用 `style_doc_header_run()`）。

`w:rPr` 子元素顺序：`rFonts → b → color → spacing → w → sz → szCs → lang`。
用 python-docx 的 `append` 追加会排错位置，破坏 schema。必须按位置插入。

### 红色反线（红头分隔线）

认定意见文头下方有一条横贯版心的红线，**它不是段落边框**，而是锚定在文号段落里的一个浮动线条形状：

| 参数 | 值 | OOXML |
|---|---|---|
| 长度 | 484.55pt（6153785 EMU） | `<wp:extent cx="6153785" cy="7620"/>` |
| 线宽 | 2.25pt（28575 EMU） | `<a:ln w="28575">` / `<v:stroke weight="2.25pt">` |
| 颜色 | `#FF0000` | `<a:srgbClr val="FF0000"/>` |
| 线型 | 实线 | `<a:prstDash val="solid"/>` |
| 水平位置 | 相对栏，向左偏 14.8pt | `<wp:positionH relativeFrom="column"><wp:posOffset>-187960</wp:posOffset>` |
| 垂直位置 | 相对段落，向下偏 5.4pt | `<wp:positionV relativeFrom="paragraph"><wp:posOffset>68580</wp:posOffset>` |
| 垂直翻转 | 是 | `<a:xfrm flipV="1"/>` |

结构上是一个 `w:r`，内含 `mc:AlternateContent`：
`mc:Choice Requires="wps"` 走 DrawingML，`mc:Fallback` 走 VML（`<v:line>`）。
两条分支都要写，否则老版本 Word / 部分 WPS 版本不显示。

`scripts/gen_docs.py` 的 `make_red_rule()` 已内置该形状，插入到文号段落第一个 run 的位置。

**只有认定意见有这条线，论证意见没有。**

### 文号

文号段落**不指定字体**（继承默认），只设 14pt、右对齐、2.5 倍行距。
指定成仿宋会导致与原件有细微字距差异。

## 核对方法

```bash
# 只看目标文档的段落格式表
python scripts/check_format.py 目标.docx

# 与参考原件逐段比对（推荐）
python scripts/check_format.py 生成.docx 参考原件.docx
```

比对输出中以下差异属于**原件本身不统一**或**有意为之**，可以忽略：

- 段落内 run 的切分数量不同（原件因多次修订被拆成多个 run，字体一致即等价）
- 论证意见最后两段（专家组成员、日期）原件未设行距，生成件统一为 28pt
- 空白占位段：原件用空格字符填充，生成件用真空段落
- **认定意见 P01（文号）字体**：原件未写字体名（显示为 None），生成件显式写「宋体」。这是有意为之——靠主题回退在 LibreOffice 下会落到 Arial Unicode MS，行高差 2pt。渲染结果一致，XML 不同。

其余任何差异都需修正。
