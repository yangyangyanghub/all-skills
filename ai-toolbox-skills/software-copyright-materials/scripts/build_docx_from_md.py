#!/usr/bin/env python3
"""Build final DOCX/TXT files from confirmed Markdown drafts."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from common import ensure_dir, read_json, safe_filename

try:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Inches, Pt, RGBColor

    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False


BLACK_RGB = "000000"


def strip_markdown_links(text: str) -> str:
    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    return text


def parse_application_lines(md_path: Path) -> tuple[list[str], list[str]]:
    lines = md_path.read_text(encoding="utf-8", errors="replace").splitlines()
    fields = [line.strip() for line in lines if line.strip().startswith("➤")]
    warnings = [line for line in fields if "待用户确认" in line]
    return fields, warnings


def parse_application_field(md_path: Path, field_name: str) -> str:
    if not md_path.exists():
        return ""
    prefix = f"➤{field_name}："
    for line in md_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return ""


def application_version(draft_dir: Path) -> str:
    version = parse_application_field(draft_dir / "申请表信息.md", "版本号")
    if "待用户确认" in version:
        return ""
    return version


def application_software_name(draft_dir: Path) -> str:
    name = parse_application_field(draft_dir / "申请表信息.md", "软件全称")
    if "待用户确认" in name:
        return ""
    return name


def write_application_txt(draft_dir: Path, out_dir: Path) -> tuple[Path | None, list[str]]:
    md_path = draft_dir / "申请表信息.md"
    if not md_path.exists():
        return None, ["缺少草稿/申请表信息.md"]
    fields, warnings = parse_application_lines(md_path)
    out_path = out_dir / "申请表信息.txt"
    out_path.write_text("\n".join(fields) + "\n", encoding="utf-8")
    return out_path, warnings


def parse_copyright_holder(holder: str) -> tuple[str, list[str]]:
    """解析著作权人字段：返回 (原始片段列表, 单位全称列表)。

    兼容两种写法：
    - 逗号/顿号混合：`单位A，统一社会信用代码：CODE、单位B，统一社会信用代码：CODE`
    - 纯顿号分隔：`单位A、单位B`
    单位全称去掉“统一社会信用代码：XXX”部分，只保留单位名称。
    """
    holder = re.sub(r"（[^（）]*统一社会信用代码[^（）]*）", "", holder)
    holder = holder.strip("；; ）(").strip()
    # 先按顿号/分号拆分成单位块（单位之间用 、 或 ； 分隔）
    blocks = re.split(r"[、；;]+", holder)
    names = [b.strip() for b in blocks if b.strip()]
    # 每个单位块去掉 “，统一社会信用代码：XXX” 部分，保留纯单位名
    clean = []
    for n in names:
        c = re.sub(r"[，,]\s*统一社会信用代码[:：]?\s*\S+", "", n)
        c = c.strip("；; ）(，,、").strip()
        if c:
            clean.append(c)
    return names, clean


def should_generate_agreement(draft_dir: Path) -> bool:
    """判断是否需要《合作开发协议书》：开发方式为合作开发，且著作权人包含两个及以上单位。
    开发方式必须是已确认的“合作开发”，不含“待确认”字样，避免未确认时误生成。"""
    app_md = draft_dir / "申请表信息.md"
    dev_mode = parse_application_field(app_md, "开发方式")
    holder = parse_application_field(app_md, "著作权人")
    if "待确认" in dev_mode or "合作" not in dev_mode:
        return False
    _, clean = parse_copyright_holder(holder)
    return len(clean) >= 2


def build_cooperation_agreement(
    draft_dir: Path,
    out_dir: Path,
    software_name: str,
    version: str,
) -> tuple[Path | None, list[str]]:
    """生成《合作开发协议书》到正式资料。仅当开发方式为合作开发且著作权人含两个及以上单位时生成。
    返回 (输出path, 警告列表)；不符合条件返回 (None, [])。"""
    if not should_generate_agreement(draft_dir):
        return None, []

    app_md = draft_dir / "申请表信息.md"
    software = f"{software_name} {version}"
    holder = parse_application_field(app_md, "著作权人")
    _, unit_names = parse_copyright_holder(holder)

    # 取前两个单位作为甲方乙方（合作开发通常为两方；多余单位归入甲方）
    jia = unit_names[0] if unit_names else "甲方单位"
    yi = unit_names[1] if len(unit_names) > 1 else "乙方单位"
    # 信用代码
    jia_code, yi_code = "", ""
    raw_codes = re.findall(r"统一社会信用代码[:：]?([A-Za-z0-9]+)", holder)
    if len(raw_codes) >= 2:
        jia_code, yi_code = raw_codes[0], raw_codes[1]
    elif raw_codes:
        jia_code = raw_codes[0]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.17)
    sec.right_margin = Cm(3.17)

    def set_run_font(run: Any, size: float, bold: bool = False) -> None:
        run.font.name = "宋体"
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor(0, 0, 0)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    def add_para(text: str, size: float = 11, bold: bool = False, space_after: float = 6) -> None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(space_after)
        r = p.add_run(text)
        set_run_font(r, size, bold)

    def add_clause(title: str, lines: list[str]) -> None:
        """条款标题与各序号项各自独立成行：
        - 条款标题独立成段，左对齐
        - 每个序号项独立成段，左对齐，缩进 2 个全角空格
        """
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        title_p.paragraph_format.space_before = Pt(8)
        title_p.paragraph_format.space_after = Pt(4)
        title_run = title_p.add_run(title)
        set_run_font(title_run, 11, bold=False)
        for line in lines:
            item_p = doc.add_paragraph()
            item_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            item_p.paragraph_format.space_after = Pt(4)
            item_p.paragraph_format.left_indent = Pt(22)  # 约 2 个全角空格缩进
            item_p.paragraph_format.first_line_indent = Pt(0)
            item_run = item_p.add_run(line)
            set_run_font(item_run, 11, bold=False)

    # 标题
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_after = Pt(18)
    tr = t.add_run("合作开发协议书")
    set_run_font(tr, 18, bold=True)

    # 甲乙方
    jia_info = f"甲方：{jia}" + (f"，统一社会信用代码{jia_code}" if jia_code else "")
    yi_info = f"乙方：{yi}" + (f"，统一社会信用代码{yi_code}" if yi_code else "")
    add_para(jia_info, space_after=3)
    add_para(yi_info, space_after=10)

    # 鉴于
    add_para(
        f"鉴于，协议各方均从事计算机软件专业开发，能够进行创造性的软件开发活动。并且，协议各方有意愿共同从事 {software} 软件的开发工作。"
        "为了规范各方的权利义务，在《中华人民共和国民法典》及其他相关法规政策的原则指导下，订立本协议书，各方共同遵守：",
        space_after=10,
    )

    # 十条
    add_clause("第一条　合作宗旨", ["为完成本软件的开发工作，并共同享有开发成果而合作。"])
    add_clause("第二条　合作项目和范围", [f"协议各方共同开发 {software} 软件，合作范围包括软件的代码编写、调试、测试等开发工作。"])
    add_clause("第三条　合作期限", ["合作期限为五年。"])
    add_clause(
        "第四条　合作方式",
        [
            "１．协议各方按照软件编程工作的正常分工进行编写，任何一方不得随意更改软件的重大功能和事项，以免对其余各方造成履约困难。",
            "２．合作各方应坚持勤勉努力诚实信用的原则，进行各方分别负责的软件的编程工作，并考虑到各方软件的兼容和接合。如部分合作人发生特殊技术困难，其余合作方有义务为其提供合理适当的技术帮助。",
        ],
    )
    add_clause(
        "第五条　知识产权",
        [
            "１．各方编写的软件源代码、技术文档及汇编而成的程序本身，其著作权均由合作方共同享有。",
            "２．各作各方在编写软件的过程中，不得有侵犯他人知识产权的行为，否则，应对外承担全部侵权责任。",
        ],
    )
    add_clause(
        "第六条　协议变更",
        [
            "１．经合作各方协商同意，本协议可以作相应变更；",
            "２．任何合作方未经与其他各方协商，擅自变更本协议条款或者将本协议权利义务转让他人，均为无效。",
        ],
    )
    add_clause(
        "第七条　禁止行为",
        [
            "１．未经全体合作人同意，禁止任何合作人私自以团体名义进行业务活动；如其业务获得利益归合作各方共有，造成损失按实际损失赔偿。",
            "２．禁止合作人经营与团队相竞争的业务。",
            "３．禁止合作方泄露本协议所涉及的相关商业秘密。",
            "４．如合作人违反上述各条，应按实际损失赔偿。",
        ],
    )
    add_clause("第八条　合作的终止", ["合作开发活动因以下事由之一得终止：①全体合作人同意终止合作关系；②合作项目因技术原因，根本不能完成；③合作项目违反法律被撤销。"])
    add_clause("第九条　纠纷的解决", ["合作各方之间如发生纠纷，应共同协商，本着有利于事业发展的原则予以解决。如协商不成，可以诉诸法院。"])
    add_clause("第十条", ["本协议如有未尽事宜，应由合作人集体讨论补充或修改。补充和修改的内容与本协议具有同等效力。"])

    # 签署区
    add_para("各方签署：", space_after=12)
    add_para(f"甲方：{jia}", space_after=36)
    add_para(f"乙方：{yi}", space_after=36)
    add_para("签署日期：　　　　年　　月　　日", space_after=0)

    out_path = out_dir / "合作开发协议书.docx"
    doc.save(out_path)
    return out_path, []


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return read_json(path)


def confirmation_issues(workdir: Path) -> list[str]:
    draft_dir = workdir / "草稿"
    issues: list[str] = []

    business = read_json_if_exists(draft_dir / "业务理解.json")
    if not business or not business.get("user_confirmed"):
        issues.append("业务理解尚未确认：请确认 草稿/业务理解.md 后记录 `business` 门禁")

    selection = read_json_if_exists(draft_dir / "代码文件选择.json")
    if not selection or not selection.get("user_confirmed"):
        issues.append("代码文件选择尚未确认：请确认 草稿/代码文件选择.json 后记录 `code-selection` 门禁")

    screenshot = read_json_if_exists(workdir / "截图方式确认.json")
    if not screenshot.get("screenshot_method_confirmed"):
        issues.append("截图方式尚未确认：请选择截图方式后记录 `screenshot-method` 门禁")

    app_md = draft_dir / "申请表信息.md"
    if app_md.exists():
        _, warnings = parse_application_lines(app_md)
        if warnings:
            issues.append("申请表信息仍包含“待用户确认”字段")
    else:
        issues.append("缺少 草稿/申请表信息.md")

    app_confirmation = read_json_if_exists(draft_dir / "申请表字段确认.json")
    if not app_confirmation.get("application_fields_confirmed"):
        issues.append("申请表字段尚未确认：请补全字段后记录 `application-fields` 门禁")

    markdown_confirmation = read_json_if_exists(draft_dir / "最终生成确认.json")
    if not markdown_confirmation.get("markdown_confirmed"):
        issues.append("Markdown 草稿尚未最终确认：请确认全部草稿后记录 `markdown` 门禁")

    return issues


def parse_code_pages(md_path: Path) -> list[tuple[int, list[str]]]:
    pages: list[tuple[int, list[str]]] = []
    current_no: int | None = None
    current_lines: list[str] = []
    in_fence = False

    for raw in md_path.read_text(encoding="utf-8", errors="replace").splitlines():
        page_match = re.match(r"^##\s+第\s*(\d+)\s*页", raw.strip())
        if page_match:
            if current_no is not None:
                pages.append((current_no, current_lines))
            current_no = int(page_match.group(1))
            current_lines = []
            in_fence = False
            continue
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if current_no is not None and in_fence:
            current_lines.append(raw)

    if current_no is not None:
        pages.append((current_no, current_lines))
    return pages


def set_run_font(run: Any, name: str, size_pt: float) -> None:
    run.font.name = name
    run.font.size = Pt(size_pt)
    try:
        run.font.color.rgb = RGBColor(0, 0, 0)
    except Exception:
        pass
    try:
        run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    except Exception:
        pass


def set_run_font_mixed(run: Any, cjk_name: str, latin_name: str, size_pt: float) -> None:
    """中西文分离字体：中文用 cjk_name，西文/数字用 latin_name。"""
    run.font.name = latin_name
    run.font.size = Pt(size_pt)
    try:
        run.font.color.rgb = RGBColor(0, 0, 0)
    except Exception:
        pass
    try:
        run._element.rPr.rFonts.set(qn("w:eastAsia"), cjk_name)
        run._element.rPr.rFonts.set(qn("w:ascii"), latin_name)
        run._element.rPr.rFonts.set(qn("w:hAnsi"), latin_name)
    except Exception:
        pass


def set_normal_font(document: Any, name: str = "SimSun", size_pt: float = 10.5) -> None:
    style = document.styles["Normal"]
    style.font.name = name
    style.font.size = Pt(size_pt)
    try:
        style.font.color.rgb = RGBColor(0, 0, 0)
    except Exception:
        pass
    try:
        style._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    except Exception:
        pass


def set_style_black(document: Any) -> None:
    for style_name in ("Normal", "Heading 1", "Heading 2", "Heading 3", "List Bullet", "List Number"):
        try:
            document.styles[style_name].font.color.rgb = RGBColor(0, 0, 0)
        except Exception:
            pass


def force_black_document(document: Any) -> None:
    set_style_black(document)
    containers = [document]
    for section in document.sections:
        containers.extend([section.header, section.footer])
    for container in containers:
        for paragraph in container.paragraphs:
            for run in paragraph.runs:
                try:
                    run.font.color.rgb = RGBColor(0, 0, 0)
                except Exception:
                    pass
        for table in container.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            try:
                                run.font.color.rgb = RGBColor(0, 0, 0)
                            except Exception:
                                pass


def configure_a4(document: Any, section: Any | None = None, include_margins: bool = True) -> None:
    sec = section if section is not None else document.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    if include_margins:
        sec.top_margin = Cm(2.54)
        sec.bottom_margin = Cm(2.54)
        sec.left_margin = Cm(3.17)
        sec.right_margin = Cm(3.17)


def configure_code_a4(document: Any, section: Any | None = None) -> None:
    sec = section if section is not None else document.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)


def add_page_field(paragraph: Any, size_pt: float = 8.0, cjk_name: str = "SimSun", latin_name: str | None = None) -> None:
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    result = OxmlElement("w:t")
    result.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    for element in (begin, instr, separate, result, end):
        run = paragraph.add_run()
        run._r.append(element)
        if latin_name:
            set_run_font_mixed(run, cjk_name, latin_name, size_pt)
        else:
            set_run_font(run, cjk_name, size_pt)


def set_code_header(document: Any, software_name: str, version: str, section: Any | None = None) -> None:
    sec = section if section is not None else document.sections[0]
    sec.header.is_linked_to_previous = False
    header = sec.header
    header.paragraphs[0].text = "" if header.paragraphs else None

    # Build a two-column header: software name on the left, page number on the right.
    table = header.add_table(rows=1, cols=2, width=Cm(17.5))
    table.autofit = True
    left_cell = table.rows[0].cells[0]
    right_cell = table.rows[0].cells[1]

    left_para = left_cell.paragraphs[0]
    left_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    left_para.paragraph_format.space_before = Pt(0)
    left_para.paragraph_format.space_after = Pt(0)
    left_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    left_para.paragraph_format.line_spacing = Pt(12)
    left_run = left_para.add_run(f"{software_name} {version}")
    set_run_font(left_run, "SimSun", 8)

    right_para = right_cell.paragraphs[0]
    right_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right_para.paragraph_format.space_before = Pt(0)
    right_para.paragraph_format.space_after = Pt(0)
    right_para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    right_para.paragraph_format.line_spacing = Pt(12)
    prefix = right_para.add_run("第 ")
    set_run_font(prefix, "SimSun", 8)
    add_page_field(right_para)
    suffix = right_para.add_run(" 页")
    set_run_font(suffix, "SimSun", 8)

    # Remove borders from the header table
    for cell in table.rows[0].cells:
        tc_pr = cell._tc.get_or_add_tcPr()
        tc_borders = OxmlElement("w:tcBorders")
        for border_name in ("top", "left", "bottom", "right"):
            border = OxmlElement(f"w:{border_name}")
            border.set(qn("w:val"), "nil")
            tc_borders.append(border)
        tc_pr.append(tc_borders)


def add_code_cover(document: Any, software_name: str, version: str, unit_name: str = "") -> Any:
    """在文档开头加入独立封面节（无页眉）：居中标题 + 单位落款，返回代码正文用的分节。"""
    cover_section = document.sections[0]
    configure_code_a4(document, cover_section)

    # 封面标题：软件全称 + 源代码
    title = f"{software_name}源代码"
    title_p = document.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(220)
    title_p.paragraph_format.space_after = Pt(0)
    title_run = title_p.add_run(title)
    set_run_font(title_run, "方正小标宋简体", 22)
    title_run.font.bold = True

    # 单位落款
    if unit_name:
        unit_p = document.add_paragraph()
        unit_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        unit_p.paragraph_format.space_before = Pt(30)
        unit_p.paragraph_format.space_after = Pt(0)
        unit_run = unit_p.add_run(unit_name)
        set_run_font(unit_run, "仿宋", 15)

    # 新建分节承载代码正文（封面节不加页眉）
    code_section = document.add_section(WD_SECTION.NEW_PAGE)
    code_section.header.is_linked_to_previous = False
    code_section.footer.is_linked_to_previous = False
    return code_section


def build_code_docx_python(
    md_path: Path,
    out_path: Path,
    software_name: str,
    version: str,
    unit_name: str = "",
    add_cover: bool = False,
) -> None:
    pages = parse_code_pages(md_path)
    if not pages:
        raise RuntimeError(f"No code pages parsed from {md_path}")

    document = Document()
    set_normal_font(document, "DengXian", 10.0)
    set_style_black(document)

    if add_cover:
        code_section = add_code_cover(document, software_name, version, unit_name)
        set_code_header(document, software_name, version, code_section)
        configure_code_a4(document, code_section)
    else:
        configure_code_a4(document)
        set_code_header(document, software_name, version)

    # 后30页文档页码从31开始，实现前后文档连续编号1-60
    start_page_no = pages[0][0] if pages else 1
    if start_page_no != 1:
        pg_num_type = OxmlElement("w:pgNumType")
        pg_num_type.set(qn("w:start"), str(start_page_no))
        body_section = document.sections[-1]
        body_section._sectPr.append(pg_num_type)

    for index, (page_no, lines) in enumerate(pages):
        for line in lines:
            # 参考格式：List Paragraph 样式 + 0.5in 左缩进 + 固定行距 12pt（满足软著"每页不少于50行"硬标准）
            # A4 上下边距各 2.0cm，可用高度约 728.5pt，12pt 固定行距每页可排下约 60 行；
            # 字号 10pt 配 12pt 行距（1.2 倍），与抽取的 lines_per_page=60 对齐：一个页块恰好一页。
            p = document.add_paragraph(style="List Paragraph")
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            p.paragraph_format.line_spacing = Pt(12)
            run = p.add_run(line if line else " ")
            set_run_font(run, "DengXian", 10.0)

    force_black_document(document)
    document.save(out_path)


def paragraph_xml(text: str, font: str = "SimSun", size_half_points: int = 21, align: str | None = None, line_twips: int = 240) -> str:
    align_xml = f'<w:jc w:val="{align}"/>' if align else ""
    escaped = html.escape(text)
    return (
        "<w:p>"
        f"<w:pPr>{align_xml}<w:spacing w:after=\"0\" w:line=\"{line_twips}\" w:lineRule=\"exact\"/></w:pPr>"
        "<w:r>"
        f"<w:rPr><w:rFonts w:ascii=\"{font}\" w:hAnsi=\"{font}\" w:eastAsia=\"{font}\"/>"
        f"<w:color w:val=\"{BLACK_RGB}\"/>"
        f"<w:sz w:val=\"{size_half_points}\"/><w:szCs w:val=\"{size_half_points}\"/></w:rPr>"
        f"<w:t xml:space=\"preserve\">{escaped}</w:t>"
        "</w:r>"
        "</w:p>"
    )


def page_break_xml() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def page_field_runs_xml() -> str:
    return (
        '<w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>'
        f'<w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
        '<w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>'
        f'<w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
        '<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>'
        f'<w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
        '<w:fldChar w:fldCharType="separate"/></w:r>'
        '<w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>'
        f'<w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
        '<w:t>1</w:t></w:r>'
        '<w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>'
        f'<w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
        '<w:fldChar w:fldCharType="end"/></w:r>'
    )


def header_xml(header_text: str) -> str:
    """Build a two-column header: software name left, page number right."""
    escaped = html.escape(header_text)
    # Use a borderless table for left/right alignment in header
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:tbl>
    <w:tblPr>
      <w:tblW w:w="5000" w:type="pct"/>
      <w:tblBorders>
        <w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/>
      </w:tblBorders>
    </w:tblPr>
    <w:tr>
      <w:tc>
        <w:p>
          <w:pPr><w:jc w:val="left"/><w:spacing w:after="0" w:line="240" w:lineRule="exact"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/><w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr><w:t xml:space="preserve">{escaped}</w:t></w:r>
        </w:p>
      </w:tc>
      <w:tc>
        <w:p>
          <w:pPr><w:jc w:val="right"/><w:spacing w:after="0" w:line="240" w:lineRule="exact"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/><w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr><w:t xml:space="preserve">第 </w:t></w:r>
          {page_field_runs_xml()}
          <w:r><w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/><w:color w:val="{BLACK_RGB}"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr><w:t xml:space="preserve"> 页</w:t></w:r>
        </w:p>
      </w:tc>
    </w:tr>
  </w:tbl>
</w:hdr>"""


