# -*- coding: utf-8 -*-
"""农房整治卷宗整改进展统计表 —— 自动更新

数据来源：邯郸市NF整改进展情况统计表*.xlsx（明细表，一行一个批次）
输出：农房整治工作卷宗整改进展统计表_YYYYMMDD.xlsx（复制模板后填值，不动模板）

口径（已用 2026-10-29 两份真实文件逐项复现人工表）：
    总批次 / 总图斑   = 明细行数 / Σ图斑数量
    累计批次 / 图斑   = "已全部完成"批次的个数及其图斑数
                        （判据：实缴 == 图斑数量，与备注"已全部完成"在本数据 109 行上完全等价）
    剩余              = 总 - 累计
    未缴费            = 总图斑 - Σ实缴        ← 以实缴为准，不读来源表的"未缴"列
    已缴费            = 剩余图斑 - 未缴费
    当日批次          = 本次累计批次 - 上次累计批次（基线）

为什么不用来源表的"未缴"列：该列是手填值，2026-10-29 永年区有 5 行与
"图斑数量-实缴"不符，合计虚高 6（1101 vs 1095），直接求和会算错。

用法：
    python update_stats.py --dir "E:\\...\\20261030"
    python update_stats.py --source a.xlsx --template b.xlsx --out-dir D:\\out
    python update_stats.py --dir "..." --dry-run          # 只算不写
    python update_stats.py --dir "..." --reset-baseline   # 用模板值重置当日基线
"""

import argparse
import json
import os
import re
import shutil
import sys

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.properties import PageSetupProperties

# ---------- 来源表（明细）列位置，0 基 ----------
SRC_SHEET = "Sheet1"
SRC_HEADER_ROW = 3          # 一级表头
SRC_SUBHEADER_ROW = 4       # 二级表头
SRC_DATA_START = 5
SRC_COL_COUNTY = 2          # B 县（市、区）
SRC_COL_PATROLS = 4         # D 图斑数量（个）
SRC_COL_PAID = 6            # F 实缴

# ---------- 目标表（统计表）列位置，0 基 ----------
DST_SHEET = "Sheet1"
DST_HEADER_ROW = 4          # 二级表头行
DST_DATA_START = 6          # 第一个县区的数据行
DST_COL_COUNTY = 2          # B 县（市、区）
DST_COL_TOT_BATCH = 3       # C 卷宗总任务-批次
DST_COL_TOT_PATROL = 4      # D 卷宗总任务-图斑
DST_COL_TODAY_BATCH = 5     # E 当日批次
DST_COL_CUM_BATCH = 6       # F 累计完成-批次
DST_COL_CUM_PATROL = 7      # G 累计完成-图斑
DST_COL_REM_BATCH = 8       # H 剩余任务-批次
DST_COL_REM_PATROL = 9      # I 剩余任务-图斑
DST_COL_PAID = 10           # J 已缴费
DST_COL_UNPAID = 11         # K 未缴费
DST_COL_NOTE = 12           # L 备注

CITY_LABEL = "邯郸市"



# ---------------------------------------------------------------- 工具
def norm_county(name):
    """规范化县区名：去掉所有空白和换行（来源表里有 '峰峰\\n矿区'）。
    """
    if name is None:
        return None
    return re.sub(r"\s+", "", str(name))


def as_int(value):
    """宽松转换：空值和非数字一律按 0。只用于已经校验过的数据。"""
    return parse_int(value)[1]


def parse_int(value):
    """严格转换，返回 (是否有效, 整数)。

    来源表的图斑数和实缴数是人填的，空着、写成"--"、写成"约30"都出现过。
    这些情况不能当 0——0 在业务上意味着"这个批次没有图斑/没缴钱"，会被
    当真数据算进总数，而且从报表上看不出来。所以要显式区分。
    """
    if value is None:
        return False, 0
    if isinstance(value, bool):
        return False, 0
    if isinstance(value, (int, float)):
        return True, int(round(value))
    text = str(value).strip().replace(",", "")
    if not text:
        return False, 0
    try:
        return True, int(round(float(text)))
    except ValueError:
        return False, 0


def warn(msg):
    print("  [警告] " + msg)


def fail(msg):
    print("  [错误] " + msg)


# ---------------------------------------------------------------- 定位文件
def _xlsx_files(directory):
    for name in os.listdir(directory):
        if name.startswith("~$") or not name.lower().endswith(".xlsx"):
            continue
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            yield name, path


DATE_IN_NAME = re.compile(r"(\d{1,2})[.\-_月](\d{1,2})")
OUTPUT_NAME = re.compile(r"_\d{8}(_\d{4})?\.xlsx$")


