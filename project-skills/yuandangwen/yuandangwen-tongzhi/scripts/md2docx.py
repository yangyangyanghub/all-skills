#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
邯郸市自然资源和规划局 · 会议通知 Markdown → Word 转换脚本

格式标准参照 references/人工范本_会议通知.md 和 references/格式规范.md。

输入：会议通知 .md 文件
输出：同目录下 .docx 文件

特性：
- 标题区：黑体 22 居中（无红头、无文号、无分隔线）
- 主送：仿宋 16 顶格
- 一级章节（一、二、三）：黑体 16
- 普通正文：仿宋 16，首行缩进 2 字符
- 会议内容（一）（二）：楷体 16
- 有关要求（一）（二）：仿宋 16
- 联系人：仿宋 16 顶格
- 落款：仿宋 16 右对齐
- **xxx** 全文统一处理：剥字符 + 黑体 16

用法：
    python md2docx.py <markdown文件路径>
"""

import sys
import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


# ============= 字体与格式工具函数 =============

def setup_run(run, font_name: str = '仿宋', size: int = 16, bold: bool = False):
    """统一设置 run 字体（含中文字体）"""
    run.font.name = font_name
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)


def add_styled_paragraph(doc, text: str, font: str = '仿宋', size: int = 16,
                          bold: bool = False, align=None,
                          first_line_indent: bool = True,
                          right_indent_cm: float = None):
    """添加一个段落，支持 **xxx** 加粗标记"""
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if first_line_indent:
        p.paragraph_format.first_line_indent = Cm(0.74)  # 2 字符 ≈ 0.74cm
    if right_indent_cm is not None:
        p.paragraph_format.right_indent = Cm(right_indent_cm)

    # 处理 **xxx** 标记
    parts = re.split(r'\*\*(.+?)\*\*', text)
    for idx, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        if idx % 2 == 1:
            # 加粗部分：用黑体
            setup_run(run, '黑体', size, True)
        else:
            setup_run(run, font, size, bold)

    return p


def is_main_recipient(line: str) -> bool:
    """判断是否为主送行（以"各"开头且以冒号结尾）"""
    line = line.strip()
    return line.startswith('各') and line.rstrip().endswith('：')


def is_first_paragraph(line: str) -> bool:
    """判断是否为引言段（以"为"开头的因果/目的段）"""
    return line.startswith('为') or line.startswith('按照') or line.startswith('根据')


def is_section_heading(line: str) -> bool:
    """判断是否为一级章节（一、二、三、四、五），兼容 `## 一、` 和 `一、`"""
    line = re.sub(r'^#+\s*', '', line).strip()
    return bool(re.match(r'^[一二三四五六七八九十]+、', line))


def _strip_markdown_heading(line: str) -> str:
    """剥掉 markdown 标题标记（## 、### 等）"""
    return re.sub(r'^#+\s*', '', line).strip()


def is_content_clause(line: str) -> bool:
    """判断是否为会议内容条款（一）（二）"""
    return bool(re.match(r'^（[一二三四五]）', line.strip()))


def is_requirement_clause(line: str) -> bool:
    """判断是否为有关要求条款（出现在五、之后）"""
    return bool(re.match(r'^（[一二三四五]）', line.strip()))


def is_contact_line(line: str) -> bool:
    """判断是否为联系人行（兼容"联 系 人""联系人""信息中心"等）"""
    line = line.strip()
    return (line.startswith('联 系 人') or line.startswith('联 系 人：')
            or line.startswith('联系人') or line.startswith('联系人：')
            or line.startswith('信息中心') or line.startswith('信息中心：'))


def is_signature_block(line: str) -> bool:
    """判断是否为落款（机关名 + 日期）"""
    line = line.strip()
    if not line or line == '---':
        return False
    return ('邯郸市' in line and '局' in line and len(line) < 30) or bool(re.match(r'^\d{4}年\d{1,2}月\d{1,2}日', line))


# ============= Markdown 解析与转换 =============