def minimal_docx(out_path: Path, body_xml: str, header_text: str | None = None, start_page: int = 1) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    header_rel = (
        '<Relationship Id="rIdHeader1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
        if header_text
        else ""
    )
    doc_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{header_rel}</Relationships>"""
    styles = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/><w:color w:val="{BLACK_RGB}"/><w:sz w:val="21"/></w:rPr>
  </w:style>
</w:styles>"""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {body_xml}
      <w:sectPr>
        {'<w:headerReference w:type="default" r:id="rIdHeader1"/>' if header_text else ''}
        {'<w:pgNumType w:start="' + str(start_page) + '"/>' if start_page != 1 else ''}
        <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1418" w:header="283" w:footer="283" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)
        zf.writestr("word/styles.xml", styles)
        zf.writestr("word/document.xml", document)
        if header_text:
            zf.writestr("word/header1.xml", header_xml(header_text))


def force_black_xml(xml: str) -> str:
    xml = re.sub(r"<w:hyperlink\b[^>]*>", "", xml)
    xml = xml.replace("</w:hyperlink>", "")
    xml = re.sub(r"<w:color\b[^>]*/>", f'<w:color w:val="{BLACK_RGB}"/>', xml)

    def ensure_rpr_color(match: re.Match[str]) -> str:
        value = match.group(0)
        if "<w:color" in value:
            return value
        return value.replace("</w:rPr>", f'<w:color w:val="{BLACK_RGB}"/></w:rPr>')

    xml = re.sub(r"<w:rPr\b[^>]*>.*?</w:rPr>", ensure_rpr_color, xml, flags=re.S)
    xml = re.sub(r"<w:r>(?!<w:rPr>)", f'<w:r><w:rPr><w:color w:val="{BLACK_RGB}"/></w:rPr>', xml)
    return xml


