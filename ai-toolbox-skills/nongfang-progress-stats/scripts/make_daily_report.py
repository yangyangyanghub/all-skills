# -*- coding: utf-8 -*-
"""生成"农房整治卷宗整改工作日报"，版式严格对齐 10.29 最终稿。

结构（与最终稿 PDF 一致）：
    第 1-2 页  A4 纵向   正文：标题、期号、发文机关、四段情况、附注、报发、印发
    第 3 页    A3 横向   附件1 邯郸市农房整治整改"省系统"进度统计表
    第 4 页    A4 横向   附件2 农房整治卷宗整改进展统计表

数据来源：
    正文批次口径  ← 统计表（update_stats.py 生成的 xlsx）
    整改率/省系统 ← 当日 + 前一日两份"通报"xls 做差
    版式          ← 最终稿 .doc（转成 docx 后作为母版）

用法：
    python make_daily_report.py --dir "E:\\...\\20261030"
    python make_daily_report.py --dir ... --restored 14,386
"""

import argparse
import copy
import datetime
import json
import os
import re
import shutil
import sys

import openpyxl
import xlrd
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

FANGSONG = "仿宋_GB2312"
KAI = "楷体_GB2312"
SONG = "宋体"

REPORT_TITLE = "农房整治卷宗整改工作日报"
AGENCY = "市自然资源和规划局"

SYS_TABLE_TITLE = "邯郸市农房整治整改“省系统”进度统计表"
STATS_TABLE_TITLE = "农房整治卷宗整改进展统计表"

# 省系统表：Word 19 列 → xls 列号（0 基）
SYS_COLUMN_MAP = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 17, 19, 21, 22]

# 省系统表里代表"已整改"的两列：拆除整改个数、补办整改个数（历史补办）
SYS_COL_DEMOLISH_DONE = 13
SYS_COL_REFILE_DONE = 19
SYS_COL_RATE = 25

# 省系统表的县区和报表叫法不一致，正文里统一用报表的叫法
CITY_NAME = "邯郸市"
NAME_ALIAS = {"邯郸经济技术开发区": "经开区", "邯郸冀南新区": "冀南新区"}


def display_name(sys_name, known):
    if sys_name in NAME_ALIAS:
        return NAME_ALIAS[sys_name]
    for name in known:
        if name in sys_name or sys_name in name:
            return name
    return sys_name[2:] if sys_name.startswith("邯郸") else sys_name


def fail(msg):
    print("  [错误] " + msg)


def append_history(directory, record):
    path = os.path.join(directory, ".nongfang_history.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def warn(msg):
    print("  [提示] " + msg)


def norm(name):
    return re.sub(r"\s+", "", str(name or ""))


def as_int(value):
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(round(value))
    text = str(value).replace(",", "").strip()
    if not text:
        return 0
    try:
        return int(round(float(text)))
    except ValueError:
        return 0


def as_rate(value):
    """比例可能是 0.406 或 40.6% 两种写法，统一成百分数字符串。"""
    if isinstance(value, str) and value.strip().endswith("%"):
        return float(value.strip().rstrip("%"))
    number = float(value or 0)
    return number * 100 if number <= 1.5 else number


# ---------------------------------------------------------------- 读统计表
STATS_SHEET = "Sheet1"
STATS_TOTAL_ROW = 5
STATS_FIRST_COUNTY_ROW = 6
STATS_LAST_COUNTY_ROW = 25
STATS_COL_COUNTY = 2
STATS_COL_TOT_BATCH = 3
STATS_COL_TOT_PATROL = 4
STATS_COL_TODAY = 5
STATS_COL_CUM_BATCH = 6
STATS_COL_CUM_PATROL = 7
STATS_COL_REM_BATCH = 8
STATS_COL_REM_PATROL = 9
STATS_COL_PAID = 10
STATS_COL_UNPAID = 11


def read_stats(path):
    ws = openpyxl.load_workbook(path, data_only=True)[STATS_SHEET]
    total = {
        "batches": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_TOT_BATCH).value),
        "patrols": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_TOT_PATROL).value),
        "today": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_TODAY).value),
        "cum_batches": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_CUM_BATCH).value),
        "cum_patrols": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_CUM_PATROL).value),
        "rem_batches": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_REM_BATCH).value),
        "rem_patrols": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_REM_PATROL).value),
        "paid": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_PAID).value),
        "unpaid": as_int(ws.cell(STATS_TOTAL_ROW, STATS_COL_UNPAID).value),
    }
    counties = []
    for r in range(STATS_FIRST_COUNTY_ROW, STATS_LAST_COUNTY_ROW + 1):
        name = ws.cell(r, STATS_COL_COUNTY).value
        if not name:
            continue
        counties.append({
            "name": norm(name),
            "total_batches": as_int(ws.cell(r, STATS_COL_TOT_BATCH).value),
            "total_patrols": as_int(ws.cell(r, STATS_COL_TOT_PATROL).value),
            "today": as_int(ws.cell(r, STATS_COL_TODAY).value),
            "cum_batches": as_int(ws.cell(r, STATS_COL_CUM_BATCH).value),
            "cum_patrols": as_int(ws.cell(r, STATS_COL_CUM_PATROL).value),
            "rem_batches": as_int(ws.cell(r, STATS_COL_REM_BATCH).value),
            "rem_patrols": as_int(ws.cell(r, STATS_COL_REM_PATROL).value),
            "paid": as_int(ws.cell(r, STATS_COL_PAID).value),
            "unpaid": as_int(ws.cell(r, STATS_COL_UNPAID).value),
        })
    return total, counties, ws


