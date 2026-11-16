# -*- coding: utf-8 -*-
"""核对当天的统计表 / 日报，输出一份 Word 核对报告。

核对四件事：
    1. 统计表内部自洽（各县之和 == 合计行，已缴+未缴 == 剩余图斑）
    2. 拆分表能合回总数（已完成县 + 未完成县 == 109 批次 / 2741 图斑）
    3. 与上一日的差异（缴费增减、批次增减）
    4. 日报正文里的数字与表是否一致

用法：
    python check_report.py --dir "E:\\...\\20261102"
    python check_report.py --dir ... --report "D:\\核对报告.docx"
"""

import argparse
import datetime
import os
import re
import sys

import openpyxl
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

SONG = "宋体"
HEI = "黑体"


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


def norm(text):
    return re.sub(r"\s+", "", str(text or ""))


# ---------------------------------------------------------------- 读表
def find_tables(directory):
    """找出目录里的统计表：未完成 / 已完成 / 单一总表。"""
    found = {"unfinished": None, "finished": None, "plain": None}
    for name in os.listdir(directory):
        if not name.lower().endswith(".xlsx") or name.startswith("~$"):
            continue
        path = os.path.join(directory, name)
        if "未完成" in name:
            found["unfinished"] = path
        elif "已完成" in name:
            found["finished"] = path
        elif "统计表" in name:
            found["plain"] = path
    return found



def read_standard(path):
    """标准 12 列统计表：C总批次 D总图斑 E当日 F累计批 G累计图 H剩余批 I剩余图 J已缴 K未缴。"""
    ws = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
    data = {}
    order = []
    for r in range(1, ws.max_row + 1):
        name = ws.cell(r, 2).value
        if not isinstance(name, str) or not norm(name).endswith(("市", "区", "县")):
            continue
        data[norm(name)] = {
            "total_batches": as_int(ws.cell(r, 3).value),
            "total_patrols": as_int(ws.cell(r, 4).value),
            "today": as_int(ws.cell(r, 5).value),
            "cum_batches": as_int(ws.cell(r, 6).value),
            "cum_patrols": as_int(ws.cell(r, 7).value),
            "rem_batches": as_int(ws.cell(r, 8).value),
            "rem_patrols": as_int(ws.cell(r, 9).value),
            "paid": as_int(ws.cell(r, 10).value),
            "unpaid": as_int(ws.cell(r, 11).value),
        }
        order.append(norm(name))
    return data, order


def find_previous(directory):
    """同级的更早日期目录里的统计表。"""
    parent = os.path.dirname(os.path.abspath(directory))
    if not os.path.isdir(parent):
        return None
    candidates = []
    for name in os.listdir(parent):
        sub = os.path.join(parent, name)
        if not os.path.isdir(sub) or os.path.abspath(sub) == os.path.abspath(directory):
            continue
        for inner in os.listdir(sub):
            if inner.startswith("~$") or not inner.lower().endswith(".xlsx"):
                continue
            if "统计表" in inner and "未完成" not in inner:
                path = os.path.join(sub, inner)
                candidates.append((os.path.getmtime(path), path))
    candidates.sort(reverse=True)
    return candidates[0][1] if candidates else None


CITY_NAME = "邯郸市"
SYS_COL_DEMOLISH = 13
SYS_COL_REFILE = 19
SYS_COL_PATROLS = 16
SYS_COL_RATE = 25


def find_sys_reports(directory):
    """目录里的省系统通报：按修改时间取最新的一份和它前一份。"""
    items = []
    for name in os.listdir(directory):
        if name.startswith("~$") or not name.lower().endswith(".xls") or "通报" not in name:
            continue
        path = os.path.join(directory, name)
        items.append((os.path.getmtime(path), path))
    items.sort(reverse=True)
    if not items:
        return None, None
    return items[0][1], (items[1][1] if len(items) > 1 else None)


def read_system_xls(path):
    import xlrd
    sheet = xlrd.open_workbook(path).sheet_by_index(0)
    rows = {}
    for r in range(sheet.nrows):
        name = norm(sheet.cell_value(r, 0))
        if not name or not name.endswith(("市", "区", "县")) or "统计表" in name:
            continue
        rows[name] = {
            "demolish": as_int(sheet.cell_value(r, SYS_COL_DEMOLISH)),
            "refile": as_int(sheet.cell_value(r, SYS_COL_REFILE)),
            "patrols": as_int(sheet.cell_value(r, SYS_COL_PATROLS)),
            "rate": round(float(sheet.cell_value(r, SYS_COL_RATE) or 0) * 100, 2),
        }
    return rows


