#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测绘技术设计书 Word 文档格式化工具

基于 CH/T 1004-2005《测绘技术设计规定》规范要求，
将 Markdown 文档转换为格式规范的 Word 文档。

功能：
- 规范的封面设计
- 自动目录生成
- 符合测绘规范的字体字号
- 页面设置（A4）
- 标题编号格式
- 表格样式
- 页眉页脚

使用方法：
    python docx_formatter.py input.md output.docx --title "技术设计书标题" --author "编制单位"
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.section import WD_ORIENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.shared import Pt, Cm, Inches, RGBColor
except ImportError:
    print("错误：未安装 python-docx 库")
    print("请执行：pip install python-docx")
    sys.exit(1)


# ============================================================================
# 测绘技术设计书格式规范（基于 CH/T 1004-2005）
# ============================================================================

# 页面设置
PAGE_WIDTH = Cm(21.0)  # A4 宽度
PAGE_HEIGHT = Cm(29.7)  # A4 高度
LEFT_MARGIN = Cm(2.5)  # 左边距
RIGHT_MARGIN = Cm(2.0)  # 右边距
TOP_MARGIN = Cm(2.5)  # 上边距
BOTTOM_MARGIN = Cm(2.0)  # 下边距

# 字体设置
FONT_SONG = "宋体"
FONT_HEI = "黑体"
FONT_KAI = "楷体"
FONT_FANGSONG = "仿宋"

# 标题字号
FONT_SIZE_COVER_TITLE = Pt(22)  # 封面标题：二号（约22pt）
FONT_SIZE_COVER_SUBTITLE = Pt(16)  # 封面副标题：三号
FONT_SIZE_H1 = Pt(16)  # 一级标题：三号
FONT_SIZE_H2 = Pt(14)  # 二级标题：四号
FONT_SIZE_H3 = Pt(12)  # 三级标题：小四
FONT_SIZE_BODY = Pt(12)  # 正文：小四
FONT_SIZE_TABLE = Pt(10.5)  # 表格：五号
FONT_SIZE_CAPTION = Pt(10.5)  # 图表说明：五号

# 行距
LINE_SPACING = 1.5  # 1.5倍行距
LINE_SPACING_TITLE = 1.3  # 标题行距