def normalize_docx_text_color(docx_path: Path) -> None:
    tmp_path = docx_path.with_suffix(docx_path.suffix + ".tmp")
    color_xml_parts = (
        "word/document.xml",
        "word/styles.xml",
        "word/numbering.xml",
        "word/header",
        "word/footer",
    )
    with zipfile.ZipFile(docx_path, "r") as src, zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename.endswith(".xml") and item.filename.startswith(color_xml_parts):
                text = data.decode("utf-8")
                data = force_black_xml(text).encode("utf-8")
            elif item.filename.endswith(".rels"):
                text = data.decode("utf-8", errors="ignore")
                if "hyperlink" in text:
                    text = re.sub(r'\s*<Relationship\b[^>]*Type="[^"]*/hyperlink"[^>]*/>', "", text)
                    data = text.encode("utf-8")
            dst.writestr(item, data)
    # Windows 上 replace 可能失败，先删除目标文件再重命名
    if docx_path.exists():
        docx_path.unlink()
    tmp_path.replace(docx_path)


def next_header_part(names: set[str]) -> tuple[str, str]:
    index = 1
    while f"word/header{index}.xml" in names:
        index += 1
    return f"word/header{index}.xml", f"header{index}.xml"


def unique_relationship_id(rels_xml: str, base: str = "rIdManualHeader") -> str:
    if f'Id="{base}"' not in rels_xml:
        return base
    index = 2
    while f'Id="{base}{index}"' in rels_xml:
        index += 1
    return f"{base}{index}"