# ---------------------------------------------------------------- 读省系统 xls
def read_system(path):
    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)
    rows = []
    for r in range(sheet.nrows):
        name = norm(sheet.cell_value(r, 0))
        if not name or name in ("行政区名称", ""):
            continue
        if "统计表" in name or "数据统计时间" in name:
            continue
        if not name.endswith(("市", "区", "县")):
            continue
        rows.append({
            "name": name,
            "row": r,
            "cells": sheet.row_values(r),
            "rate": as_rate(sheet.cell_value(r, SYS_COL_RATE)),
            "demolish_done": as_int(sheet.cell_value(r, SYS_COL_DEMOLISH_DONE)),
            "refile_done": as_int(sheet.cell_value(r, SYS_COL_REFILE_DONE)),
        })
    if not rows:
        raise SystemExit("省系统表没有解析到县区行，请检查文件是否选错")
    return rows, sheet


SYS_COL_PATROLS = 16


def validate_cross(counties, sys_today):
    """省系统表和统计表的图斑总数必须一致。

    两份材料是分别上报的，一边改了另一边没改就会对不上，日报里同一段话会
    出现两个总图斑数，一看就露馅。省系统表里有一列（隐藏列）存的就是卷宗
    图斑数，正好可以拿来对账。
    """
    stats_by = {c["name"]: c["total_patrols"] for c in counties}
    mismatches = []
    for row in sys_today:
        cells = row["cells"]
        raw = cells[SYS_COL_PATROLS] if SYS_COL_PATROLS < len(cells) else ""
        value = as_int(raw)
        if not value:
            continue
        name = display_name(row["name"], stats_by.keys())
        expected = stats_by.get(name)
        if expected is None:
            continue
        if value != expected:
            mismatches.append("%s：省系统表 %d，统计表 %d" % (name, value, expected))
    return mismatches


def find_previous_restored(directory, current_date):
    """从更早一期日报的 PDF 里把"恢复被扣减卷宗 X 个批次涉及 Y 个图斑"读出来。

    这个数省系统表里没有对应列，是业务口径。但它在一段时间内是延续的，
    读上一期比每天手敲可靠。找不到就返回 None，由调用方决定留【待填】。

    每天的日报放在独立日期目录里（20261030、20261031…），上一期在兄弟目录，
    所以除了自己还要扫一遍父目录下的其它子目录。
    """
    search_dirs = [directory]
    parent = os.path.dirname(os.path.abspath(directory))
    if os.path.isdir(parent):
        for name in os.listdir(parent):
            sibling = os.path.join(parent, name)
            if os.path.isdir(sibling) and os.path.abspath(sibling) != os.path.abspath(directory):
                search_dirs.append(sibling)

    candidates = []
    for folder in search_dirs:
        for name in os.listdir(folder):
            if "日报" not in name or not name.lower().endswith(".pdf") or "备份" in name:
                continue
            match = re.search(r"(\d{1,2})\.(\d{1,2})", name)
            file_key = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
            if file_key >= (current_date.month, current_date.day):
                continue
            path = os.path.join(folder, name)
            candidates.append((os.path.getmtime(path), path, name))

    candidates.sort(reverse=True)
    for _, path, name in candidates:
        try:
            import fitz
            with fitz.open(path) as doc:
                text = "".join(page.get_text() for page in doc)
        except Exception:
            continue
        flat = re.sub(r"\s+", "", text)
        match = re.search(r"恢复被扣减卷宗(\d+)个批次涉及(\d+)个图斑", flat)
        if match:
            return int(match.group(1)), int(match.group(2)), name
    return None