def parse_markdown(md_path: Path) -> dict:
    """解析 markdown，剥离 frontmatter 和元信息"""
    content = md_path.read_text(encoding='utf-8')

    # 剥 frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, count=1, flags=re.DOTALL)

    # 剥 "## 参考资料" 之后的内容
    content = re.split(r'\n## 参考资料', content, maxsplit=1)[0]

    # 剥 "## 待洋哥确认" 之后的内容
    content = re.split(r'\n## 待洋哥确认', content, maxsplit=1)[0]

    # 提取 H1 标题
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ''

    # 剥 H1 标题行
    content = re.sub(r'^# .+\n', '', content, count=1, flags=re.MULTILINE)

    return {
        'title': title,
        'body': content.strip(),
    }


def build_docx(md_path: Path, output_path: Path = None) -> Path:
    """根据 markdown 生成 docx"""
    if output_path is None:
        output_path = md_path.with_suffix('.docx')

    parsed = parse_markdown(md_path)
    title = parsed['title']
    body = parsed['body']

    doc = Document()

    # === 页面设置 ===
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(3.7)
    section.bottom_margin = Cm(3.5)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.6)

    # === 标题区（无红头、无文号） ===
    # 第 1 行：机关名（默认从落款或"邯郸市自然资源和规划局"取）
    agency_line = '邯郸市自然资源和规划局'
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(agency_line)
    setup_run(run, '黑体', 22)

    # 第 2 行：通知标题
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title)
    setup_run(run, '黑体', 22)

    # 空行分隔
    doc.add_paragraph()

    # === 正文逐段处理 ===
    lines = body.split('\n')
    in_requirements_section = False  # 标记是否在"五、有关要求"之后

    for raw_line in lines:
        line = _strip_markdown_heading(raw_line).rstrip()
        if not line:
            continue
        # 过滤 markdown 分割线
        if line == '---' or set(line) == {'-', '*'} and len(line) > 3:
            continue

        # 主送（顶格，仿宋 16）
        if is_main_recipient(line):
            p = doc.add_paragraph()
            run = p.add_run(line)
            setup_run(run, '仿宋', 16)
            p.paragraph_format.first_line_indent = Cm(0)
            continue

        # 一级章节标题（黑体 16，独立成行，无缩进）
        if is_section_heading(line):
            # 章节切换时检测：进入"五、有关要求"
            if line.startswith('五、') and ('有关要求' in line or '要求' in line):
                in_requirements_section = True
            elif line.startswith('四、') and '内容' in line:
                # 离开会议内容区
                in_requirements_section = False
            p = doc.add_paragraph()
            run = p.add_run(line)
            setup_run(run, '黑体', 16)
            p.paragraph_format.first_line_indent = Cm(0)
            continue

        # 联系人在"有关要求"段后可能出现，单独判断
        if is_contact_line(line):
            p = doc.add_paragraph()
            run = p.add_run(line)
            setup_run(run, '仿宋', 16)
            p.paragraph_format.first_line_indent = Cm(0)
            continue

        # 会议内容条款（一）（二）：楷体 16（在四、会议内容之后、五、之前）
        if is_content_clause(line) and not in_requirements_section:
            add_styled_paragraph(doc, line, font='楷体', size=16)
            continue

        # 有关要求条款：仿宋 16
        if is_requirement_clause(line) and in_requirements_section:
            add_styled_paragraph(doc, line, font='仿宋', size=16)
            continue

        # 引言段（首行缩进，仿宋 16）
        if is_first_paragraph(line):
            add_styled_paragraph(doc, line, font='仿宋', size=16)
            continue

        # 落款（机关名 + 日期，右对齐）
        if is_signature_block(line):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(line)
            setup_run(run, '仿宋', 16)
            p.paragraph_format.right_indent = Cm(2.5)
            p.paragraph_format.first_line_indent = Cm(0)
            continue

        # 默认：仿宋 16 首行缩进
        add_styled_paragraph(doc, line, font='仿宋', size=16)

    doc.save(output_path)
    return output_path


# ============= 入口 =============

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python md2docx.py <markdown_file>')
        sys.exit(1)

    md_file = Path(sys.argv[1])
    if not md_file.exists():
        print(f'[ERROR] 文件不存在: {md_file}')
        sys.exit(1)

    output = build_docx(md_file)
    print(f'[OK] 已生成: {output}')