def find_source(directory, explicit=None):
    """定位来源明细表：文件名含 NF 与 整改，排除统计表与已生成的输出文件。

    排序优先用文件名里的日期（10.29 / 10.30），同日再比修改时间。
    只按修改时间排会让"从别处拷进来但保留旧时间戳"的文件被漏掉。
    """
    if explicit:
        return explicit
    candidates = []
    for name, path in _xlsx_files(directory):
        low = name.lower()
        if "nf" not in low or "整改" not in name:
            continue
        if "统计表" in name and "农房" in name:
            continue
        if OUTPUT_NAME.search(name):
            continue
        match = DATE_IN_NAME.search(name)
        file_date = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
        # 修改时间优先于文件名里的 M.D：文件名不带年份，跨年时 12.31 会被
        # 当成比 1.1 新，元旦当天就会选错表。mtime 是当天收件时间，更可靠。
        candidates.append((os.path.getmtime(path), file_date, path))
    if not candidates:
        raise SystemExit("未找到来源表：目录中没有文件名含 'NF' 且含 '整改' 的 .xlsx，请用 --source 指定。")
    candidates.sort(reverse=True)
    return candidates[0][2]


def find_template(directory, explicit=None):
    """定位统计表模板：文件名含 农房整治 与 统计表，且不带 8 位日期后缀。"""
    if explicit:
        return explicit
    candidates = []
    for name, path in _xlsx_files(directory):
        if "农房整治" not in name or "统计表" not in name:
            continue
        if OUTPUT_NAME.search(name):
            continue
        candidates.append((os.path.getmtime(path), path))
    if not candidates:
        raise SystemExit("未找到统计表模板：目录中没有文件名含 '农房整治' 与 '统计表' 的 .xlsx，请用 --template 指定。")
    candidates.sort(reverse=True)
    return candidates[0][1]


def date_from_filename(path, fallback_year):
    """从 '邯郸市NF整改进展情况统计表10.29(3).xlsx' 里取 10.29 → datetime.date。"""
    base = os.path.basename(path)
    match = DATE_IN_NAME.search(base)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            import datetime
            try:
                return datetime.date(fallback_year, month, day)
            except ValueError:
                pass
    import datetime
    return datetime.date.fromtimestamp(os.path.getmtime(path))