def find_system_files(directory):
    """按文件名里的日期找当日的和前一日的通报 xls。"""
    items = []
    for name in os.listdir(directory):
        if name.startswith("~$") or not name.lower().endswith((".xls", ".xlsx")):
            continue
        if "通报" not in name:
            continue
        match = re.search(r"(\d{1,2})\.(\d{1,2})", name)
        if not match:
            continue
        file_date = (int(match.group(1)), int(match.group(2)))
        items.append((os.path.getmtime(os.path.join(directory, name)), file_date,
                      os.path.join(directory, name)))
    items.sort()
    if not items:
        return None, None
    today = items[-1][2]
    prev = items[-2][2] if len(items) > 1 else None
    return today, prev


# ---------------------------------------------------------------- 正文文字
def build_paragraphs(total, counties, sys_today, sys_prev, restored, date):
    """返回 [(段落索引, [(文本, 字体, 加粗), ...]), ...]。"""
    by_name = {c["name"]: c for c in counties}

    # 一、当日完成情况
    today_items = sorted([c for c in counties if c["today"] > 0],
                         key=lambda c: (-c["today"], c["total_batches"], -c["total_patrols"]))
    if today_items:
        today_text = "、".join("%s%d个" % (c["name"], c["today"]) for c in today_items)
        today_sentence = "今日完成%d个批次（%s）。" % (total["today"], today_text)
    else:
        today_sentence = "今日无新增完成整改批次。"
    p7 = [
        ("一、当日完成情况：", KAI, False),
        (today_sentence, FANGSONG, False),
    ]

    # 二、完成整改县、区（剩余批次为 0），按统计表倒序与最终稿一致
    done = [c["name"] for c in counties if c["rem_batches"] == 0 and c["total_batches"] > 0]
    p8 = [
        ("二、完成整改县、区：", KAI, False),
        ("%s已完成整改任务。" % "、".join(reversed(done)), FANGSONG, True),
    ]

    # 三、剩余任务情况：按批次整改率升序，零进展的合并成一句
    pending = [c for c in counties if c["rem_batches"] > 0]
    pending.sort(key=lambda c: (c["cum_batches"] / c["total_batches"] if c["total_batches"] else 0,
                                c["total_batches"]))
    zero = [c for c in pending if c["cum_batches"] == 0]
    rest = [c for c in pending if c["cum_batches"] > 0]

    segments = [("三、剩余任务情况：", KAI, False), ("按批次整改率由低到高依次为，", KAI, False)]
    if zero:
        for i, c in enumerate(zero):
            segments.append((c["name"], FANGSONG, True))
            segments.append(("%d个批次（%d个地块）" % (c["total_batches"], c["total_patrols"]),
                             FANGSONG, False))
            segments.append(("均无进展；" if i == len(zero) - 1 else "、", FANGSONG, False))
    for i, c in enumerate(rest):
        segments.append((c["name"], FANGSONG, True))
        segments.append(("完成%d个，剩余%d个批次（%d个地块）"
                         % (c["cum_batches"], c["rem_batches"], c["rem_patrols"]), FANGSONG, False))
        segments.append(("。" if i == len(rest) - 1 else "；", FANGSONG, False))
    p9 = segments

    # 截至目前
    p10 = build_prev_day_paragraph(total, sys_today, sys_prev, restored,known_names=[c["name"] for c in counties])

    return {6: build_overview(total), 7: p7, 8: p8, 9: p9, 10: p10}