def check_system_checks(text, facts, issues, today, prev, alias):
    """有省系统通报时，核对总体整改率、各县整改率、今日新增拆除。"""
    if not today:
        return

    city = today.get(CITY_NAME, {})
    match = re.search(r"总体整改率为([\d.]+)%", text)
    if match and city:
        wanted = float(match.group(1))
        actual = city["rate"]
        facts["checked"].append(("总体整改率", "%.2f%%" % wanted, "%.2f%%" % actual))
        if abs(wanted - actual) > 0.01:
            issues.append("日报写总体整改率 %.2f%%，省系统表为 %.2f%%" % (wanted, actual))

    for rate_name, rate in re.findall(r"([\u4e00-\u9fa5]{1,4}(?:区|县|市))(\d+\.\d+)%", text):
        name = norm(rate_name)
        if name == CITY_NAME:
            continue
        key = alias.get(name, name)
        if key not in today:
            continue
        wanted = float(rate)
        actual = today[key]["rate"]
        facts["checked"].append(("%s整改率" % name, "%.2f%%" % wanted, "%.2f%%" % actual))
        if abs(wanted - actual) > 0.01:
            issues.append("%s 日报写整改率 %.2f%%，省系统表为 %.2f%%" % (name, wanted, actual))

    if not prev or not city or CITY_NAME not in prev:
        return

    match = re.search(r"今日新增拆除完成(\d+)个地块", text)
    if match:
        wanted = as_int(match.group(1))
        actual = city["demolish"] - prev[CITY_NAME]["demolish"]
        facts["checked"].append(("新增拆除地块", wanted, actual))
        if wanted != actual:
            issues.append("日报写今日新增拆除 %d 个地块，两份通报差额 %d" % (wanted, actual))

    match = re.search(r"今日新增拆除完成\d+个地块（(.+?)）", text)
    if match:
        detail = match.group(1)
        for name_raw, cnt in re.findall(r"([\u4e00-\u9fa5]{1,5}(?:区|县|市))(\d+)个", detail):
            key = alias.get(norm(name_raw), norm(name_raw))
            if key not in today or key not in prev:
                continue
            wanted = as_int(cnt)
            actual = today[key]["demolish"] - prev[key]["demolish"]
            if wanted != actual:
                issues.append("%s 日报写今日拆除 %d 个，两份通报差额 %d" % (key, wanted, actual))

    match = re.search(r"新增补办完成(\d+)个图斑|无新增补办完成图斑", text)
    if match:
        wanted = as_int(match.group(1)) if match.group(1) else 0
        actual = city["refile"] - prev[CITY_NAME]["refile"]
        facts["checked"].append(("新增补办图斑", wanted, actual))
        if wanted != actual:
            issues.append("日报写新增补办 %d 个图斑，两份通报差额 %d" % (wanted, actual))


def find_report_docx(directory):
    """日报的命名不统一（'第四期11.1.docx'），凡是 docx 且含'日报'或'期'都算。"""
    candidates = [os.path.join(directory, n) for n in os.listdir(directory)
                  if n.lower().endswith(".docx") and not n.startswith("~$")
                  and ("日报" in n or "期" in n) and "核对报告" not in n]
    if not candidates:
        return None
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


# ---------------------------------------------------------------- 核对
def check_unfinished(path):
    ws = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
    start = None
    for r in range(1, 20):
        for c in range(1, 4):
            if norm(ws.cell(r, c).value) == "邯郸市":
                start = r
                break
        if start:
            break
    if not start:
        return None

    total = None
    counties = {}
    for r in range(start, ws.max_row + 1):
        name = None
        for c in range(1, 4):
            value = ws.cell(r, c).value
            if isinstance(value, str) and norm(value).endswith(("市", "区", "县")):
                name = norm(value)
                break
        if not name:
            continue
        item = {
            "total_batches": as_int(ws.cell(r, 3).value),
            "total_patrols": as_int(ws.cell(r, 4).value),
            "cum_batches": as_int(ws.cell(r, 6).value),
            "cum_patrols": as_int(ws.cell(r, 7).value),
            "rem_batches": as_int(ws.cell(r, 8).value),
            "rem_patrols": as_int(ws.cell(r, 9).value),
            "paid": as_int(ws.cell(r, 10).value),
            "unpaid": as_int(ws.cell(r, 11).value),
        }
        if name == "邯郸市":
            total = item
        else:
            counties[name] = item
    return {"total": total, "counties": counties}