# ---------------------------------------------------------------- 读来源表
def read_source(path, warnings, bad_rows):
    """返回 (明细行列表, 合计行字典, 告警列表)。

    明细行：{'county': 规范县区名, 'patrols': int, 'paid': int, 'raw_county': 原始值}
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    if SRC_SHEET not in wb.sheetnames:
        raise SystemExit("来源表缺少工作表 %s，实际有：%s" % (SRC_SHEET, wb.sheetnames))
    ws = wb[SRC_SHEET]

    # --- 表头自检：列位置写死，但先验证，防止来源表结构变化后静默算错
    h3 = ws.cell(SRC_HEADER_ROW, SRC_COL_PATROLS).value
    h4_paid = ws.cell(SRC_SUBHEADER_ROW, SRC_COL_PAID).value
    h3_county = ws.cell(SRC_HEADER_ROW, SRC_COL_COUNTY).value
    if not h3 or "图斑" not in str(h3):
        raise SystemExit("来源表第%d行第D列不是'图斑数量'，实际=%r，表结构可能变了" % (SRC_HEADER_ROW, h3))
    if h4_paid != "实缴":
        raise SystemExit("来源表第%d行第F列不是'实缴'，实际=%r，表结构可能变了" % (SRC_SUBHEADER_ROW, h4_paid))
    if not h3_county or "县" not in str(h3_county):
        raise SystemExit("来源表第%d行第B列不是县区名，实际=%r" % (SRC_HEADER_ROW, h3_county))

    # --- 合并单元格填值：B 列每个县区只写首行
    fill = {}
    for rng in ws.merged_cells.ranges:
        if rng.min_col <= SRC_COL_COUNTY <= rng.max_col and rng.min_row >= SRC_DATA_START:
            value = ws.cell(rng.min_row, SRC_COL_COUNTY).value
            for r in range(rng.min_row, rng.max_row + 1):
                fill[r] = value

    rows = []
    total_row = None
    current_county = None
    for r in range(SRC_DATA_START, ws.max_row + 1):
        col_a = ws.cell(r, 1).value
        raw_county = fill.get(r, ws.cell(r, SRC_COL_COUNTY).value)
        if raw_county is not None and str(raw_county).strip():
            current_county = raw_county

        if col_a is not None and str(col_a).strip() == "合计":
            total_row = {
                "batches": None,
                "patrols": as_int(ws.cell(r, SRC_COL_PATROLS).value),
                "paid": as_int(ws.cell(r, SRC_COL_PAID).value),
                "row": r,
            }
            break

        patrols_raw = ws.cell(r, SRC_COL_PATROLS).value
        paid_raw = ws.cell(r, SRC_COL_PAID).value
        county = norm_county(current_county)

        # 跳过空行 / 备注行（A 列为空且无图斑无实缴）
        if (patrols_raw is None or str(patrols_raw).strip() == "") and \
           (paid_raw is None or str(paid_raw).strip() == ""):
            continue
        if not county:
            warnings.append("第%d行有数据但县区名为空，已跳过" % r)
            continue

        patrols_ok, patrols = parse_int(patrols_raw)
        paid_ok, paid = parse_int(paid_raw)
        if not patrols_ok:
            bad_rows.append({"row": r, "county": county, "field": "图斑数量", "value": patrols_raw})
        if not paid_ok:
            bad_rows.append({"row": r, "county": county, "field": "实缴", "value": paid_raw})

        rows.append({
            "row": r,
            "county": county,
            "raw_county": current_county,
            "patrols": patrols,
            "paid": paid,
            "valid": patrols_ok and paid_ok,
        })

    if not rows:
        raise SystemExit("来源表没有解析到任何明细行，请检查表格结构。")
    return rows, total_row, ws, bad_rows


# ---------------------------------------------------------------- 聚合
def aggregate(rows):
    """按县区聚合，返回 OrderedDict（按来源表出现顺序）。"""
    agg = {}
    order = []
    for row in rows:
        county = row["county"]
        if county not in agg:
            agg[county] = {
                "batches": 0,
                "patrols": 0,
                "paid": 0,
                "cum_batches": 0,
                "cum_patrols": 0,
            }
            order.append(county)
        bucket = agg[county]
        bucket["batches"] += 1
        bucket["patrols"] += row["patrols"]
        bucket["paid"] += row["paid"]

        # 完成判据：该批次图斑全部实缴。不看备注列——备注是人工写的，28 号表里
        # 就有"图斑15/实缴14/标已完成"和"图斑11/实缴11/没标"两处矛盾，只能以实缴为准。
        if row["patrols"] > 0 and row["paid"] == row["patrols"]:
            bucket["cum_batches"] += 1
            bucket["cum_patrols"] += row["patrols"]

    return agg, order


def finalize(agg, order):
    """补全派生列。"""
    result = []
    for county in order:
        b = agg[county]
        total_patrols = b["patrols"]
        total_batches = b["batches"]
        cum_batches = b["cum_batches"]
        cum_patrols = b["cum_patrols"]
        rem_batches = total_batches - cum_batches
        rem_patrols = total_patrols - cum_patrols
        # 未缴费以实缴为准：总数 - 实缴
        unpaid = total_patrols - b["paid"]
        paid_remaining = rem_patrols - unpaid
        result.append({
            "county": county,
            "total_batches": total_batches,
            "total_patrols": total_patrols,
            "cum_batches": cum_batches,
            "cum_patrols": cum_patrols,
            "rem_batches": rem_batches,
            "rem_patrols": rem_patrols,
            "paid": paid_remaining,
            "unpaid": unpaid,
            "pay_total": b["paid"],
            "today_batches": 0,     # 稍后用基线填
        })
    return result


# ---------------------------------------------------------------- 模板 / 基线
def read_template_counties(ws):
    """读模板里的县区顺序（第 6 行起，B 列非空）。返回 [(row, county), ...]。"""
    out = []
    for r in range(DST_DATA_START, ws.max_row + 1):
        name = ws.cell(r, DST_COL_COUNTY).value
        if name is None or not str(name).strip():
            continue
        out.append((r, norm_county(name)))
    return out


def read_template_snapshot(ws):
    """读模板现有各列值，作为首次运行的当日基线和任务数对比基准。"""
    snapshot = {}
    for r, county in read_template_counties(ws):
        snapshot[county] = {
            "total_batches": as_int(ws.cell(r, DST_COL_TOT_BATCH).value),
            "total_patrols": as_int(ws.cell(r, DST_COL_TOT_PATROL).value),
            "cum_batches": as_int(ws.cell(r, DST_COL_CUM_BATCH).value),
            "cum_patrols": as_int(ws.cell(r, DST_COL_CUM_PATROL).value),
            "paid": as_int(ws.cell(r, DST_COL_PAID).value),
            "unpaid": as_int(ws.cell(r, DST_COL_UNPAID).value),
        }
    return snapshot


BASELINE_KEEP_DAYS = 40


def load_baseline(path):
    """读基线。返回按日期索引的快照表 {"2026-10-28": {...}, ...}。

    旧版基线是"最后一次运行的结果"单条记录，直接用它做当日增量会出问题：
    同一天跑第二遍时基线已经被第一遍覆盖，当日批次就从 10 变成 0，拿去出
    日报会写成"今日无新增"。改成按日期存快照后，同一天跑多少次，取的都是
    同一个"上一个不同日期"的基准。
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError) as exc:
        warn("基线文件读取失败（%s），将退回用模板值作基线：%s" % (path, exc))
        return {}

    if "snapshots" in payload:
        return payload["snapshots"]

    legacy_date = payload.get("data_date")
    if legacy_date and "counties" in payload:
        return {legacy_date: {"counties": payload["counties"]}}
    return {}


def pick_snapshot(snapshots, date):
    """取严格早于 date 的最近一份快照。同日重跑时不会被自己污染。"""
    earlier = sorted(k for k in snapshots if k < date.isoformat())
    if not earlier:
        return None, None
    return earlier[-1], snapshots[earlier[-1]]


