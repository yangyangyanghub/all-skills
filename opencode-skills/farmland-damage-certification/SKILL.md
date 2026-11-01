---
name: farmland-damage-certification
description: Use when drafting, generating, or checking 耕地破坏论证意见 / 破坏耕地行政认定意见 for 卫片执法、非法占地、耕地破坏程度认定 cases, or when extracting facts from 执法局调查报告 (scanned PDF) plus 土地利用现状面积表 (xlsx) to produce 公顷/亩 area figures that must reconcile exactly. Triggers 耕地破坏、破坏耕地、论证意见、认定意见、鉴定意见、耕地认定书、地类面积表、宗地图、卫片执法、非法占地、耕作层破坏、破坏耕地程度.
---

# 耕地破坏鉴定文书生成

## 概述

从执法局调查报告 + 土地利用现状面积表，生成《耕地破坏论证意见》和《耕地破坏行政认定意见》两份公文初稿。格式与既有定稿文书逐项对齐，面积经六层校验后闭合。产出是**供人工修改的初稿**，不是终稿。

## 何时使用

- 新批次的违法占地耕地破坏鉴定，需要出两份文书初稿
- 已有初稿，需要核对面积是否自洽、格式是否与历史文书一致
- 需要从扫描件调查报告和 xlsx 地类表里提取事实要素

不适用：非耕地破坏类的行政处罚文书；纯 GIS 空间分析；不动产权属争议。

## 硬性规则

1. **内容描述以执法局调查报告为事实基础。报告没写的事实，不补。**
   - 建设方式（开挖 / 回填 / 硬化 / 砌筑 / 浇筑…）报告没写就不写
   - 不得补报告未提的用地类型（「配套设施用地」等）
   - 地块编号、地块数量报告没提就不列（`include_plot_ids` 默认关闭）
   - 现状描述以报告现场勘查结论为基础，**允许补解释性说明**（如黄花鸢尾的作用、耕作层被水淹没）
   - 宁可少写，不能多写

   **破坏程度结论不在此限。**「原耕作层破坏」「种植条件严重毁坏」「已不具备恢复耕种条件」是耕地破坏鉴定的应有结论——**不构成破坏就不会启动鉴定程序**，所以这些表述不属于虚构，写与不写只是表述繁简之别。
2. **面积以公顷为主，括号内亩**，格式 `X.XXXX公顷（合Y.YY亩）`，1 公顷 = 15 亩
3. **亩数必须四舍五入保留 2 位，禁止截断**。0.2890×15=4.3350 → 4.34；3.1590×15=47.3850 → 47.39
4. **分项之和必须等于总数**，公顷、亩两个口径都要验，亩的分项和必须等于合计亩
5. **两份文书左右边距不同**：论证意见 3.175cm，认定意见 2.499cm。不要统一
6. **法规依据条款固定**，见 `references/law-basis.md`，不得增删改写
7. **地类年份 = 违法年份的上一年**，与地类表文件名对应
8. **材料里查不到的项留占位**（文号写 `X`），不编造。尤其不要凭猜测填文号、日期、基本农田
9. **实质判断不替用户做**：现状是否够得上"耕作层破坏"、已办证部分是否扣减，写清事实后交人工确认
10. **项目名称须与立项批复核对**，调查报告里的名称可能是旧称或错称

## 快速开始

| # | 步骤 | 输入 | 输出 |
|---|---|---|---|
| 1 | 扫描件 OCR | 执法局调查报告.pdf | 执法局调查报告.md |
| 2 | 填配置 | `assets/example-config.json` | 本案.json |
| 3 | 面积预检 | 本案.json | PASS/FAIL（不出文档） |
| 4 | 生成文书 | 本案.json | 论证意见.docx + 认定意见.docx |
| 5 | 面积校验 | 本案.json + 两份 docx | 六层 PASS/FAIL |
| 6 | 格式检查 | 单份 docx | 格式断言 PASS/FAIL |
| 7 | 内容溯源 | docx + 调查报告.md | 虚构表述 PASS/FAIL |
| 8 | 与原件比对（可选） | 生成件 + 参考件 | 逐项格式差异 |