class DocxFormatter:
    """Word 文档格式化器"""

    def __init__(self):
        self.doc = Document()
        self._setup_page()
        self._setup_styles()

    def _setup_page(self):
        """设置页面格式"""
        section = self.doc.sections[0]
        section.page_width = PAGE_WIDTH
        section.page_height = PAGE_HEIGHT
        section.left_margin = LEFT_MARGIN
        section.right_margin = RIGHT_MARGIN
        section.top_margin = TOP_MARGIN
        section.bottom_margin = BOTTOM_MARGIN

    def _setup_styles(self):
        """设置文档样式"""
        styles = self.doc.styles

        # 正文样式
        body_style = styles["Normal"]
        body_style.font.name = FONT_SONG
        body_style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
        body_style.font.size = FONT_SIZE_BODY
        body_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        body_style.paragraph_format.first_line_indent = Cm(0.74)  # 两字符缩进

        # 一级标题样式
        self._create_heading_style("Heading 1", FONT_SIZE_H1, FONT_HEI, bold=True)

        # 二级标题样式
        self._create_heading_style("Heading 2", FONT_SIZE_H2, FONT_HEI, bold=True)

        # 三级标题样式
        self._create_heading_style("Heading 3", FONT_SIZE_H3, FONT_HEI, bold=True)

        # 四级标题样式
        self._create_heading_style("Heading 4", FONT_SIZE_BODY, FONT_HEI, bold=True)

    def _create_heading_style(self, style_name: str, font_size: Pt, font_name: str, bold: bool = False):
        """创建标题样式"""
        style = self.doc.styles[style_name]
        style.font.name = font_name
        style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
        style.font.size = font_size
        style.font.bold = bold
        style.font.color.rgb = RGBColor(0, 0, 0)  # 黑色
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.first_line_indent = Pt(0)  # 标题不缩进

    def create_cover(self, title: str, subtitle: Optional[str] = None, 
                     project_name: Optional[str] = None, author: Optional[str] = None,
                     date: Optional[str] = None):
        """
        创建封面页

        根据CH/T 1004-2005规范，技术设计书封面应包含：
        - 项目名称
        - 文档标题
        - 编制单位
        - 编制日期
        """
        # 封面使用单独的节
        section = self.doc.add_section()
        section.page_width = PAGE_WIDTH
        section.page_height = PAGE_HEIGHT
        section.left_margin = LEFT_MARGIN
        section.right_margin = RIGHT_MARGIN
        section.top_margin = TOP_MARGIN
        section.bottom_margin = BOTTOM_MARGIN

        # 顶部空白
        for _ in range(3):
            self.doc.add_paragraph()

        # 项目名称（如果有）
        if project_name:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(project_name)
            run.font.name = FONT_HEI
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_HEI)
            run.font.size = FONT_SIZE_COVER_SUBTITLE
            self.doc.add_paragraph()

        # 主标题
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.font.name = FONT_HEI
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_HEI)
        run.font.size = FONT_SIZE_COVER_TITLE
        run.font.bold = True

        # 副标题（如果有）
        if subtitle:
            self.doc.add_paragraph()
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(subtitle)
            run.font.name = FONT_HEI
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_HEI)
            run.font.size = FONT_SIZE_COVER_SUBTITLE

        # 中间空白
        for _ in range(8):
            self.doc.add_paragraph()

        # 编制单位
        if author:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(author)
            run.font.name = FONT_SONG
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
            run.font.size = FONT_SIZE_H2

        # 编制日期
        if date:
            self.doc.add_paragraph()
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(date)
            run.font.name = FONT_SONG
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
            run.font.size = FONT_SIZE_BODY
        else:
            self.doc.add_paragraph()
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(datetime.now().strftime("%Y年%m月"))
            run.font.name = FONT_SONG
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
            run.font.size = FONT_SIZE_BODY

        # 分页符
        self.doc.add_page_break()

    def add_toc(self):
        """添加目录页"""
        # 目录标题
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("目  录")
        run.font.name = FONT_HEI
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_HEI)
        run.font.size = FONT_SIZE_H1
        run.font.bold = True

        self.doc.add_paragraph()

        # 添加目录域
        paragraph = self.doc.add_paragraph()
        run = paragraph.add_run()
        fld_char = OxmlElement("w:fldChar")
        fld_char.set(qn("w:fldCharType"), "begin")
        run._r.append(fld_char)

        run = paragraph.add_run()
        instr_text = OxmlElement("w:instrText")
        instr_text.text = 'TOC \\o "1-3" \\h \\z \\u'
        run._r.append(instr_text)

        run = paragraph.add_run()
        fld_char = OxmlElement("w:fldChar")
        fld_char.set(qn("w:fldCharType"), "separate")
        run._r.append(fld_char)

        run = paragraph.add_run("请右键点击更新目录")
        run.font.name = FONT_SONG
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)

        run = paragraph.add_run()
        fld_char = OxmlElement("w:fldChar")
        fld_char.set(qn("w:fldCharType"), "end")
        run._r.append(fld_char)

        # 分页符
        self.doc.add_page_break()

    def parse_markdown(self, md_content: str) -> list:
        """
        解析 Markdown 内容为结构化数据

        返回格式：
        [
            {"type": "h1", "text": "...", "level": 1},
            {"type": "h2", "text": "...", "level": 2},
            {"type": "paragraph", "text": "..."},
            {"type": "table", "headers": [...], "rows": [...]},
            {"type": "code", "text": "..."},
            {"type": "blockquote", "text": "..."},
        ]
        """
        elements = []
        lines = md_content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # 跳过空行
            if not line.strip():
                i += 1
                continue

            # 标题
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                elements.append({"type": f"h{level}", "text": text, "level": level})
                i += 1
                continue

            # 表格
            if line.strip().startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1

                if len(table_lines) >= 2:
                    # 解析表头
                    headers = [cell.strip() for cell in table_lines[0].split("|")[1:-1]]
                    # 跳过分隔行
                    rows = []
                    for row_line in table_lines[2:]:
                        row = [cell.strip() for cell in row_line.split("|")[1:-1]]
                        rows.append(row)
                    elements.append({"type": "table", "headers": headers, "rows": rows})
                continue

            # 代码块
            if line.strip().startswith("```"):
                code_lines = []
                i += 1  # 跳过开始标记
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # 跳过结束标记
                elements.append({"type": "code", "text": "\n".join(code_lines)})
                continue

            # 引用块
            if line.strip().startswith(">"):
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    quote_lines.append(lines[i].strip()[1:].strip())
                    i += 1
                elements.append({"type": "blockquote", "text": " ".join(quote_lines)})
                continue

            # 列表
            list_match = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.+)$", line)
            if list_match:
                indent = len(list_match.group(1))
                text = list_match.group(3)
                elements.append({"type": "list_item", "text": text, "indent": indent})
                i += 1
                continue

            # 普通段落
            paragraph_lines = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if (not next_line.strip() or 
                    next_line.startswith("#") or 
                    next_line.startswith("|") or
                    next_line.startswith("```") or
                    next_line.startswith(">") or
                    re.match(r"^\s*([-*+]|\d+\.)\s+", next_line)):
                    break
                paragraph_lines.append(next_line)
                i += 1

            elements.append({"type": "paragraph", "text": " ".join(paragraph_lines)})

        return elements

    def add_content_from_markdown(self, md_content: str):
        """从 Markdown 内容添加正文"""
        elements = self.parse_markdown(md_content)
        in_list = False

        for element in elements:
            if element["type"].startswith("h"):
                level = element["level"]
                text = element["text"]
                # 使用标准编号格式
                heading = self.doc.add_heading(text, level=level)
                heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

            elif element["type"] == "paragraph":
                text = element["text"]
                # 处理内联格式
                p = self.doc.add_paragraph()
                self._add_formatted_text(p, text)

            elif element["type"] == "table":
                self._add_table(element["headers"], element["rows"])

            elif element["type"] == "code":
                p = self.doc.add_paragraph()
                run = p.add_run(element["text"])
                run.font.name = "Courier New"
                run.font.size = Pt(9)

            elif element["type"] == "blockquote":
                p = self.doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1)
                run = p.add_run(element["text"])
                run.font.name = FONT_KAI
                run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_KAI)
                run.font.size = FONT_SIZE_BODY
                run.italic = True

            elif element["type"] == "list_item":
                p = self.doc.add_paragraph(style="List Bullet")
                self._add_formatted_text(p, element["text"])
                if element["indent"] > 0:
                    p.paragraph_format.left_indent = Cm(element["indent"] * 0.5)

    def _add_formatted_text(self, paragraph, text: str):
        """添加带格式的文本（处理加粗、斜体、代码等）"""
        # 简单的格式处理
        parts = []
        current = ""
        i = 0

        while i < len(text):
            # 加粗 **text**
            if text[i:i+2] == "**":
                if current:
                    parts.append(("normal", current))
                    current = ""
                j = text.find("**", i+2)
                if j != -1:
                    parts.append(("bold", text[i+2:j]))
                    i = j + 2
                    continue
            # 斜体 *text*
            elif text[i] == "*" and (i == 0 or text[i-1] != "*"):
                if current:
                    parts.append(("normal", current))
                    current = ""
                j = text.find("*", i+1)
                if j != -1 and text[j-1:j+1] != "**":
                    parts.append(("italic", text[i+1:j]))
                    i = j + 1
                    continue
            # 行内代码 `code`
            elif text[i] == "`":
                if current:
                    parts.append(("normal", current))
                    current = ""
                j = text.find("`", i+1)
                if j != -1:
                    parts.append(("code", text[i+1:j]))
                    i = j + 1
                    continue

            current += text[i]
            i += 1

        if current:
            parts.append(("normal", current))

        # 添加到段落
        for fmt, txt in parts:
            run = paragraph.add_run(txt)
            run.font.name = FONT_SONG
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
            run.font.size = FONT_SIZE_BODY

            if fmt == "bold":
                run.font.bold = True
            elif fmt == "italic":
                run.italic = True
            elif fmt == "code":
                run.font.name = "Courier New"
                run.font.size = Pt(10)

    def _add_table(self, headers: list, rows: list):
        """添加表格"""
        table = self.doc.add_table(rows=len(rows) + 1, cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # 表头
        header_row = table.rows[0]
        for i, header in enumerate(headers):
            cell = header_row.cells[i]
            cell.text = header
            # 设置表头样式
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.name = FONT_HEI
                    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_HEI)
                    run.font.size = FONT_SIZE_TABLE
                    run.font.bold = True
            # 设置背景色
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "E7E6E6")
            cell._tc.get_or_add_tcPr().append(shading)

        # 数据行
        for row_idx, row_data in enumerate(rows):
            row = table.rows[row_idx + 1]
            for col_idx, cell_text in enumerate(row_data):
                cell = row.cells[col_idx]
                cell.text = cell_text
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = FONT_SONG
                        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
                        run.font.size = FONT_SIZE_TABLE

    def add_header_footer(self, title: str):
        """添加页眉页脚"""
        for section in self.doc.sections:
            # 页眉
            header = section.header
            p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(title)
            run.font.name = FONT_SONG
            run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_SONG)
            run.font.size = Pt(9)

            # 添加页眉下划线
            p_format = p.paragraph_format
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "6")
            bottom.set(qn("w:space"), "1")
            bottom.set(qn("w:color"), "000000")
            pBdr.append(bottom)
            p._p.get_or_add_pPr().append(pBdr)

            # 页脚（页码）
            footer = section.footer
            p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # 添加页码域
            run = p.add_run()
            fld_char1 = OxmlElement("w:fldChar")
            fld_char1.set(qn("w:fldCharType"), "begin")
            run._r.append(fld_char1)

            run = p.add_run()
            instr_text = OxmlElement("w:instrText")
            instr_text.text = "PAGE"
            run._r.append(instr_text)

            run = p.add_run()
            fld_char2 = OxmlElement("w:fldChar")
            fld_char2.set(qn("w:fldCharType"), "end")
            run._r.append(fld_char2)

    def save(self, output_path: str):
        """保存文档"""
        self.doc.save(output_path)
        print(f"文档已保存至：{output_path}")