def add_header_to_existing_docx(docx_path: Path, header_text: str) -> None:
    """Add the same two-column header used by code materials to an existing DOCX."""
    tmp_path = docx_path.with_suffix(docx_path.suffix + ".tmp")
    with zipfile.ZipFile(docx_path, "r") as src:
        names = set(src.namelist())
        header_part, header_target = next_header_part(names)
        rels_xml = src.read("word/_rels/document.xml.rels").decode("utf-8")
        rel_id = unique_relationship_id(rels_xml)

        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    text = data.decode("utf-8")
                    override = (
                        f'<Override PartName="/{header_part}" '
                        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
                    )
                    if f'PartName="/{header_part}"' not in text:
                        text = text.replace("</Types>", f"{override}</Types>")
                    data = text.encode("utf-8")
                elif item.filename == "word/_rels/document.xml.rels":
                    text = data.decode("utf-8")
                    relationship = (
                        f'<Relationship Id="{rel_id}" '
                        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" '
                        f'Target="{header_target}"/>'
                    )
                    text = text.replace("</Relationships>", f"{relationship}</Relationships>")
                    data = text.encode("utf-8")
                elif item.filename == "word/document.xml":
                    text = data.decode("utf-8")
                    if "xmlns:r=" not in text:
                        text = text.replace(
                            "<w:document ",
                            '<w:document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ',
                            1,
                        )
                    header_ref = f'<w:headerReference w:type="default" r:id="{rel_id}"/>'
                    if "<w:headerReference" in text:
                        text = re.sub(r"<w:headerReference\b[^>]*/>", header_ref, text, count=1)
                    else:
                        text = re.sub(r"(<w:sectPr\b[^>]*>)", rf"\1{header_ref}", text, count=1)
                    data = text.encode("utf-8")
                dst.writestr(item, data)
            dst.writestr(header_part, header_xml(header_text))
    tmp_path.replace(docx_path)