```bash
# 1. OCR（调查报告是扫描件时）
python "C:/Users/HP/.config/opencode/skills/doc-to-md/scripts/convert.py" 执法局调查报告.pdf

# 2. 填配置
Copy-Item assets/example-config.json 本案.json    # Windows
# cp assets/example-config.json 本案.json         # Unix / macOS

# 3. 面积预检，先只校验不出文档
python scripts/gen_docs.py 本案.json --dry-run

# 4. 生成两份 docx
python scripts/gen_docs.py 本案.json

# 5. 面积六层校验
python scripts/verify_area.py 本案.json

# 6. 格式合规检查（两份各跑一次）
python scripts/check_spec.py 论证意见.docx
python scripts/check_spec.py 认定意见.docx

# 7. 内容溯源（可选 --render 追加渲染级检查，需 LibreOffice）
python scripts/check_spec.py 论证意见.docx --report 执法局调查报告.md
python scripts/check_spec.py 认定意见.docx --report 执法局调查报告.md

# 8. 与最近一份定稿原件逐项比对（可选）
python scripts/check_format.py 生成.docx 参考原件.docx
```

`scripts/gen_docs.py` 在面积校验不通过时**拒绝生成文档**并打印原因，这是有意的。

### ⚠️ `.md` 副本不能当检查依据

目录里的 `.md` 只是过程产物。人工在 WPS 里改完 docx 后，md **不会跟着更新**。

实测教训：一份 md 停留在改稿前 7 小时、还带着"开挖建设"和"第二污水处理厂"，两个独立 agent 都读它，一个误报违规、一个误判项目名不一致。

**任何检查都以 `.docx` 为准。** 需要文字比对时，现转一份新的：

```bash
python "C:/Users/HP/.config/opencode/skills/doc-to-md/scripts/convert.py" 文书.docx --force
```

## 🔴 CHECKPOINT · 生成前

跑完 `--dry-run`、面积通过后，**必须先和用户确认这三项**，再执行生成：

1. **项目名称** —— 调查报告可能写旧称（馆陶出现过"第二"实为"第三"）
2. **违法时间 / 地类年份** —— 地类年份 = 违法年份的上一年
3. **是否涉及永久基本农田** —— 报告未明确时必须核实，不可默认"不涉及"

这三项错了，整份文书作废，改配置重跑比改 docx 快。

## 🔴 CHECKPOINT · 交付前

以下全打勾才交付，不要凭目检：

- [ ] `check_spec.py` 全 PASS（论证意见、认定意见各跑一次）
- [ ] `verify_area.py` 全部 PASS
- [ ] 需要时 `check_spec.py --render` 全 PASS
- [ ] `check_format.py` 与参考件无差异（预期差异清单见 `references/format-spec.md` 末尾）
- [ ] 文号 `X` 已标注待填
- [ ] 日期为论证会实际日期
- [ ] 专家组名单待签字
- [ ] 已向用户说明需人工核实的实质判断项

## 跑不起来怎么办

| 症状 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `ModuleNotFoundError: docx` | `pip install python-docx` | 换用已装 python-docx 的解释器 |
| `ModuleNotFoundError: openpyxl` | `pip install openpyxl` | 手工从 xlsx 抄地类数据填进配置 |
| `ModuleNotFoundError: pdfplumber` | `pip install pdfplumber` | 跳过 `--render`，只做结构级检查 |
| OCR 超时或空白 | 提高 DPI、单页转换 | 人工录入报告要素到配置 |
| `[错误] 无法写入` | 关闭 WPS / Word 中打开的该文档 | 改 `meta.out_dir` 输出到别的目录 |
| `[警告] font_source 不存在` | 把 `meta.font_source` 指向任意含方正大标宋简体的 docx | 删掉该字段，接受红头用替代字体 |
| `gen_docs.py` 报面积校验失败 | 按错误行提示定位到具体地块与地类 | 回到 xlsx 逐行核对，差异多在某个地块的分项 |
| `check_spec.py` 大面积 FAIL | 先看 S1 页面和 S2 文档默认 | 若是改了模板导致，从 `assets/example-config.json` 重跑 |

## 三个检查脚本的分工