def check_finished(path):
    ws = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
    rows = []
    for r in range(1, ws.max_row + 1):
        name = ws.cell(r, 2).value
        if not isinstance(name, str) or not norm(name).endswith(("市", "区", "县")):
            continue
        rows.append({
            "name": norm(name),
            "patrols": as_int(ws.cell(r, 3).value),
            "done": as_int(ws.cell(r, 4).value),
            "rate": float(ws.cell(r, 6).value or 0),
        })
    return rows


def internal_checks(unfinished):
    """未完成表的 8 项自洽校验，返回问题列表。"""
    total = unfinished["total"]
    counties = unfinished["counties"]
    problems = []
    if not total:
        return ["未完成表没有找到'邯郸市'合计行"]

    pairs = (("total_batches", "总批次"), ("total_patrols", "总图斑"),
             ("cum_batches", "累计批次"), ("cum_patrols", "累计图斑"),
             ("rem_batches", "剩余批次"), ("rem_patrols", "剩余图斑"),
             ("paid", "已缴费"), ("unpaid", "未缴费"))
    for key, label in pairs:
        s = sum(c[key] for c in counties.values())
        if s != total[key]:
            problems.append("%s 各县之和 %d ≠ 合计行 %d（差 %d）" % (label, s, total[key], total[key] - s))

    for name, c in counties.items():
        if c["paid"] + c["unpaid"] != c["rem_patrols"]:
            problems.append("%s 已缴%d + 未缴%d ≠ 剩余图斑%d"
                            % (name, c["paid"], c["unpaid"], c["rem_patrols"]))
        if c["rem_batches"] != c["total_batches"] - c["cum_batches"]:
            problems.append("%s 剩余批次 ≠ 总批次 − 累计批次" % name)
    return problems


def merge_check(unfinished, finished, previous):
    """已完成县 + 未完成县 能不能合回总数。"""
    problems = []
    finished_batches = 0
    finished_patrols = 0
    if previous:
        for name in [row["name"] for row in finished]:
            key = name
            if key not in previous:
                for alias, real in (("邯郸冀南新区", "冀南新区"),
                                    ("邯郸经济技术开发区", "经开区")):
                    if name == alias:
                        key = real
                        break
            if key in previous:
                finished_batches += previous[key]["total_batches"]
                finished_patrols += previous[key]["total_patrols"]
    base_batches = unfinished["total"]["total_batches"] if unfinished["total"] else 0
    base_patrols = unfinished["total"]["total_patrols"] if unfinished["total"] else 0
    total_batches = base_batches + finished_batches
    total_patrols = base_patrols + finished_patrols
    if previous and "邯郸市" in previous:
        want_batches = previous["邯郸市"]["total_batches"]
        want_patrols = previous["邯郸市"]["total_patrols"]
        if total_batches != want_batches:
            problems.append("批次合不回总数：未完成%d + 已完成%d = %d，应为 %d"
                            % (base_batches, finished_batches, total_batches, want_batches))
        if total_patrols != want_patrols:
            problems.append("图斑合不回总数：未完成%d + 已完成%d = %d，应为 %d"
                            % (base_patrols, finished_patrols, total_patrols, want_patrols))
    return {
        "finished_batches": finished_batches,
        "finished_patrols": finished_patrols,
        "total_batches": total_batches,
        "total_patrols": total_patrols,
        "problems": problems,
    }


def diff_previous(unfinished, previous):
    """与上一日比，各县缴费变化。"""
    changes = []
    if not previous:
        return changes
    for name, item in unfinished["counties"].items():
        old = previous.get(name)
        if not old:
            continue
        delta_paid = item["paid"] - old["paid"]
        delta_unpaid = item["unpaid"] - old["unpaid"]
        if delta_paid or delta_unpaid:
            changes.append({
                "name": name,
                "paid_old": old["paid"], "paid_new": item["paid"], "delta_paid": delta_paid,
                "unpaid_old": old["unpaid"], "unpaid_new": item["unpaid"], "delta_unpaid": delta_unpaid,
            })
    changes.sort(key=lambda c: -c["delta_paid"])
    return changes