def build_code_docx_ooxml(md_path: Path, out_path: Path, software_name: str, version: str) -> None:
    pages = parse_code_pages(md_path)
    if not pages:
        raise RuntimeError(f"No code pages parsed from {md_path}")
    start_page_no = pages[0][0] if pages else 1
    body: list[str] = []
    for index, (page_no, lines) in enumerate(pages):
        for line in lines:
            body.append(paragraph_xml(line if line else " ", font="Consolas", size_half_points=14, line_twips=280))
        if index != len(pages) - 1:
            # 嵌入式分页符：嵌入最后一段的 run 避免多余空段落
            last = body.pop()
            last = last.replace('</w:r></w:p>', '<w:br w:type="page"/></w:r></w:p>')
            body.append(last)
    minimal_docx(out_path, "\n".join(body), header_text=f"{software_name} {version}", start_page=start_page_no)


def add_markdown_table(document: Any, rows: list[list[str]]) -> None:
    if not rows:
        return
    table = document.add_table(rows=1, cols=len(rows[0]))
    table.style = "Table Grid"
    for idx, text in enumerate(rows[0]):
        table.rows[0].cells[idx].text = strip_markdown_links(text)
    for row in rows[1:]:
        cells = table.add_row().cells
        for idx, text in enumerate(row[: len(cells)]):
            cells[idx].text = strip_markdown_links(text)