def build_overview(total):
    """"已缴纳"要的是全部实缴（1646），不是统计表 J 列的"已缴费"（1075）。

    统计表 J 列只统计剩余任务里已缴的部分，已完成批次的图斑不在里面。
    实缴 = 总图斑 − 未缴，这个恒等式在口径里已经成立，直接用。
    """
    paid_total = total["patrols"] - total["unpaid"]
    return [("我市共涉及%d个批次%d个图斑，已整改%d个批次，%d个批次未整改。"
             "耕地开垦费已缴纳%d个，未缴纳%d个。"
             % (total["batches"], total["patrols"], total["cum_batches"],
                total["rem_batches"], paid_total, total["unpaid"]), FANGSONG, False)]


def build_prev_day_paragraph(total, sys_today, sys_prev, restored, known_names):
    """"截至目前"这一段：拆除/补办增量靠两份 xls 做差，整体整改率取当日 xls。"""
    city_today = next((r for r in sys_today if r["name"] == CITY_NAME), None)
    city_prev = next((r for r in sys_prev if r["name"] == CITY_NAME), None) if sys_prev else None

    segments = [("截至目前，", FANGSONG, False)]

    if city_today and city_prev:
        delta_demolish = city_today["demolish_done"] - city_prev["demolish_done"]
        ups = []
        downs = []
        for row in sys_today:
            if row["name"] == CITY_NAME:
                continue
            old = next((r for r in sys_prev if r["name"] == row["name"]), None)
            if not old:
                continue
            diff = row["demolish_done"] - old["demolish_done"]
            if diff > 0:
                ups.append((display_name(row["name"], known_names), diff))
            elif diff < 0:
                downs.append((display_name(row["name"], known_names), -diff))
        ups.sort(key=lambda item: -item[1])

        if delta_demolish > 0:
            text = "今日新增拆除完成%d个地块（%s）" % (
                delta_demolish, "、".join("%s%d个" % item for item in ups))
            # 有的县会往下掉（撤了或改了口径），不写出来明细加起来就跟净增对不上
            if downs:
                text += "，%s减少%s" % ("、".join(item[0] for item in downs),
                                      "、".join("%d个" % item[1] for item in downs))
            segments.append((text + "，", FANGSONG, False))
        else:
            segments.append(("今日无新增拆除完成地块，", FANGSONG, False))

        delta_refile = city_today["refile_done"] - city_prev["refile_done"]
        if delta_refile > 0:
            segments.append(("新增补办完成%d个图斑，" % delta_refile, FANGSONG, False))
        else:
            segments.append(("无新增补办完成图斑，", FANGSONG, False))
    else:
        segments.append(("今日新增拆除完成【待填】个地块（【待填】），"
                         "【待填】新增补办完成图斑，", FANGSONG, False))

    if restored and (restored[0] or restored[1]):
        segments.append(("恢复被扣减卷宗%d个批次涉及%d个图斑（含邯山区3倍扣减批次），"
                         % (restored[0], restored[1]), FANGSONG, False))
    else:
        segments.append(("恢复被扣减卷宗【待填】个批次涉及【待填】个图斑"
                         "（含邯山区3倍扣减批次），", FANGSONG, False))

    if city_today:
        rate = city_today["rate"]
        others = [r for r in sys_today if r["name"] != CITY_NAME]
        high = sorted(others, key=lambda r: -r["rate"])[:4]
        # 最终稿里"整改率较低"是从高到低念最低的三个（27.94 / 26.17 / 18.36）
        low = sorted(others, key=lambda r: r["rate"])[:3][::-1]
        segments.append(("总体整改率为%.2f%%。" % rate, FANGSONG, False))
        segments.append(("、".join("%s%.2f%%" % (r["name"], r["rate"]) for r in high)
                         + "整改率较高，", FANGSONG, False))
        segments.append(("、".join("%s%.2f%%" % (r["name"], r["rate"]) for r in low)
                         + "整改率较低。", FANGSONG, False))
    else:
        segments.append(("总体整改率为【待填】%。【待填】整改率较高，【待填】整改率较低。",
                         FANGSONG, False))
    return segments


# ---------------------------------------------------------------- 写 Word
def clear_runs(paragraph):
    """清空文字，但留住 VML 图形。

    公文的抬头红线、版记上下横线都是 <w:pict><v:line> 画在段落里的，它们和
    文字共用 run 列表。整段清空会把线一起删掉，所以带图形的 run 必须跳过。
    """
    for run in list(paragraph.runs):
        xml = run._element.xml
        if "<w:pict" in xml or "<w:drawing>" in xml:
            continue
        run._element.getparent().remove(run._element)