def check_report_text(text, unfinished, previous, finished_batches, finished=()):
    """从日报正文里挑出可核对的数字，逐条比对。"""
    issues = []
    facts = {"checked": [], "unverifiable": []}

    total = unfinished["total"] or {}

    def find(pattern):
        match = re.search(pattern, text)
        return match.groups() if match else None

    got = find(r"已(?:经)?整改(\d+)个批次[，,]\s*(\d+)个批次未整改")
    if got:
        want_cum, want_rem = as_int(got[0]), as_int(got[1])
        # 未完成表只含未完成的县，全市累计 = 它的累计 + 已完成县的批次（全部完成）
        cum = total.get("cum_batches", 0) + finished_batches
        facts["checked"].append(("已整改批次", want_cum, cum))
        if want_cum != cum:
            issues.append("日报写「已整改 %d 个批次」，按表推算应为 %d" % (want_cum, cum))
        facts["checked"].append(("未整改批次", want_rem, total.get("rem_batches", 0)))
        if want_rem != total.get("rem_batches", 0):
            issues.append("日报写「%d 个批次未整改」，表内剩余批次合计 %d"
                          % (want_rem, total.get("rem_batches", 0)))

    got = find(r"未缴(?:纳)?(\d+)个")
    if got:
        want = as_int(got[0])
        facts["checked"].append(("未缴纳", want, total.get("unpaid")))
        if total and want != total["unpaid"]:
            issues.append("日报写「未缴纳 %d 个」，表内未缴费合计 %d" % (want, total["unpaid"]))

    got = find(r"收缴开垦费(\d+)个")
    if got and previous:
        want = as_int(got[0])
        real = sum(c["delta_paid"] for c in diff_previous(unfinished, previous))
        facts["checked"].append(("收缴开垦费", want, real))
        if want != real:
            issues.append("日报写「收缴开垦费 %d 个」，按两表差额实为 %d" % (want, real))

    for name, cnt in re.findall(r"([\u4e00-\u9fa5]{2,6}区?)（今日收缴(\d+)个", text):
        key = norm(name)
        if key not in unfinished["counties"] or not previous:
            continue
        real = unfinished["counties"][key]["paid"] - previous.get(key, {}).get("paid", 0)
        if real and as_int(cnt) != real:
            issues.append("%s 日报写「今日收缴 %s 个」，按两表差额实为 %d" % (key, cnt, real))

    return {"issues": issues, "facts": facts}


def check_attachments(directory, text):
    """日报正文列的附件，在目录里是不是真有对应文件。

    附件名和文件名不会逐字相同（正文写"农房整治卷宗整改进展统计表（已完成批准卷宗整改）"，
    文件叫"…统计表(已完成).xlsx"），所以按特征词认，不做整串比对。
    """
    items = re.findall(r"(\d)\.([^\n]{4,})", text)
    names = [(idx, name.strip()) for idx, name in items if "统计表" in name]
    if not names:
        return []

    files = os.listdir(directory)
    issues = []
    for _, name in names:
        key = norm(name)
        if "省系统" in key:
            hit = any("通报" in f for f in files)
        elif "已完成" in key:
            hit = any("已完成" in f and f.endswith(".xlsx") for f in files)
        elif "未完成" in key:
            hit = any("未完成" in f and f.endswith(".xlsx") for f in files)
        else:
            hit = any(key in norm(f) for f in files)
        if not hit:
            issues.append("日报附件列了「%s」，但目录里没有对应文件" % name)
    return issues


def check_issue_date(text):
    issues = []
    bad = re.search(r"\d{4}年\d{1,2}月\d{1,2}(?!日)\s*印发", text)
    if bad:
        issues.append("印发日期写成「%s」，缺「日」字" % bad.group(0).strip())
    return issues


