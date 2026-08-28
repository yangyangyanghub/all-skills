---
name: doc-to-md
description: ANY document → Markdown text extractor. THIS IS THE DEFAULT skill whenever the user wants markdown / plain text / 文字 / OCR output from a file — regardless of source format. Handles PDF (text + scanned via offline RapidOCR), Word docx, PowerPoint pptx, Excel xlsx/xls/csv, HTML, EPUB, Outlook msg, Jupyter ipynb, audio mp3/wav, images jpg/png/gif/bmp/tiff (with OCR), ZIP archives. Trigger phrases: "转 md", "转 markdown", "转成 markdown", "convert to markdown", "提取文字", "提取文本", "识别文字", "OCR", "这个文件里写了什么", "能读出文字吗", "扫描件转文字", "截图识别", "图片里的字", "docx 转 md", "pptx 转 md", "PDF 转 md", "Excel 转 md", "网页存成 md". MUST use THIS skill (not pdf/docx/xlsx skills) whenever the deliverable is markdown or extracted text. Use pdf/docx/xlsx skills ONLY for in-place editing (merge/split/encrypt/formulas/charts), NOT for text extraction. Handles Chinese filenames on Windows. Outputs .md beside each source file.
---

# Document to Markdown Converter

将单个文件、整个文件夹或混合格式的文档批量转换为 Markdown。基于 markitdown 18 种格式支持 + RapidOCR 离线 OCR 兜底。

## 何时使用

- 用户说"转 md"、"转成 markdown"、"批量转换"、"提取文字"、"OCR"
- 用户给出**任何**文档路径（PDF / Word / PPT / Excel / HTML / 邮件 / 音频 / 图片）希望得到文字版
- 用户问"这些文件能转成 md 吗"
- 用户给一个文件夹混合了多种格式，希望统一转 md

## 不要用于

- 反向转换（md → docx/pdf 之类，用 pandoc 或 docx skill）
- PDF 合并/拆分/加密（用 pdf skill）
- 表格数据清洗（用 xlsx skill）
- 需要保留精细排版的场景（markdown 会丢格式）

## 支持格式（18 种）

| 类别 | 扩展名 |
|------|--------|
| 文档 | `.pdf` `.docx` `.pptx` `.xlsx` `.xls` `.csv` `.epub` `.ipynb` |
| 网页 | `.html` `.htm` |
| 邮件 | `.msg`（Outlook） |
| 音频 | `.mp3` `.wav`（语音识别） |
| 图片 | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.tiff`（OCR + 元数据） |
| 归档 | `.zip`（递归提取内容） |
| 文本 | `.txt` `.json` `.xml` 等 plain text |

## 环境前置

固化的 uv 工具环境（**所有 skill 共用**）：
- Python: `C:\Users\HP\AppData\Roaming\uv\tools\markitdown\Scripts\python.exe`
- 已装: `markitdown[all]` 0.1.5, `rapidocr`, `onnxruntime`, `pypdfium2`, `pillow`, `numpy`

环境缺失时提示用户：
```powershell
uv tool install --python 3.12 --with rapidocr --with onnxruntime --with pypdfium2 --with pillow --with numpy 'markitdown[all]'
```

## 核心脚本

| 脚本 | 用途 |
|------|------|
| `scripts/convert.py` | 通用批量转换器，按扩展名路由 + OCR 兜底 |

## 用法

```powershell
$env:PYTHONUTF8 = "1"
$py = "C:\Users\HP\AppData\Roaming\uv\tools\markitdown\Scripts\python.exe"
$script = "C:\Users\HP\.config\opencode\skill\doc-to-md\scripts\convert.py"

# 单个文件（任意支持格式）
& $py $script "E:\Downloads\report.pdf"
& $py $script "E:\Docs\方案.docx"
& $py $script "E:\Photos\screenshot.png"

# 整个文件夹（递归，混合格式无脑全转）
& $py $script "E:\BaiduNetdiskDownload\沟通训练营"

# 只转特定扩展名（多个用逗号分隔）
& $py $script "E:\Mixed" --ext pdf,docx,pptx

# 跳过 OCR（PDF 扫描版和图片只读元数据）
& $py $script "E:\Downloads" --no-ocr

# 覆盖已存在的 md
& $py $script "E:\Downloads" --force

# 输出到独立目录
& $py $script "E:\Downloads" --out-dir "E:\Downloads\md"
```

## 工作流程

1. **枚举**：`Path.rglob` 找出所有支持的扩展名（Unicode 安全）
2. **第一阶段（直接转换）**：用 markitdown 库 API 逐个处理
   - 文字版 PDF、Office、HTML 等：直接得到完整 md
   - 扫描版 PDF：得到空白或极少文字（< 50 字符）→ 标记 OCR
   - 图片：默认得到元数据，OCR 模式下额外识别文字
3. **第二阶段（OCR 兜底）**：
   - 扫描版 PDF：pypdfium2 200 DPI 渲染 → 超长截图按 3000 px 切片 → RapidOCR
   - 图片：直接 RapidOCR
4. **输出**：默认 `.md` 写到源文件同目录，UTF-8

## AI 执行准则

- **必须**用 Python 脚本调用，**不要**直接在 PowerShell 字符串里调 `markitdown.exe`（中文路径 ANSI 乱码）
- 单个简单文件（docx/html/几页文字 PDF）< 5 秒
- 扫描版 PDF 单页约 10-30 秒（OCR）
- 图片 OCR 单张约 2-5 秒
- 大批量（>50 个扫描版）须告知预估耗时
- 完成必须报告：总数、文字版直转数、OCR 数、空白数、失败数

## 已知限制

- 加密 PDF / 受密码保护 Office：失败，需用户先解密
- RapidOCR 中文准确率 95%+，公式 / 手写 / 复杂表格效果一般
- 音频转写依赖系统 SpeechRecognition（需要联网调 Google API，可能被墙）
- ZIP 内含支持格式会被递归处理；超大归档慢