def parse_table_line(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def add_image(document: Any, image_path: Path) -> None:
    if not image_path.exists():
        p = document.add_paragraph()
        run = p.add_run(f"[截图缺失：{image_path}]")
        set_run_font(run, "SimSun", 10.5)
        return
    try:
        document.add_picture(str(image_path), width=Inches(5.8))
    except Exception:
        p = document.add_paragraph()
        run = p.add_run(f"[截图无法插入：{image_path}]")
        set_run_font(run, "SimSun", 10.5)


def add_cover_page(document: Any, software_name: str, version: str, unit_name: str, completion_date: str) -> Any:
    """为操作手册加独立封面节（无页眉）：主标题（黑体二号加粗居中）+ 信息（宋体三号居中）。返回正文用分节。"""
    cover_section = document.sections[0]
    configure_a4(document, cover_section)

    # 主标题：软件全称 + 版本号，黑体加粗二号居中
    title_p = document.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(180)
    title_p.paragraph_format.space_after = Pt(0)
    title_run = title_p.add_run(f"{software_name} {version}")
    set_run_font_mixed(title_run, "黑体", "Times New Roman", 22)
    title_run.font.bold = True

    # 封面信息：编写单位、编写日期，宋体三号居中
    info_lines: list[str] = []
    if unit_name:
        info_lines.append(f"编写单位：{unit_name}")
    if completion_date:
        info_lines.append(f"编写日期：{completion_date}")
    for info in info_lines:
        info_p = document.add_paragraph()
        info_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_p.paragraph_format.space_before = Pt(60 if info is info_lines[0] else 6)
        info_p.paragraph_format.space_after = Pt(0)
        info_run = info_p.add_run(info)
        set_run_font_mixed(info_run, "宋体", "Times New Roman", 16)

    # 新建分节承载正文（封面节不加页眉）
    body_section = document.add_section(WD_SECTION.NEW_PAGE)
    body_section.header.is_linked_to_previous = False
    body_section.footer.is_linked_to_previous = False
    return body_section


def set_manual_header(document: Any, software_name: str, version: str, section: Any | None = None) -> None:
    """操作手册页眉：两栏——中间软件全称+版本号，右上角页码"第 X 页"，宋体小五号。"""
    sec = section if section is not None else document.sections[0]
    sec.header.is_linked_to_previous = False
    header = sec.header
    header.paragraphs[0].text = "" if header.paragraphs else None

    table = header.add_table(rows=1, cols=3, width=Cm(17.5))
    table.autofit = True
    # 三栏：左(留白均衡) / 中(软件名版本，居中) / 右(页码，右对齐)
    left_cell = table.rows[0].cells[0]
    center_cell = table.rows[0].cells[1]
    right_cell = table.rows[0].cells[2]

    def config_para(cell: Any, align: Any) -> Any:
        para = cell.paragraphs[0]
        para.alignment = align
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        para.paragraph_format.line_spacing = Pt(14)
        return para

    # 中间：软件名+版本
    center_para = config_para(center_cell, WD_ALIGN_PARAGRAPH.CENTER)
    center_run = center_para.add_run(f"{software_name} {version}")
    set_run_font_mixed(center_run, "宋体", "Times New Roman", 9)

    # 右上角：第 X 页
    right_para = config_para(right_cell, WD_ALIGN_PARAGRAPH.RIGHT)
    prefix = right_para.add_run("第 ")
    set_run_font_mixed(prefix, "宋体", "Times New Roman", 9)
    add_page_field(right_para, 9, "宋体", "Times New Roman")
    suffix = right_para.add_run(" 页")
    set_run_font_mixed(suffix, "宋体", "Times New Roman", 9)

    # 去掉页眉表格边框
    for cell in table.rows[0].cells:
        tc_pr = cell._tc.get_or_add_tcPr()
        tc_borders = OxmlElement("w:tcBorders")
        for border_name in ("top", "left", "bottom", "right"):
            border = OxmlElement(f"w:{border_name}")
            border.set(qn("w:val"), "nil")
            tc_borders.append(border)
        tc_pr.append(tc_borders)


def add_manual_caption(document: Any, text: str, align: Any = WD_ALIGN_PARAGRAPH.CENTER, size_pt: float = 10.5) -> None:
    """图注 / 表注：宋体五号居中，置于图片下方或表格上方。"""
    p = document.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    set_run_font_mixed(run, "宋体", "Times New Roman", size_pt)


def add_markdown_paragraph(document: Any, text: str, cjk_name: str = "宋体", latin_name: str = "Times New Roman", size_pt: float = 12.0,
                           align: Any = WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_indent: float = 24.0,
                           line_spacing: float = 1.5, space_before: float = 0.0, space_after: float = 0.0) -> Any:
    """新增一个段落，并解析 Markdown 的 `**加粗**` 语法：加粗片段设 bold=True，其余为普通文本。

    把 text 按 `**...**` 切分为若干 run，加粗部分运行用 bold=True，非加粗部分正常显示。
    支持单个段落内多个加粗片段。返回新增段落对象。
    """
    from docx.oxml.ns import qn as _qn  # noqa: F401  # 已由模块顶层导入 qn, 这里避免重复

    p = document.add_paragraph()
    p.alignment = align
    if first_line_indent:
        p.paragraph_format.first_line_indent = Pt(first_line_indent)
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)

    # 用 `**...**` 拆分文本；保留加粗标记，逐个判断是否加粗
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    for part in parts:
        if not part:
            continue
        is_bold = part.startswith("**") and part.endswith("**") and len(part) > 4
        content = part[2:-2] if is_bold else part
        run = p.add_run(content)
        set_run_font_mixed(run, cjk_name, latin_name, size_pt)
        if is_bold:
            run.font.bold = True
    return p