| 脚本 | 输入 | 用途 |
|---|---|---|
| `verify_area.py` | 配置 JSON + docx | 面积六层校验（地块→汇总→㎡→亩→破坏面→文书文本） |
| `check_spec.py` | 只需 docx | **格式硬约束**：页面、docDefaults、段落、红头、红线、字体嵌入、落款对齐。不依赖参考文件 |
| `check_format.py` | 生成件 + 参考件 | 与某一份具体原件逐项比对，找出历史差异 |

`check_spec.py` 是交付前的**必跑项**。它把本文件与 `references/format-spec.md` 里的每一条约定都做成了断言，54 项左右，缺一项就报 FAIL。

`check_spec.py --render` 追加渲染级校验：转 PDF 后实测「红线到文头文字底部的距离」和「落款两行水平中心是否重合」。结构属性都对但渲染仍有偏差时用它。

## 配置文件

见 `assets/example-config.json` 完整样板。关键字段：

| 字段 | 说明 |
|---|---|
| `meta.out_dir` | 输出目录 |
| `meta.doc_date` | 论证会当日，两份文书同日 |
| `meta.land_year` | 地类年份（违法年份上一年） |
| `meta.doc_number` | 文号，留 `X` 占位 |
| `meta.county_bureau` | 县局全称 |
| `case.subject` | 当事人全称 |
| `case.violation_year` | 非法占用年份 |
| `case.damage_ha` | 认定破坏的耕地公顷数 |
| `case.permanent_farmland` | `null` 表示不涉及；数值表示涉及面积（公顷） |
| `case.status` | 现状描述，如「水面及配套设施用地」 |
| `case.title_lunzheng` / `title_rending` | 可选，覆盖默认标题 |
| `plots[]` | 逐地块明细，脚本自动汇总各地类 |
| `survey_m2` | 可选，调查报告的平方米数据，用于交叉校验 |

`plots[]` 每个地块支持：`id`、`area`、`gengdi`（耕地）、`guoyuan`（果园）、`qiaomu_lindi`（乔木林地）、`qita_lindi`（其他林地）、`nongdao`（农村道路）、`jianshe`（建设用地）。

### 措辞配置项（各单位写法不同，按定稿习惯配）

| 字段 | 默认 | 说明 |
|---|---|---|
| `case.suspect_prefix` | `true` | 标题/首段/结论是否用「涉嫌」。磁县用，冀南新区/经开区/馆陶不用 |
| `case.conclusion_subject_phrase` | `违法占地` | 结论句「主体 __ 总面积X」中间的行为短语 |
| `case.summary_phrase` | `违法建设{项目}` | 「综上」句的行为短语，整句为「主体 __ 共造成…」 |
| `case.action_word` | `违法` | 拼 `summary_phrase` 用的动作词（违法/非法） |
| `case.damage_phrase` | `严重毁坏` | 「种植条件 __」，两份文书共用 |
| `case.lunzheng_damage_phrase` | 继承 `damage_phrase` | 仅在当地明确要求两份表述不同时才配，正常留空 |
| `case.rending_damage_phrase` | 继承 `damage_phrase` | 同上 |
| `case.include_plot_ids` | `false` | 基本情况是否列地块编号（DK1、DK2…） |
| `case.include_land_type_sentence` | `true` | 认定意见是否保留「按照违法占地发生上一年度地类，为…」 |
| `case.status_judgment` | 空 | 现状描述后的判断句。**留空**则只陈述现状，不替专家下结论 |
| `case.construction` | 空 | 建设内容；留空则「建设XX项目。」直接结束 |
| `case.body_line_pt` | `28` | 正文行距（pt） |
| `case.rending_line_pt` | 继承 `body_line_pt` | 认定意见正文行距，内容长时可压到 26 |

## 取数口径

| 要素 | 来源 | 注意 |
|---|---|---|
| 当事人、项目、坐落、违法时间、建设内容、现状 | 执法局调查报告 | 违法时间以报告"非法占用时间"为准；**项目名称须与立项批复/发改文件核对**，调查报告里的名称可能是旧称或错称（馆陶就出现过"第二"实为"第三"） |
| 各地类面积 | 土地利用现状面积表（xlsx，按地块分行） | 取"建设前"地类；公顷 |
| 总面积 | 宗地图 / 地类认定书 | 与地类表总计、调查报告㎡三方核对 |
| 平方米数据 | 调查报告 | 用于第四层交叉校验 |
| 是否占永久基本农田 | 调查报告 | 报告未明确时必须核实，不可默认"不涉及" |