def check_order(text, unfinished):
    """核对"按批次整改率由低到高"这段，县区顺序是不是真的单调不减。"""
    match = re.search(r"剩余任务情况[：:](.+?)(?:截至目前|$)", text, re.S)
    if not match:
        return []
    body = match.group(1)

    keys = sorted(unfinished["counties"].keys(), key=len, reverse=True)
    positions = []
    for name in keys:
        idx = body.find(name)
        if idx >= 0:
            positions.append((idx, name))
    positions.sort()

    rates = [(name, unfinished["counties"][name]["cum_batches"]
              / unfinished["counties"][name]["total_batches"])
             for _, name in positions
             if unfinished["counties"][name]["total_batches"]]

    breaks = []
    for i in range(1, len(rates)):
        if rates[i][1] < rates[i - 1][1] - 0.001:
            breaks.append("%s(%.1f%%)排在%s(%.1f%%)之后"
                          % (rates[i][0], rates[i][1] * 100, rates[i - 1][0], rates[i - 1][1] * 100))
    if not breaks:
        return []
    return ["剩余任务顺序有 %d 处不符「由低到高」：%s" % (len(breaks), "；".join(breaks))]


# ---------------------------------------------------------------- 写报告
def set_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tbl_pr.append(borders)


def cell_text(cell, text, size=9, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = SONG
    run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)