def build_manual_docx_python(md_path: Path, out_path: Path, base_dir: Path, software_name: str, version: str, unit_name: str = "", completion_date: str = "") -> None:
    document = Document()
    configure_a4(document)
    set_normal_font(document, "SimSun", 12.0)
    set_style_black(document)

    # 封面（独立节，无页眉）
    if unit_name or completion_date:
        body_section = add_cover_page(document, software_name, version, unit_name, completion_date)
        set_manual_header(document, software_name, version, body_section)
    else:
        set_manual_header(document, software_name, version)

    lines = md_path.read_text(encoding="utf-8", errors="replace").splitlines()
    table_buf: list[list[str]] = []
    in_fence = False
    # 用于给图片/表格自动编号
    figure_no = 0
    table_no = 0
    current_chapter = 0

    def flush_table() -> None:
        nonlocal table_buf, table_no
        if table_buf:
            data = [row for row in table_buf if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)]
            if data:
                # 表注：置于表格上方
                table_no += 1
                add_manual_caption(document, f"表{current_chapter}-{table_no}", WD_ALIGN_PARAGRAPH.CENTER, 10.5)
                add_markdown_table(document, data)
            table_buf = []

    for line in lines:
        stripped = line.strip()
        stripped = strip_markdown_links(stripped)
        if stripped.startswith("```"):
            flush_table()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("<!--") and "截图" in stripped:
            stripped = "【截图预留：请在此处插入当前功能页面或操作结果截图。】"
        if stripped.startswith("|") and stripped.endswith("|"):
            table_buf.append(parse_table_line(stripped))
            continue
        flush_table()
        if not stripped:
            continue
        image_match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
        if image_match:
            add_image(document, (base_dir / image_match.group(1)).resolve())
            figure_no += 1
            add_manual_caption(document, f"图{current_chapter}-{figure_no}", WD_ALIGN_PARAGRAPH.CENTER, 10.5)
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            hash_count = len(heading.group(1))
            text = heading.group(2)
            # 层级映射（Markdown # 个数 → 文档标题级）：
            #   # （1个）为文档主标题，封面上已含软件名+版本号，正文跳过
            #   ## （2个）→ 一级章标题，黑体加粗三号
            #   ### （3个）→ 二级节标题，黑体加粗小三号
            #   #### （4个）→ 三级标题，宋体加粗四号
            if hash_count == 1:
                continue
            if hash_count == 2:
                # 章标题：黑体加粗三号，段前17磅、段后16.5磅
                p = document.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(17)
                p.paragraph_format.space_after = Pt(16.5)
                p.paragraph_format.line_spacing = 1.5
                run = p.add_run(text)
                set_run_font_mixed(run, "黑体", "Times New Roman", 16)
                run.font.bold = True
                # 提取章节号供图注/表注使用
                m = re.match(r"^(\d+)\.\s", text)
                if m:
                    current_chapter = int(m.group(1))
            elif hash_count == 3:
                # 节标题：黑体加粗小三号，段前13磅、段后13磅
                p = document.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(13)
                p.paragraph_format.space_after = Pt(13)
                p.paragraph_format.line_spacing = 1.5
                run = p.add_run(text)
                set_run_font_mixed(run, "黑体", "Times New Roman", 15)
                run.font.bold = True
            elif hash_count == 4:
                # 三级标题：宋体加粗四号，段前0.5行、段后0.5行
                p = document.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.5
                run = p.add_run(text)
                set_run_font_mixed(run, "宋体", "Times New Roman", 14)
                run.font.bold = True
            else:
                # 四级及以上按正文处理
                p = document.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Pt(24)
                p.paragraph_format.line_spacing = 1.5
                run = p.add_run(text)
                set_run_font_mixed(run, "宋体", "Times New Roman", 12)
            continue
        # 正文（含列表转段落）：
        if re.match(r"^[-*+]\s+", stripped):
            stripped = re.sub(r"^[-*+]\s+", "", stripped)
        elif re.match(r"^\d+\.\s+", stripped):
            stripped = re.sub(r"^\d+\.\s+", "", stripped)
        # 用 markdown 解析函数生成正文段落，支持 **加粗** 语法
        add_markdown_paragraph(document, stripped, "宋体", "Times New Roman", 12.0,
                               WD_ALIGN_PARAGRAPH.JUSTIFY, 24.0, 1.5)
    flush_table()
    force_black_document(document)
    document.save(out_path)


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def build_with_pandoc(md_path: Path, out_path: Path, code_mode: bool = False) -> None:
    if not pandoc_available():
        raise RuntimeError("python-docx is unavailable and pandoc is not installed")
    source = md_path
    tmp_name: str | None = None
    original_text = md_path.read_text(encoding="utf-8", errors="replace")
    text = original_text
    text = re.sub(r"```text\s*\nSTOP_FOR_USER\n.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--[^>]*截图[^>]*-->", "【截图预留：请在此处插入当前功能页面或操作结果截图。】", text)
    text = strip_markdown_links(text)
    if code_mode:
        text = re.sub(r"(?=^##\s+第\s*\d+\s*页)", r"\n\\newpage\n", text, flags=re.M)
    if code_mode or "STOP_FOR_USER" in original_text:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_name = tmp.name
        source = Path(tmp_name)
    try:
        subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", str(source), "-o", str(out_path)], check=True, encoding="utf-8", errors="replace")
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)


def build_code_docx(
    md_path: Path,
    out_path: Path,
    software_name: str,
    version: str,
    unit_name: str = "",
    add_cover: bool = False,
) -> None:
    if DOCX_AVAILABLE:
        build_code_docx_python(md_path, out_path, software_name, version, unit_name, add_cover)
    else:
        build_code_docx_ooxml(md_path, out_path, software_name, version)
    normalize_docx_text_color(out_path)


def build_manual_docx(md_path: Path, out_path: Path, base_dir: Path, software_name: str, version: str, unit_name: str = "", completion_date: str = "") -> None:
    if DOCX_AVAILABLE:
        build_manual_docx_python(md_path, out_path, base_dir, software_name, version, unit_name, completion_date)
    else:
        build_with_pandoc(md_path, out_path, code_mode=False)
        add_header_to_existing_docx(out_path, f"{software_name} {version}")
    normalize_docx_text_color(out_path)


def run_command(command: list[str], cwd: Path | None = None, timeout: int = 60) -> tuple[int, str]:
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
        return completed.returncode, (completed.stdout + completed.stderr).strip()
    except Exception as exc:
        return 99, str(exc)


def docx_checks(skill_dir: Path, outputs: list[Path]) -> list[str]:
    notes: list[str] = []
    env_script = skill_dir / "vendor/docx-toolkit/scripts/env_check.sh"
    preview_script = skill_dir / "vendor/docx-toolkit/scripts/docx_preview.sh"
    if env_script.exists():
        code, output = run_command(["bash", str(env_script)], cwd=env_script.parent.parent, timeout=30)
        status = "READY" if code == 0 else "NOT READY"
        first_lines = "\n".join(output.splitlines()[:12])
        notes.append(f"DOCX env: {status}\n\n```text\n{first_lines}\n```")
    else:
        notes.append("DOCX env: vendor script missing")

    if preview_script.exists():
        for out in outputs:
            code, output = run_command(["bash", str(preview_script), str(out)], timeout=45)
            first_lines = "\n".join(output.splitlines()[:8])
            notes.append(f"Preview {out.name}: exit={code}\n\n```text\n{first_lines}\n```")
    return notes