def format_docx(input_md: str, output_docx: str, 
                title: str = "技术设计书",
                subtitle: Optional[str] = None,
                project_name: Optional[str] = None,
                author: Optional[str] = None,
                date: Optional[str] = None):
    """
    将 Markdown 文件转换为格式规范的 Word 文档
    
    参数：
        input_md: Markdown 文件路径
        output_docx: 输出 Word 文件路径
        title: 文档标题
        subtitle: 副标题
        project_name: 项目名称
        author: 编制单位
        date: 编制日期
    """
    # 读取 Markdown 内容
    md_path = Path(input_md)
    if not md_path.exists():
        print(f"错误：文件不存在 {input_md}")
        return False

    md_content = md_path.read_text(encoding="utf-8")

    # 创建格式化器
    formatter = DocxFormatter()

    # 创建封面
    formatter.create_cover(
        title=title,
        subtitle=subtitle,
        project_name=project_name,
        author=author,
        date=date
    )

    # 添加目录
    formatter.add_toc()

    # 添加正文内容
    formatter.add_content_from_markdown(md_content)

    # 添加页眉页脚
    formatter.add_header_footer(title)

    # 保存文档
    formatter.save(output_docx)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="测绘技术设计书 Word 文档格式化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python docx_formatter.py input.md output.docx
  python docx_formatter.py input.md output.docx --title "航空摄影测量技术设计书" --author "XX测绘院"
        """
    )
    parser.add_argument("input", help="输入的 Markdown 文件路径")
    parser.add_argument("output", help="输出的 Word 文件路径")
    parser.add_argument("--title", default="技术设计书", help="文档标题")
    parser.add_argument("--subtitle", help="副标题")
    parser.add_argument("--project", help="项目名称")
    parser.add_argument("--author", help="编制单位")
    parser.add_argument("--date", help="编制日期（默认当前月份）")

    args = parser.parse_args()

    success = format_docx(
        input_md=args.input,
        output_docx=args.output,
        title=args.title,
        subtitle=args.subtitle,
        project_name=args.project,
        author=args.author,
        date=args.date
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()