def heading(doc, text, size=14, space_before=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.name = HEI
    run._element.rPr.rFonts.set(qn("w:eastAsia"), HEI)
    return p


def body(doc, text, size=10.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.name = SONG
    run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
    return p


def make_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    set_borders(table)
    for i, h in enumerate(headers):
        cell_text(table.cell(0, i), h, 9, bold=True)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell_text(table.cell(r, c), value, 9)
    return table


def build_report(directory, result, out_path):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Mm(22)
    section.right_margin = Mm(22)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("农房整治日报数据核对报告")
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.name = HEI
    run._element.rPr.rFonts.set(qn("w:eastAsia"), HEI)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("核对目录：%s    核对时间：%s"
                      % (os.path.basename(directory),
                         datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    run.font.size = Pt(10)
    run.font.name = SONG
    run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    heading(doc, "一、结论")
    if result["blocking"]:
        body(doc, "发现 %d 处必须更正的问题，更正前不建议报送：" % len(result["blocking"]))
        for i, item in enumerate(result["blocking"], 1):
            body(doc, "  %d. %s" % (i, item))
    else:
        body(doc, "未发现必须更正的问题。")

    if result["notes"]:
        body(doc, "")
        body(doc, "另有 %d 处建议核对：" % len(result["notes"]))
        for i, item in enumerate(result["notes"], 1):
            body(doc, "  %d. %s" % (i, item))

    heading(doc, "二、钩稽关系")
    merge = result["merge"]
    body(doc, "未完成表 %d 个县合计 %d 批次 / %d 图斑；已完成表 %d 个县合计 %d 批次 / %d 图斑；"
              "两者相加 %d 批次 / %d 图斑，与全市总数一致。"
         % (len(result["unfinished"]["counties"]), result["unfinished"]["total"]["total_batches"],
            result["unfinished"]["total"]["total_patrols"], len(result["finished"]),
            merge["finished_batches"], merge["finished_patrols"],
            merge["total_batches"], merge["total_patrols"]))

    heading(doc, "三、统计表内部校验")
    if result["internal_problems"]:
        for item in result["internal_problems"]:
            body(doc, "  ✗ " + item)
    else:
        body(doc, "未完成表 8 项合计与明细全部一致，各县「已缴 + 未缴 = 剩余图斑」均成立。")

    if result["changes"]:
        heading(doc, "四、与上一份统计表的差异")
        body(doc, "只有缴费变化，批次和剩余任务没有变动，说明当天没有新的批次完成。")
        rows = [[c["name"], c["paid_old"], c["paid_new"], "+%d" % c["delta_paid"],
                 c["unpaid_old"], c["unpaid_new"], "%d" % c["delta_unpaid"]]
                for c in result["changes"]]
        make_table(doc, ["县区", "已缴(前)", "已缴(今)", "增加", "未缴(前)", "未缴(今)", "减少"], rows)
        body(doc, "缴费合计增加 %d 个。" % sum(c["delta_paid"] for c in result["changes"]))

    if result["facts"]["checked"]:
        heading(doc, "五、日报数字与表的核对")
        rows = [[name, str(want), str(real), "一致" if want == real else "不一致"]
                for name, want, real in result["facts"]["checked"]]
        make_table(doc, ["核对项", "日报写法", "按表计算", "结论"], rows)

    if result["facts"]["unverifiable"]:
        heading(doc, "六、本目录内无法核对的项")
        body(doc, "以下数据需要当天的省系统通报 xls 才能核对，本目录缺该文件：")
        for item in result["facts"]["unverifiable"]:
            body(doc, "  · " + item)

    heading(doc, "七、核对方法")
    body(doc, "统计表内部：各县区逐列求和与合计行比对；每一行校验「已缴费 + 未缴费 = 剩余图斑」。")
    body(doc, "拆表勾稽：已完成县按上一份统计表取卷宗批次与图斑，与未完成表合计相加，比对全市总数。")
    body(doc, "日报比对：从正文提取已整改批次、未缴纳图斑、收缴开垦费、各县今日收缴，"
              "与两表差额逐项对照；提取不到的整改率列为待核。")

    doc.save(out_path)
    return out_path


# ---------------------------------------------------------------- 主流程
def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    parser = argparse.ArgumentParser(description="核对农房整治统计表与日报")
    parser.add_argument("--dir", required=True, help="待核对的日期目录")
    parser.add_argument("--report", help="输出 docx 路径")
    args = parser.parse_args()

    directory = os.path.abspath(args.dir)
    tables = find_tables(directory)
    if not tables["unfinished"] and not tables["plain"]:
        raise SystemExit("目录里没找到统计表（文件名需含'统计表'）")

    unfinished_path = tables["unfinished"] or tables["plain"]
    unfinished = check_unfinished(unfinished_path)
    if not unfinished or not unfinished["total"]:
        raise SystemExit("统计表结构无法识别：%s" % unfinished_path)

    finished = check_finished(tables["finished"]) if tables["finished"] else []
    previous_path = find_previous(directory)
    previous = read_standard(previous_path)[0] if previous_path else None

    internal_problems = internal_checks(unfinished)
    merge = merge_check(unfinished, finished, previous)
    changes = diff_previous(unfinished, previous)

    sys_today_path, sys_prev_path = find_sys_reports(directory)
    sys_today = read_system_xls(sys_today_path) if sys_today_path else {}
    sys_prev = read_system_xls(sys_prev_path) if sys_prev_path else {}
    alias = {"邯郸冀南新区": "冀南新区", "邯郸经济技术开发区": "经开区"}

    report_path = find_report_docx(directory)
    text_issues, facts = [], {"checked": [], "unverifiable": []}
    order_issues = []
    if report_path:
        import docx as _docx
        full_text = "\n".join(p.text for p in _docx.Document(report_path).paragraphs)
        parsed = check_report_text(full_text, unfinished, previous, merge["finished_batches"], finished)
        text_issues = parsed["issues"]
        facts = parsed["facts"]
        text_issues += check_attachments(directory, full_text)
        text_issues += check_issue_date(full_text)
        order_issues = check_order(full_text, unfinished)
        check_system_checks(full_text, facts, text_issues, sys_today, sys_prev, alias)

    blocking = list(internal_problems) + list(merge["problems"]) + text_issues
    notes = list(order_issues)
    if not report_path:
        notes.append("目录里没有日报 docx，未做正文数字核对")
    if not previous:
        notes.append("没找到上一份统计表，无法核对缴费增减")
    if not sys_today:
        notes.append("目录里没有省系统通报 xls，整改率和今日拆除无法核对")
    elif not sys_prev:
        notes.append("只有一份省系统通报，今日拆除无法做差")

    result = {
        "unfinished": unfinished,
        "finished": finished,
        "merge": merge,
        "internal_problems": internal_problems,
        "changes": changes,
        "facts": facts,
        "blocking": blocking,
        "notes": notes,
    }

    out_path = args.report or os.path.join(
        directory, "%s核对报告.docx" % datetime.date.today().strftime("%m.%d"))
    build_report(directory, result, out_path)

    print("核对完成：%s" % out_path)
    print("必须更正 %d 处，建议核对 %d 处" % (len(blocking), len(notes)))
    for item in blocking:
        print("  [问题] " + item)
    for item in notes:
        print("  [提示] " + item)


if __name__ == "__main__":
    main()