def build_all(workdir: Path, software_name: str, version: str, skip_preview: bool) -> dict[str, Any]:
    workdir = ensure_dir(workdir)
    draft_dir = workdir / "草稿"
    final_dir = ensure_dir(workdir / "正式资料")
    app_name = application_software_name(draft_dir)
    app_version = application_version(draft_dir)
    final_software_name = app_name or software_name
    final_version = app_version or version
    safe_name = safe_filename(final_software_name)
    outputs: list[Path] = []
    warnings: list[str] = []
    if app_name and app_name != software_name:
        warnings.append(f"命令参数软件名称为 {software_name}，正式资料已按申请表信息软件名称 {app_name} 生成")
    if app_version and app_version != version:
        warnings.append(f"命令参数版本号为 {version}，正式资料已按申请表信息版本号 {app_version} 生成")
    screenshot_confirmation = read_json_if_exists(workdir / "截图方式确认.json")
    screenshot_method = screenshot_confirmation.get("screenshot_method")
    screenshot_manifest = workdir / "截图/截图清单.json"
    if screenshot_method == "skip":
        warnings.append("用户选择暂不截图；操作手册已保留截图预留位置")
    elif screenshot_method and not screenshot_manifest.exists():
        warnings.append("操作手册截图未生成或未插入；操作手册应保留截图预留位置")
    elif screenshot_manifest.exists():
        screenshots = read_json_if_exists(screenshot_manifest).get("screenshots") or []
        if not screenshots:
            warnings.append("操作手册截图清单为空；操作手册应保留截图预留位置")

    app_txt, app_warnings = write_application_txt(draft_dir, final_dir)
    if app_txt:
        outputs.append(app_txt)
    warnings.extend(app_warnings)

    # 合作开发（著作权人含两个及以上单位）时生成《合作开发协议书》
    agreement_path, agreement_warnings = build_cooperation_agreement(
        draft_dir, final_dir, final_software_name, final_version
    )
    if agreement_path:
        outputs.append(agreement_path)
    if agreement_warnings:
        warnings.extend(agreement_warnings)

    code_specs = [
        ("代码-前30页.md", f"{safe_name}-代码(前30页).docx"),
        ("代码-后30页.md", f"{safe_name}-代码(后30页).docx"),
        ("代码-全部.md", f"{safe_name}-代码(全部).docx"),
    ]
    raw_holder = parse_application_field(draft_dir / "申请表信息.md", "著作权人")
    # 封面单位落款只留单位名称主体，去掉统一社会信用代码（兼容“单位名，统一社会信用代码：xxx”和括号写法）
    _, unit_names = parse_copyright_holder(raw_holder)
    unit_name = "、".join(unit_names) if unit_names else re.sub(r"（[^（）]*统一社会信用代码[^（）]*）", "", raw_holder).strip("；; ）(").strip()
    # 操作手册封面编写日期取申请表"开发完成日期"
    manual_completion_date = parse_application_field(draft_dir / "申请表信息.md", "开发完成日期")
    manual_completion_date = manual_completion_date.replace("待用户确认", "").strip()
    if not manual_completion_date or not re.match(r"\d{4}", manual_completion_date):
        manual_completion_date = ""
    first_code_built = False
    for md_name, docx_name in code_specs:
        md_path = draft_dir / md_name
        if md_path.exists():
            out_path = final_dir / docx_name
            build_code_docx(md_path, out_path, final_software_name, final_version, unit_name, add_cover=not first_code_built)
            first_code_built = True
            outputs.append(out_path)

    manual_md = draft_dir / "操作手册.md"
    if manual_md.exists():
        manual_out = final_dir / f"{safe_name}_操作手册.docx"
        manual_source = manual_md
        tmp_manual: Path | None = None
        if app_name and app_name != software_name:
            text = manual_md.read_text(encoding="utf-8", errors="replace").replace(software_name, app_name)
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
                tmp.write(text)
                tmp_manual = Path(tmp.name)
            manual_source = tmp_manual
        try:
            build_manual_docx(manual_source, manual_out, draft_dir, final_software_name, final_version, unit_name, manual_completion_date)
        finally:
            if tmp_manual:
                tmp_manual.unlink(missing_ok=True)
        outputs.append(manual_out)
    else:
        warnings.append("缺少草稿/操作手册.md")

    skill_dir = Path(__file__).resolve().parents[1]
    notes = [] if skip_preview else docx_checks(skill_dir, [p for p in outputs if p.suffix.lower() == ".docx"])
    report = write_report(final_dir, outputs, warnings, notes)
    return {"outputs": [str(p) for p in outputs], "warnings": warnings, "report": str(report)}


def write_report(workdir: Path, outputs: list[Path], warnings: list[str], notes: list[str]) -> Path:
    report = workdir / "生成报告.md"
    lines = ["# 生成报告", "", "## 输出文件", ""]
    for path in outputs:
        size = path.stat().st_size if path.exists() else 0
        lines.append(f"- `{path.name}` ({size} bytes)")
    lines.extend(["", "## 警告", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- 无")
    lines.extend(["", "## DOCX 校验", ""])
    if notes:
        lines.extend(notes)
    else:
        lines.append("- 已跳过预览校验")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="软件著作权申请资料")
    parser.add_argument("--software-name", required=True)
    parser.add_argument("--version", default="V1.0")
    parser.add_argument("--skip-preview", action="store_true")
    args = parser.parse_args()

    workdir = Path(args.workdir)
    issues = confirmation_issues(workdir)
    if issues:
        print("STOP_FOR_USER")
        print("NEXT_ACTION: 正式 Word/TXT 生成前必须完成以下确认：")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(2)

    result = build_all(workdir, args.software_name, args.version, args.skip_preview)
    print(f"OK final materials: {Path(args.workdir) / '正式资料'}")
    for output in result["outputs"]:
        print(output)
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    print(f"Report: {result['report']}")


if __name__ == "__main__":
    main()