def fill_paragraph(paragraph, segments, size):
    clear_runs(paragraph)
    for text, font_name, bold in segments:
        run = paragraph.add_run(text)
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def set_date_paragraph(paragraph, date):
    """发文机关 + 日期那一行：机关名和日期之间用空格撑开。"""
    clear_runs(paragraph)
    left = paragraph.add_run(AGENCY)
    left.font.size = Pt(16)
    left.font.name = KAI
    left._element.rPr.rFonts.set(qn("w:eastAsia"), KAI)
    gap = paragraph.add_run(" " * 19)
    gap.font.size = Pt(16)
    gap.font.name = KAI
    gap._element.rPr.rFonts.set(qn("w:eastAsia"), KAI)
    right = paragraph.add_run("%d年%d月%d日" % (date.year, date.month, date.day))
    right.font.size = Pt(16)
    right.font.name = KAI
    right._element.rPr.rFonts.set(qn("w:eastAsia"), KAI)


def set_table_borders(table, size=4):
    """母版 doc 里没有 "Table Grid" 样式，只能自己往 tblPr 里写边框。"""
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement("w:" + edge)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    tbl_pr.append(borders)


def set_cell(cell, text, size, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, font=SONG):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text))
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)


def build_sys_table(doc, sheet, date):
    rows = sheet.nrows
    data_rows = []
    for r in range(rows):
        name = norm(sheet.cell_value(r, 0))
        if name and name.endswith(("市", "区", "县")) and "统计表" not in name:
            data_rows.append(r)
    table = doc.add_table(rows=3 + len(data_rows), cols=len(SYS_COLUMN_MAP))
    set_table_borders(table)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    head_font_size = 8
    body_font_size = 9

    table.cell(0, 0).merge(table.cell(2, 0))
    table.cell(0, 1).merge(table.cell(2, 1))
    for start, end in ((2, 4), (5, 7), (8, 10), (11, 13), (14, 18)):
        table.cell(0, start).merge(table.cell(0, end))
    table.cell(1, 16).merge(table.cell(1, 17))

    group_titles = {0: "行政区名称", 1: "图斑总个数\n（拆分后）",
                    2: "住宅类（占比6.75%）",
                    5: "特殊设施（宗教活动场所、宗祠\n、骨灰堂等）\n（占比3.46%）",
                    8: "按设施农用地认定\n（占比6.39%）",
                    11: "拆除（占比17.50%）",
                    14: "补办用地手续（占比65.90%）"}
    for col, text in group_titles.items():
        set_cell(table.cell(0, col), text, head_font_size, bold=True)

    sub = {2: "个数", 3: "整改个数", 4: "整改比例",
           5: "个数", 6: "整改个数", 7: "整改比例",
           8: "个数", 9: "整改个数", 10: "整改比例",
           11: "个数", 12: "整改个数", 13: "整改比例",
           14: "个数", 15: "新增补办\n个数", 16: "整改个数", 18: "补办整改比例"}
    for col, text in sub.items():
        set_cell(table.cell(1, col), text, head_font_size, bold=True)

    set_cell(table.cell(2, 16), "历史补办", head_font_size, bold=True)
    set_cell(table.cell(2, 17), "其中已取得用地\n批复", head_font_size, bold=True)

    for i, r in enumerate(data_rows):
        row_idx = 3 + i
        values = sheet.row_values(r)
        is_city = norm(values[0]) == CITY_NAME
        for col, src_col in enumerate(SYS_COLUMN_MAP):
            raw = values[src_col] if src_col < len(values) else ""
            if src_col in (4, 7, 10, 14, 22):
                text = "%.2f%%" % (as_rate(raw),)
            elif isinstance(raw, float) and raw == int(raw):
                text = str(int(raw))
            else:
                text = "" if raw == "" else str(raw)
            set_cell(table.cell(row_idx, col), text, body_font_size, bold=is_city)
    return table