def save_baseline(path, snapshots, date, payload):
    snapshots[date.isoformat()] = payload
    keep = sorted(snapshots)[-BASELINE_KEEP_DAYS:]
    trimmed = {k: snapshots[k] for k in keep}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"snapshots": trimmed}, fh, ensure_ascii=False, indent=2)
    return trimmed


# ---------------------------------------------------------------- 写表
A4_PAPER_SIZE = 9
REPORT_FONT_SIZE = 14
REPORT_ROW_HEIGHT = 19.8
REPORT_MARGIN_INCH = 0.25


def apply_report_style(ws):
    """统一报表外观：数据区 14 号字、A4 横向一页、水平居中。

    字号必须落在 xlsx 里而不是只在导出时临时改，用户直接打开 xlsx 看到的
    也得是 14 号。行高沿用模板的 19.8——14 号字占 18.7，再大会把 21 行挤出
    A4 横向一页；配合 0.25 英寸页边距，整表刚好落在 552pt 可用高度内。
    """
    for row in ws.iter_rows(min_row=DST_DATA_START - 1, max_row=ws.max_row,
                            min_col=1, max_col=DST_COL_NOTE):
        for cell in row:
            font = cell.font
            cell.font = Font(name=font.name, sz=REPORT_FONT_SIZE,
                             b=font.b, i=font.i, color=font.color)
            if cell.column == DST_COL_NOTE:
                continue
            cell.alignment = Alignment(horizontal="center", vertical="center",
                                       wrap_text=False)
            # 模板的数值格式是 '0_ '，尾部下划线会留一个空格宽，居中后看着偏左。
            # 换成纯 '0' 才是真正的居中数字。
            if cell.column != DST_COL_COUNTY:
                cell.number_format = "0"

    for r in range(DST_DATA_START - 1, ws.max_row + 1):
        ws.row_dimensions[r].height = REPORT_ROW_HEIGHT

    # "累计完成情况"跨 F:G 两列，模板原宽度是给 10 号字配的，14 号下会折成
    # "累计完成情 / 况"。加宽到合计 16 个字符宽，六个字正好一行。
    ws.column_dimensions["F"].width = 9
    ws.column_dimensions["G"].width = 7

    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = A4_PAPER_SIZE
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    if ws.sheet_properties.pageSetUpPr is None:
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    else:
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.page_margins.left = REPORT_MARGIN_INCH
    ws.page_margins.right = REPORT_MARGIN_INCH
    ws.page_margins.top = REPORT_MARGIN_INCH
    ws.page_margins.bottom = REPORT_MARGIN_INCH
    ws.print_options.horizontalCentered = True


def write_output(template_path, out_path, date, city_row, county_rows, data, warnings):
    """复制模板到 out_path，写入数值与标题。"""
    shutil.copy2(template_path, out_path)
    wb = openpyxl.load_workbook(out_path)
    ws = wb[DST_SHEET]

    # 1) 标题日期
    title = "农房整治卷宗整改进展统计表\n（%d月%d日）" % (date.month, date.day)
    ws.cell(1, 1).value = title

    # 2) 合计行
    def put(row, col, value):
        ws.cell(row, col).value = None if value == 0 else value

    by_county = {item["county"]: item for item in data}
    totals = {
        "total_batches": sum(i["total_batches"] for i in data),
        "total_patrols": sum(i["total_patrols"] for i in data),
        "cum_batches": sum(i["cum_batches"] for i in data),
        "cum_patrols": sum(i["cum_patrols"] for i in data),
        "rem_batches": sum(i["rem_batches"] for i in data),
        "rem_patrols": sum(i["rem_patrols"] for i in data),
        "paid": sum(i["paid"] for i in data),
        "unpaid": sum(i["unpaid"] for i in data),
        "today_batches": sum(i["today_batches"] for i in data),
    }
    put(city_row, DST_COL_TOT_BATCH, totals["total_batches"])
    put(city_row, DST_COL_TOT_PATROL, totals["total_patrols"])
    put(city_row, DST_COL_TODAY_BATCH, totals["today_batches"])
    put(city_row, DST_COL_CUM_BATCH, totals["cum_batches"])
    put(city_row, DST_COL_CUM_PATROL, totals["cum_patrols"])
    put(city_row, DST_COL_REM_BATCH, totals["rem_batches"])
    put(city_row, DST_COL_REM_PATROL, totals["rem_patrols"])
    put(city_row, DST_COL_PAID, totals["paid"])
    put(city_row, DST_COL_UNPAID, totals["unpaid"])

    # 3) 各县区行
    for r, county in county_rows:
        item = by_county.get(county)
        if item is None:
            warnings.append("模板县区 %s 在来源表中没有对应数据，该行已置空" % county)
            for col in (DST_COL_TOT_BATCH, DST_COL_TOT_PATROL, DST_COL_TODAY_BATCH,
                        DST_COL_CUM_BATCH, DST_COL_CUM_PATROL, DST_COL_REM_BATCH,
                        DST_COL_REM_PATROL, DST_COL_PAID, DST_COL_UNPAID):
                ws.cell(r, col).value = None
            continue
        put(r, DST_COL_TOT_BATCH, item["total_batches"])
        put(r, DST_COL_TOT_PATROL, item["total_patrols"])
        put(r, DST_COL_TODAY_BATCH, item["today_batches"])
        put(r, DST_COL_CUM_BATCH, item["cum_batches"])
        put(r, DST_COL_CUM_PATROL, item["cum_patrols"])
        put(r, DST_COL_REM_BATCH, item["rem_batches"])
        put(r, DST_COL_REM_PATROL, item["rem_patrols"])
        put(r, DST_COL_PAID, item["paid"])
        put(r, DST_COL_UNPAID, item["unpaid"])

    apply_report_style(ws)
    wb.save(out_path)
    return totals