**面积口径冲突的处理**：环保督察、审计、宗地图三方的面积常常不一致。文书一律用自然资源部门出具的**宗地图 / 地类认定书**数据，不要混用其他口径。

## 常见错误

| 错误 | 后果 | 修正 |
|---|---|---|
| 两份文书用同一个左右边距 | 与历史文书不一致，排版肉眼可见差异 | 论证 3.175cm，认定 2.499cm |
| 正文没设两端对齐 | 段落显示左对齐，右边参差不齐 | 原件把 `jc=both` 设在 **Normal 样式**上，段落自身不设；生成时必须设 Normal 样式对齐 |
| 只比段落 alignment 判断对齐是否一致 | 参考件与生成件都显示 None，误判为一致 | 比「有效对齐」：段落 jc 优先，否则取 Normal |
| 认定意见漏了红头下方的红色反线 | 红头不完整，一眼看出不是正式公文 | 反线是锚定在文号段落里的浮动线条形状，不是段落边框；用 `make_red_rule()` |
| 红头只设字体字号，没设字符间距/缩放 | 字宽拥挤，与原件的疏朗观感不同 | `w:spacing=40`（+2pt）+ `w:w=75`（75% 横向缩放），注意 rPr 子元素顺序 |
| 红头字形与原件不同 | 机器没装「方正大标宋简体」，用了替代字体 | 必须嵌入字体：`meta.font_source` 指向参考原件，`embed_font.py` 自动注入 odttf |
| 文头 rPr 缺 `w:cs` / `szCs` / `lang` | python-docx 不写这三项，字距与断行有细微差异 | 用 `style_doc_header_run()` 手工构造完整 rPr |
| 红色反线压住文号 | 线穿过文字，一眼看出错位 | 两个可能：① docGrid 不一致（文号段是 2.5 倍行距，行高受网格约束）；② **docDefaults 带了 python-docx 默认的 after=200/line=276**，让文头段和文号段各多 10pt 段后距、行距变 1.15 倍，文号段整体下移 23.2pt。用 `reset_doc_defaults()` |
| 文号中文变成 Arial Unicode MS | 文号行高度量与原件差 2pt，后续段落跟着偏 | 原件靠 `hint="eastAsia"` + 主题回退，LibreOffice 回退策略不同。显式写 `w:eastAsia="宋体"`，ascii 不写（保数字的 Calibri） |
| 落款日期没对准机关名中心 | 日期偏左或偏右，与机关名不对齐 | 原件用「缩进 + 空格」对位，实测偏 81pt。改用两段共用的居中制表位 `Pt(344)`，长度变化也自动对齐 |
| 亩数用截断（4.335→4.33） | 分项和与合计对不上，或与历史文书口径不符 | 四舍五入 |
| 只校验公顷不校验亩 | 亩的分项和 ≠ 合计亩 | 两个口径都校验 |
| 「综上：」在两份文书里同样处理 | 论证该加粗、认定不加粗 | 见 format-spec |
| 标题统一成一种段落结构 | 论证是单段落软换行，认定是两段 | 见 format-spec |
| 认定意见的「按照违法占地发生上一年度地类」句 | 与当地习惯不符 | 这是**可选项**，由 `include_land_type_sentence` 控制。磁县写了，冀南新区/经开区/馆陶都没写。不要当成必选句硬加 |
| 地类年份取材料提供时间 | 与地类表对不上 | 取违法年份上一年 |
| 替用户判断"这块办过证要扣减" | 越权下实质结论 | 写清事实，交人工定 |
| 生成文档后发现面积错，逐份手改 docx | 改漏、格式乱 | 改 JSON 重跑 gen_docs.py |

## 数据流

```
执法局调查报告(扫描PDF) ──OCR──┐
                              ├──> 本案.json ──> gen_docs.py ──> 论证意见.docx
土地利用现状面积表(xlsx) ─────┘        │                        认定意见.docx
                                      │
                                      └──> verify_area.py ──> 六层校验 PASS/FAIL
```