def build_stats_table(doc, stats_ws):
    """附件2：直接把统计表（xlsx）的结构复刻成 Word 表格。"""
    table = doc.add_table(rows=25, cols=12)
    set_table_borders(table)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    size = 10.5

    table.cell(0, 0).merge(table.cell(1, 11))
    table.cell(0, 0).text = ""
    title_p = table.cell(0, 0).paragraphs[0]
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(STATS_TABLE_TITLE)
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.name = SONG
    title_run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    table.cell(2, 0).merge(table.cell(3, 0))
    table.cell(2, 1).merge(table.cell(3, 1))
    table.cell(2, 2).merge(table.cell(2, 3))
    table.cell(2, 4).merge(table.cell(2, 4))
    table.cell(2, 5).merge(table.cell(2, 6))
    table.cell(2, 7).merge(table.cell(2, 10))
    table.cell(2, 11).merge(table.cell(3, 11))

    headers_top = {0: "序号", 1: "县（市、区）", 2: "卷宗总任务",
                   4: "当日批次\n完成情况", 5: "累计完成情况",
                   7: "剩余任务", 11: "备注"}
    for col, text in headers_top.items():
        set_cell(table.cell(2, col), text, size, bold=True, font="黑体")

    headers_sub = {2: "批次", 3: "图斑", 5: "批次", 6: "图斑",
                   7: "批次", 8: "图斑", 9: "已缴费", 10: "未缴费"}
    for col, text in headers_sub.items():
        set_cell(table.cell(3, col), text, size, bold=True, font="黑体")

    for i in range(21):
        src_row = STATS_TOTAL_ROW + i
        dst_row = 4 + i
        for col in range(1, 13):
            value = stats_ws.cell(src_row, col).value
            text = "" if value is None else value
            set_cell(table.cell(dst_row, col - 1), text, size)
    return table


def ensure_docx(path):
    """母版是 .doc 时先转一份 docx。python-docx 读不了 97-2003 二进制格式。"""
    if path.lower().endswith(".docx"):
        return path
    target = path + ".template.docx"
    if os.path.exists(target):
        return target
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        opened = word.Documents.Open(os.path.abspath(path), ReadOnly=True)
        opened.SaveAs2(os.path.abspath(target), FileFormat=16)
        opened.Close(False)
    finally:
        word.Quit()
    return target


def word_convert(src, dst, file_format):
    """Word 转换：0=doc, 16=docx, 17=pdf。"""
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        opened = word.Documents.Open(os.path.abspath(src))
        opened.SaveAs2(os.path.abspath(dst), FileFormat=file_format)
        opened.Close(False)
    finally:
        word.Quit()


def xlsx_to_pdf(xlsx_path, pdf_path):
    """把统计表导成 A4 横向一页。

    人工做的统计表不一定设过页面设置，直接导出会得到 945×668 这种非标准纸张，
    跟日报正文的 A4 对不上。这里在内存里统一设一次，不改源文件。
    """
    import win32com.client
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        book = excel.Workbooks.Open(os.path.abspath(xlsx_path))
        sheet = book.Worksheets(1)
        sheet.PageSetup.PaperSize = 9
        sheet.PageSetup.Orientation = 2
        sheet.PageSetup.Zoom = False
        sheet.PageSetup.FitToPagesWide = 1
        sheet.PageSetup.FitToPagesTall = 1
        book.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
        book.Close(False)
    finally:
        excel.Quit()


def merge_pdfs(paths, out_path):
    import fitz
    merged = fitz.open()
    for path in paths:
        with fitz.open(path) as src:
            merged.insert_pdf(src)
    merged.save(out_path)
    merged.close()


def build_attachment1_docx(sys_sheet, date, out_docx):
    """附件1 单独成文（A3 横向），不塞进日报正文。"""
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Mm(420)
    section.page_height = Mm(297)
    section.left_margin = Mm(15)
    section.right_margin = Mm(15)
    section.top_margin = Mm(15)
    section.bottom_margin = Mm(15)

    title_paragraph = doc.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_paragraph.add_run(SYS_TABLE_TITLE)
    title_run.font.size = Pt(18)
    title_run.font.bold = True
    title_run.font.name = SONG
    title_run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    meta_paragraph = doc.add_paragraph()
    meta_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    meta_run = meta_paragraph.add_run(
        "数据统计时间：%d年%d月%d日18:00          单位：个"
        % (date.year, date.month, date.day))
    meta_run.font.size = Pt(10)
    meta_run.font.name = SONG
    meta_run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    build_sys_table(doc, sys_sheet, date)
    doc.save(out_docx)