# ---------------------------------------------------------------- 校验
def export_pdf(xlsx_path, pdf_path):
    """把 xlsx 导成 PDF：优先用 Excel COM（还原度最好），失败退回 LibreOffice。

    返回 (是否成功, 说明)。失败不该让统计失败——xlsx 才是主交付。
    """
    xlsx_abs = os.path.abspath(xlsx_path)
    pdf_abs = os.path.abspath(pdf_path)

    try:
        import win32com.client
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        try:
            book = excel.Workbooks.Open(xlsx_abs)
            book.ExportAsFixedFormat(0, pdf_abs)   # 0 = xlTypePDF
            book.Close(False)
        finally:
            excel.Quit()
        return True, "Excel"
    except Exception as exc:
        first_error = str(exc)[:120]

    soffice = shutil.which("soffice")
    if not soffice:
        for candidate in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                          r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
            if os.path.exists(candidate):
                soffice = candidate
                break
    if soffice:
        try:
            import subprocess
            subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                            "--outdir", os.path.dirname(pdf_abs), xlsx_abs],
                           check=True, capture_output=True, timeout=180)
            if os.path.exists(pdf_abs):
                return True, "LibreOffice"
            return False, "LibreOffice 未生成 PDF"
        except Exception as exc:
            return False, "Excel 失败(%s)，LibreOffice 也失败(%s)" % (first_error, str(exc)[:120])
    return False, "Excel 导出失败(%s)，且未找到 LibreOffice" % first_error


def verify_output(path, data, totals, county_rows):
    """写完重新打开，逐格核对。不信任"保存成功"就等于"写对了"。

    openpyxl 保存可能因为文件被占用、磁盘满、样式对象异常等原因静默丢内容，
    而这批报表是要直接报上去的，写完不回头看等于赌。
    """
    ws = openpyxl.load_workbook(path, data_only=True)[DST_SHEET]
    by_county = {item["county"]: item for item in data}
    problems = []

    city_row = DST_DATA_START - 1
    checks = ((DST_COL_TOT_BATCH, "total_batches", "总批次"),
              (DST_COL_TOT_PATROL, "total_patrols", "总图斑"),
              (DST_COL_CUM_BATCH, "cum_batches", "累计批次"),
              (DST_COL_CUM_PATROL, "cum_patrols", "累计图斑"),
              (DST_COL_REM_PATROL, "rem_patrols", "剩余图斑"),
              (DST_COL_PAID, "paid", "已缴费"),
              (DST_COL_UNPAID, "unpaid", "未缴费"))
    for col, key, label in checks:
        got = as_int(ws.cell(city_row, col).value)
        if got != totals[key]:
            problems.append("合计行%s 写入 %d，应为 %d" % (label, got, totals[key]))

    for row, county in county_rows:
        item = by_county.get(county)
        expected_name = ws.cell(row, DST_COL_COUNTY).value
        if norm_county(expected_name) != county:
            problems.append("第%d行县区名变成 %r" % (row, expected_name))
            continue
        if item is None:
            continue
        got = as_int(ws.cell(row, DST_COL_TOT_BATCH).value)
        if got != item["total_batches"]:
            problems.append("%s 总批次写入 %d，应为 %d" % (county, got, item["total_batches"]))
        got = as_int(ws.cell(row, DST_COL_CUM_PATROL).value)
        if got != item["cum_patrols"]:
            problems.append("%s 累计图斑写入 %d，应为 %d" % (county, got, item["cum_patrols"]))

    sample = ws.cell(DST_DATA_START, DST_COL_TOT_BATCH)
    if sample.font.sz != REPORT_FONT_SIZE:
        problems.append("数据区字号是 %s，应为 %s" % (sample.font.sz, REPORT_FONT_SIZE))

    return problems