def build_attachment2_docx(stats_ws, out_docx):
    """附件2 也走 Word：Excel 导出的纸张尺寸受默认打印机影响，控不住。"""
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Mm(297)
    section.page_height = Mm(210)
    section.left_margin = Mm(15)
    section.right_margin = Mm(15)
    section.top_margin = Mm(12)
    section.bottom_margin = Mm(12)
    build_stats_table(doc, stats_ws)
    doc.save(out_docx)


def add_section(doc, page_w_mm, page_h_mm):
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.orientation = WD_ORIENT.LANDSCAPE if page_w_mm > page_h_mm else WD_ORIENT.PORTRAIT
    section.page_width = Mm(page_w_mm)
    section.page_height = Mm(page_h_mm)
    section.left_margin = Mm(15)
    section.right_margin = Mm(15)
    section.top_margin = Mm(15)
    section.bottom_margin = Mm(15)
    return section


# ---------------------------------------------------------------- 主流程
def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    parser = argparse.ArgumentParser(description="生成农房整治卷宗整改工作日报")
    parser.add_argument("--dir", required=True, help="业务目录")
    parser.add_argument("--stats", help="统计表 xlsx，默认取目录里最新的 _YYYYMMDD.xlsx")
    parser.add_argument("--sys", help="当日省系统 xls，默认取文件名日期最新的通报文件")
    parser.add_argument("--sys-prev", help="前一日省系统 xls，用于算今日新增")
    parser.add_argument("--template", help="日报母版 doc/docx")
    parser.add_argument("--date", help="数据日期 YYYY-MM-DD")
    parser.add_argument("--issue", type=int, help="期号，默认按日累加")
    parser.add_argument("--restored", help="恢复被扣减卷宗：批次,图斑（如 14,386）")
    parser.add_argument("--out", help="输出 doc 路径")
    parser.add_argument("--no-pdf", action="store_true", help="只出正文 doc，不合并 PDF")
    parser.add_argument("--allow-mismatch", action="store_true", help="两源图斑数不一致时仍继续")
    args = parser.parse_args()

    directory = os.path.abspath(args.dir)

    # ---- 统计表
    stats_path = args.stats
    if not stats_path:
        candidates = [os.path.join(directory, n) for n in os.listdir(directory)
                      if re.search(r"农房整治.*_\d{8}(_\d{4})?\.xlsx$", n)]
        if not candidates:
            raise SystemExit("没找到统计表：先跑 update_stats.py 生成，或用 --stats 指定")
        stats_path = max(candidates, key=os.path.getmtime)
    total, counties, stats_ws = read_stats(stats_path)
    print("统计表：%s" % stats_path)

    # ---- 省系统 xls
    sys_today_path = args.sys
    sys_prev_path = args.sys_prev
    if not sys_today_path or not sys_prev_path:
        found_today, found_prev = find_system_files(directory)
        sys_today_path = sys_today_path or found_today
        sys_prev_path = sys_prev_path or found_prev
    if not sys_today_path:
        raise SystemExit("没找到省系统通报 xls（文件名需含'通报'和 M.D 日期）")
    sys_today, sys_sheet = read_system(sys_today_path)
    print("省系统表：%s" % sys_today_path)
    if sys_prev_path:
        sys_prev, _ = read_system(sys_prev_path)
        print("前一日省系统表：%s" % sys_prev_path)
    else:
        sys_prev = []
        warn("没有前一日的省系统表，'今日新增拆除/补办'只能留【待填】")

    mismatches = validate_cross(counties, sys_today)
    if mismatches:
        fail("省系统表和统计表的图斑数对不上，两份材料不是同一天的：")
        for line in mismatches[:10]:
            fail("  " + line)
        if not args.allow_mismatch:
            fail("请先确认哪一份是当天的，改好再出日报；确认要以统计表为准时加 --allow-mismatch。")
            sys.exit(2)

    # ---- 日期与期号
    if args.date:
        date = datetime.date.fromisoformat(args.date)
    else:
        match = re.search(r"(\d{1,2})\.(\d{1,2})", os.path.basename(sys_today_path))
        date = (datetime.date(datetime.date.today().year, int(match.group(1)), int(match.group(2)))
                if match else datetime.date.today())

    issue_path = os.path.join(directory, ".nongfang_report.json")
    issue_state = {}
    if os.path.exists(issue_path):
        try:
            issue_state = json.load(open(issue_path, encoding="utf-8"))
        except (OSError, ValueError):
            issue_state = {}
    last_issue = int(issue_state.get("issue", 0))
    if args.issue:
        issue = args.issue
    elif issue_state.get("date") == date.isoformat():
        issue = last_issue
    else:
        issue = last_issue + 1

    restored = (0, 0)
    if args.restored:
        parts = [as_int(x) for x in re.split(r"[,，]", args.restored) if x.strip()]
        restored = (parts[0], parts[1] if len(parts) > 1 else 0)
    else:
        inherited = find_previous_restored(directory, date)
        if inherited:
            restored = (inherited[0], inherited[1])
            print("恢复被扣减卷宗：沿用上期 %s 的 %d 个批次 %d 个图斑"
                  % (inherited[2], inherited[0], inherited[1]))
        else:
            warn("未指定 --restored，历史日报里也没找到这一项，留【待填】")

    # ---- 母版
    template_path = args.template or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "日报模板.doc")
    if not os.path.exists(template_path):
        raise SystemExit("没找到日报母版：%s（可用 --template 指定）" % template_path)
    doc = Document(ensure_docx(template_path))

    # ---- 正文
    paragraphs = build_paragraphs(total, counties, sys_today, sys_prev, restored, date)
    set_date_paragraph(doc.paragraphs[4], date)
    fill_paragraph(doc.paragraphs[2], [("第%d期" % issue, KAI, False)], 16)
    for idx, segments in paragraphs.items():
        fill_paragraph(doc.paragraphs[idx], segments, 16)
    fill_paragraph(doc.paragraphs[25],
                   [("\u3000邯郸市自然资源和规划局办公室          %d年%d月%d日印发"
                     % (date.year, date.month, date.day), "方正仿宋_GB2312", False)], 14)
    doc.paragraphs[2].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ---- 保存正文（日报只有正文，附表留到 PDF 合并时再加）
    out_path = args.out or os.path.join(
        directory, "农房整治工作卷宗整改工作日报%s最终稿.doc" % date.strftime("%m.%d"))
    tmp_docx = out_path + ".tmp.docx"
    doc.save(tmp_docx)
    word_convert(tmp_docx, out_path, 0)
    os.remove(tmp_docx)

    # ---- PDF：正文 + 附件1 + 附件2 逐段转好再合并
    if not args.no_pdf:
        pdf_path = os.path.splitext(out_path)[0] + ".pdf"
        work_dir = os.path.join(directory, ".report_tmp")
        os.makedirs(work_dir, exist_ok=True)
        body_pdf = os.path.join(work_dir, "body.pdf")
        att1_docx = os.path.join(work_dir, "att1.docx")
        att1_pdf = os.path.join(work_dir, "att1.pdf")
        att2_pdf = os.path.join(work_dir, "att2.pdf")

        word_convert(out_path, body_pdf, 17)
        build_attachment1_docx(sys_sheet, date, att1_docx)
        word_convert(att1_docx, att1_pdf, 17)
        att2_docx = os.path.join(work_dir, "att2.docx")
        build_attachment2_docx(stats_ws, att2_docx)
        word_convert(att2_docx, att2_pdf, 17)
        merge_pdfs([body_pdf, att1_pdf, att2_pdf], pdf_path)
        shutil.rmtree(work_dir, ignore_errors=True)
        print("PDF（正文+两页附表）：%s" % pdf_path)

    json.dump({"issue": issue, "date": date.isoformat()},
              open(issue_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print()
    print("已生成：%s" % out_path)
    append_history(directory, {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "action": "report",
        "data_date": date.isoformat(),
        "issue": issue,
        "output": os.path.basename(out_path),
        "restored": list(restored),
        "totals": {"batches": total["batches"], "patrols": total["patrols"],
                   "cum_batches": total["cum_batches"]},
    })
    print("期号：第%d期  数据日期：%s" % (issue, date.isoformat()))
    print("正文：%d批次/%d图斑，已整改%d，未整改%d，已缴%d，未缴%d"
          % (total["batches"], total["patrols"], total["cum_batches"],
             total["rem_batches"], total["patrols"] - total["unpaid"], total["unpaid"]))


if __name__ == "__main__":
    main()