def append_history(directory, record):
    """每次运行追加一行，出了问题能倒查是哪天的哪份数据出的。"""
    path = os.path.join(directory, ".nongfang_history.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def validate(data, totals, src_total_row, warnings, table_counties):
    """逐项自检，返回是否整体通过。

    table_counties 是模板里真实存在的县区名集合。来源表出现模板没有的县区时，
    它的数据仍会计入全市合计，但落不到任何一行——这种"合计大于表内行之和"
    必须报错，否则会把漏报藏起来。
    """
    ok = True

    # 1) 表内能落地的县区之和 == 全市合计
    landed = [i for i in data if i["county"] in table_counties]
    orphans = [i["county"] for i in data if i["county"] not in table_counties]
    for key, label in (("total_batches", "总批次"), ("total_patrols", "总图斑"),
                       ("cum_batches", "累计批次"), ("cum_patrols", "累计图斑"),
                       ("paid", "已缴费"), ("unpaid", "未缴费")):
        s = sum(i[key] for i in landed)
        if s != totals[key]:
            fail("%s：表内 %d 个县区合计 %d != 全市合计 %d，差 %d"
                 % (label, len(landed), s, totals[key], totals[key] - s))
            ok = False
    if orphans:
        fail("来源表有 %d 个县区在模板里找不到对应行，其数据已计入合计但无法落表：%s"
             % (len(orphans), "、".join(orphans)))
        ok = False

    # 2) 已缴 + 未缴 == 剩余图斑
    for item in data:
        if item["paid"] + item["unpaid"] != item["rem_patrols"]:
            fail("%s 已缴%d + 未缴%d != 剩余图斑%d"
                 % (item["county"], item["paid"], item["unpaid"], item["rem_patrols"]))
            ok = False

    # 3) 累计 <= 总数，未缴不能为负
    for item in data:
        if item["cum_batches"] > item["total_batches"] or item["cum_patrols"] > item["total_patrols"]:
            fail("%s 累计完成超过总任务" % item["county"])
            ok = False
        if item["unpaid"] < 0:
            fail("%s 未缴费算出负数（%d），实缴超过图斑数" % (item["county"], item["unpaid"]))
            ok = False

    # 4) 与来源表合计行对比：未缴必然对不上（手填列有误），实缴和图斑应一致
    if src_total_row:
        if as_int(src_total_row.get("patrols")) not in (0, totals["total_patrols"]):
            fail("来源表合计行图斑 %s != 明细求和 %d，说明有明细行没读进来，或合计行是旧的"
                 % (src_total_row.get("patrols"), totals["total_patrols"]))
            ok = False
        src_unpaid = as_int(src_total_row.get("patrols")) - as_int(src_total_row.get("paid"))
        if src_unpaid and src_unpaid != totals["unpaid"]:
            warn("来源表'未缴'列口径为 %d，本表按'图斑-实缴'算出 %d（差 %d）。以实缴为准，属正常。"
                 % (src_unpaid, totals["unpaid"], totals["unpaid"] - src_unpaid))

    return ok


# ---------------------------------------------------------------- 主流程
def main():
    # 固定 UTF-8：本技能主要由 agent 调用并解析输出，agent 一律按 UTF-8 解码。
    # GBK 控制台下会显示乱码但数据不受影响，chcp 65001 即可。
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    parser = argparse.ArgumentParser(description="农房整治卷宗整改进展统计表自动更新")
    parser.add_argument("--dir", help="业务目录（同时用于自动发现来源表、模板、输出与基线）")
    parser.add_argument("--source", help="来源明细表路径，默认在 --dir 里自动找最新的 NF 整改表")
    parser.add_argument("--template", help="统计表模板路径，默认在 --dir 里自动找")
    parser.add_argument("--out-dir", help="输出目录，默认与模板同目录")
    parser.add_argument("--baseline", help="基线 JSON 路径，默认 <dir>/.nongfang_baseline.json")
    parser.add_argument("--date", help="数据日期 YYYY-MM-DD，默认从来源表文件名提取")
    parser.add_argument("--dry-run", action="store_true", help="只计算并打印，不写任何文件")
    parser.add_argument("--no-pdf", action="store_true", help="只出 xlsx，不导 PDF")
    parser.add_argument("--allow-dirty", action="store_true", help="图斑/实缴填空写错时仍继续（按 0 处理）")
    parser.add_argument("--reset-baseline", action="store_true", help="忽略现有基线，用模板值重置")
    args = parser.parse_args()

    if not args.dir and not (args.source and args.template):
        parser.error("请用 --dir 指定业务目录，或同时给 --source 与 --template")

    directory = os.path.abspath(args.dir) if args.dir else os.path.dirname(os.path.abspath(args.source))
    source_path = os.path.abspath(find_source(directory, args.source))
    template_path = os.path.abspath(find_template(directory, args.template))
    out_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.dirname(template_path)
    baseline_path = os.path.abspath(args.baseline) if args.baseline else os.path.join(directory, ".nongfang_baseline.json")

    print("来源表：%s" % source_path)
    print("模板表：%s" % template_path)

    # ---- 日期
    import datetime
    if args.date:
        try:
            data_date = datetime.date.fromisoformat(args.date)
        except ValueError:
            parser.error("--date 需要 YYYY-MM-DD 格式")
    else:
        data_date = date_from_filename(source_path, datetime.date.today().year)
    print("数据日期：%s" % data_date.isoformat())

    warnings = []
    bad_rows = []

    # ---- 读来源
    rows, src_total_row, _, bad_rows = read_source(source_path, warnings, bad_rows)

    if bad_rows:
        fail("来源表有 %d 处图斑数或实缴数填空/写错，不能当成 0 用：" % len(bad_rows))
        for item in bad_rows[:20]:
            fail("  第%d行 %s 的「%s」= %r" % (item["row"], item["county"],
                                              item["field"], item["value"]))
        if len(bad_rows) > 20:
            fail("  ……还有 %d 处" % (len(bad_rows) - 20))
        if not args.allow_dirty:
            fail("请先在上报表里改正再跑；确认这些值就是 0 时加 --allow-dirty 强制继续。")
            sys.exit(2)

    over_paid = [r for r in rows if r["paid"] > r["patrols"]]
    if over_paid:
        fail("来源表有 %d 个批次的实缴数超过图斑数，会导致未缴费算成负数：" % len(over_paid))
        for item in over_paid[:10]:
            fail("  第%d行 %s 图斑%d 实缴%d" % (item["row"], item["county"],
                                             item["patrols"], item["paid"]))
        if not args.allow_dirty:
            fail("请核对这几行的图斑数或实缴数后重跑。")
            sys.exit(2)
    if src_total_row:
        if as_int(src_total_row["patrols"]) and as_int(src_total_row["paid"]):
            print("来源表合计行：图斑 %s，实缴 %s" % (src_total_row["patrols"], src_total_row["paid"]))
        else:
            print("来源表合计行为公式且无缓存值，跳过该行校验（明细数据不受影响）")

    # ---- 聚合
    agg, order = aggregate(rows)
    data = finalize(agg, order)

    # ---- 模板与基线
    wb_tpl = openpyxl.load_workbook(template_path, data_only=True)
    if DST_SHEET not in wb_tpl.sheetnames:
        raise SystemExit("模板缺少工作表 %s，实际有：%s" % (DST_SHEET, wb_tpl.sheetnames))
    ws_tpl = wb_tpl[DST_SHEET]
    county_rows = read_template_counties(ws_tpl)
    tpl_snapshot = read_template_snapshot(ws_tpl)

    if not county_rows:
        raise SystemExit("模板里没有解析到县区行")
    table_counties = {county for _, county in county_rows}

    snapshots = {} if args.reset_baseline else load_baseline(baseline_path)
    base_date, baseline = pick_snapshot(snapshots, data_date)
    if baseline is None:
        baseline = {
            "counties": {k: {"cum_batches": v["cum_batches"], "cum_patrols": v["cum_patrols"]}
                         for k, v in tpl_snapshot.items()},
        }
        print("当日基线：模板现有累计值（没有更早的快照，按首次运行处理）")
    else:
        print("当日基线：%s 的快照" % base_date)

    # ---- 当日批次
    base_counties = baseline.get("counties", {})
    for item in data:
        if item["county"] not in table_counties:
            item["today_batches"] = 0
            continue
        base = base_counties.get(item["county"])
        base_cum = as_int(base.get("cum_batches")) if base else 0
        delta = item["cum_batches"] - base_cum
        if delta < 0:
            warnings.append("%s 本次累计批次 %d 少于基线 %d（数据回退？），当日按 0 计"
                            % (item["county"], item["cum_batches"], base_cum))
            delta = 0
        item["today_batches"] = delta

    # ---- 任务数变化提示
    for item in data:
        tpl = tpl_snapshot.get(item["county"])
        if not tpl:
            warnings.append("来源表新增县区 %s，模板中无对应行，请手工加行" % item["county"])
            continue
        if tpl["total_patrols"] and tpl["total_patrols"] != item["total_patrols"]:
            warnings.append("%s 图斑总数 %d → %d（任务口径变化）"
                            % (item["county"], tpl["total_patrols"], item["total_patrols"]))
        if tpl["total_batches"] and tpl["total_batches"] != item["total_batches"]:
            warnings.append("%s 批次总数 %d → %d（任务口径变化）"
                            % (item["county"], tpl["total_batches"], item["total_batches"]))

    # ---- 合计行位置
    city_row = DST_DATA_START - 1
    while city_row > 1:
        label = ws_tpl.cell(city_row, 1).value
        if label and CITY_LABEL in str(label):
            break
        city_row -= 1
    else:
        raise SystemExit("模板里找不到 '%s' 合计行" % CITY_LABEL)

    # ---- 汇总
    totals = {k: sum(i[k] for i in data) for k in
              ("total_batches", "total_patrols", "cum_batches", "cum_patrols",
               "rem_batches", "rem_patrols", "paid", "unpaid", "today_batches")}

    ok = validate(data, totals, src_total_row, warnings, table_counties)

    # ---- 输出
    out_path = None
    if not args.dry_run:
        stamp = data_date.strftime("%Y%m%d")
        out_name = "农房整治工作卷宗整改进展统计表_%s.xlsx" % stamp
        out_path = os.path.join(out_dir, out_name)
        if os.path.exists(out_path):
            # 同一天重跑是常态（改完来源表再算一遍），覆盖同名文件即可，
            # 加时间后缀只会让目录里堆一堆 _1743 的文件。
            print("同名文件已存在，覆盖：%s" % os.path.basename(out_path))
        write_output(template_path, out_path, data_date, city_row, county_rows, data, warnings)

        problems = verify_output(out_path, data, totals, county_rows)
        if problems:
            fail("写入后回读校验没通过，文件可能不完整：")
            for line in problems[:10]:
                fail("  " + line)
            fail("已生成的文件：%s" % out_path)
            sys.exit(3)

        pdf_path = None
        if not args.no_pdf:
            pdf_path = os.path.splitext(out_path)[0] + ".pdf"
            pdf_ok, pdf_note = export_pdf(out_path, pdf_path)
            if pdf_ok:
                print("PDF（%s）：%s" % (pdf_note, pdf_path))
            else:
                warnings.append("PDF 导出失败：%s。xlsx 已生成，不受影响。" % pdf_note)

        save_baseline(baseline_path, snapshots, data_date, {
            "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "source_file": source_path,
            "total": {"batches": totals["total_batches"], "patrols": totals["total_patrols"]},
            "counties": {
                i["county"]: {
                    "cum_batches": i["cum_batches"],
                    "cum_patrols": i["cum_patrols"],
                    "paid": i["paid"],
                    "unpaid": i["unpaid"],
                } for i in data
            },
        })

        append_history(directory, {
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "action": "stats",
            "data_date": data_date.isoformat(),
            "source": os.path.basename(source_path),
            "output": os.path.basename(out_path),
            "pdf": os.path.basename(pdf_path) if pdf_path else None,
            "totals": {"batches": totals["total_batches"], "patrols": totals["total_patrols"],
                       "cum_batches": totals["cum_batches"], "unpaid": totals["unpaid"]},
            "warnings": len(warnings),
            "ok": ok,
        })

    # ---- 打印
    print()
    header = "%-10s %6s %6s %6s %6s %6s %6s %6s %6s %6s" % (
        "县区", "总批次", "总图斑", "当日批", "累计批", "累计图", "剩余批", "剩余图", "已缴", "未缴")
    print(header)
    print("-" * len(header))
    ordered = sorted(data, key=lambda i: (-i["rem_patrols"], i["county"]))
    for item in ordered:
        print("%-10s %6d %6d %6d %6d %6d %6d %6d %6d %6d" % (
            item["county"], item["total_batches"], item["total_patrols"], item["today_batches"],
            item["cum_batches"], item["cum_patrols"], item["rem_batches"], item["rem_patrols"],
            item["paid"], item["unpaid"]))
    print("-" * len(header))
    print("%-10s %6d %6d %6d %6d %6d %6d %6d %6d %6d" % (
        CITY_LABEL, totals["total_batches"], totals["total_patrols"], totals["today_batches"],
        totals["cum_batches"], totals["cum_patrols"], totals["rem_batches"], totals["rem_patrols"],
        totals["paid"], totals["unpaid"]))

    print()
    if warnings:
        print("共 %d 条提示：" % len(warnings))
        for w in warnings:
            print("  - " + w)
    else:
        print("校验通过，无提示。")

    print()
    print("完成率：批次 %d/%d（%.1f%%），图斑 %d/%d（%.1f%%）" % (
        totals["cum_batches"], totals["total_batches"],
        100.0 * totals["cum_batches"] / totals["total_batches"] if totals["total_batches"] else 0,
        totals["cum_patrols"], totals["total_patrols"],
        100.0 * totals["cum_patrols"] / totals["total_patrols"] if totals["total_patrols"] else 0))

    if base_counties:
        changes = []
        for item in data:
            old = base_counties.get(item["county"], {})
            delta_batch = item["cum_batches"] - as_int(old.get("cum_batches"))
            delta_patrol = item["cum_patrols"] - as_int(old.get("cum_patrols"))
            if delta_batch or delta_patrol:
                changes.append((item["county"], delta_batch, delta_patrol))
        print()
        if changes:
            print("与上一份快照相比（%s）：" % (base_date or "模板值"))
            for name, delta_batch, delta_patrol in changes:
                print("  %-10s 批次 %+d，图斑 %+d" % (name, delta_batch, delta_patrol))
        else:
            print("与上一份快照相比：没有变化")

    if args.dry_run:
        print("--dry-run：未写出任何文件。")
    else:
        print("已生成：%s" % out_path)
        print("基线已更新：%s" % baseline_path)

    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
