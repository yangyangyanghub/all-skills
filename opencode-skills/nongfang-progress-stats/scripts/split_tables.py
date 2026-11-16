# -*- coding: utf-8 -*-
"""一张 NF 明细表拆成两张统计表：未完成（12 列）/ 已完成（16 列）。

用法:
    python split_tables.py --dir "E:\\...\\20261102"
    python split_tables.py --dir ... --adjust 永年区=4 --dry-run

口径:
    完成 = 该批次 实缴 >= 图斑数量
    未缴 = 该县 图斑合计 - 实缴合计（明细里手填的"未缴"列只用于对账，不直接采用）
    已缴（剩余口径）= 剩余图斑 - 未缴
    剩余批次 = 0 -> 进"已完成"表，否则进"未完成"表

列的来源:
    未完成表：全部来自明细
    已完成表的图斑/整改/拆除列来自当日省系统通报，卷宗图斑来自明细，
    「已缴费」「今日进展」不在明细里，默认沿用母版（或用 --fees 提供台账）
"""
import argparse
import copy
import datetime
import os
import re
import sys

import openpyxl
import xlrd

sys.stdout.reconfigure(encoding="utf-8")

NF_PATTERN = r"NF.*整改.*\.xlsx$"
UNFINISHED_PATTERN = r"统计表.*未完成.*\.xlsx$"
FINISHED_PATTERN = r"统计表.*已完成.*\.xlsx$"
SYS_PATTERN = r"通报.*\.xls$"

SYS_COL_TOTAL = 1
SYS_COL_DEMOLISH = 12
SYS_COL_DEMOLISH_DONE = 13
SYS_COL_PATROLS = 16
SYS_COL_DONE_ALL = 24
SYS_COL_RATE = 25

UNFINISHED_FIRST = 7
UNFINISHED_COLS = 12
FINISHED_FIRST = 6
FINISHED_COLS = 16

ALIAS = {"经济技术开发区": "经开区"}


def norm(text):
    return re.sub(r"\s+", "", str(text or ""))


def canon(text):
    name = norm(text)
    if name.startswith("邯郸"):
        name = name[2:]
    return ALIAS.get(name, name)


def num(value):
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(round(value))
    try:
        return int(round(float(str(value).replace(",", "").strip())))
    except ValueError:
        return 0


def find(directory, pattern, exclude=()):
    hits = [os.path.join(directory, n) for n in os.listdir(directory)
            if re.search(pattern, n) and not n.startswith("~$") and n not in exclude]
    return max(hits, key=os.path.getmtime) if hits else None


def file_date(path):
    match = re.search(r"(\d{1,2})\.(\d{1,2})", os.path.basename(path))
    return (int(match.group(1)), int(match.group(2))) if match else None


def find_prev_nf(directory, current_path, date):
    """同一目录里日期早于当前明细的、日期最大的一份 NF 明细。"""
    current = os.path.abspath(current_path)
    best = None
    best_key = None
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.abspath(path) == current or not re.search(NF_PATTERN, name):
            continue
        key = file_date(path)
        if not key:
            continue
        if key >= (date.month, date.day):
            continue
        if best_key is None or key > best_key:
            best, best_key = path, key
    return best


def pick_nf(directory):
    """按文件名里的日期取最新一期明细（mtime 不可靠，拷贝会变）。"""
    best = None
    best_key = None
    for name in os.listdir(directory):
        if not re.search(NF_PATTERN, name):
            continue
        path = os.path.join(directory, name)
        key = file_date(path)
        if not key:
            continue
        if best_key is None or key > best_key:
            best, best_key = path, key
    return best or find(directory, NF_PATTERN)


def read_nf(path, adjust):
    ws = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
    county = None
    agg = {}
    order = []
    for r in range(1, ws.max_row + 1):
        name = ws.cell(r, 2).value
        project = ws.cell(r, 3).value
        if name not in (None, ""):
            county = canon(name)
            display = norm(name)
        if project in (None, "") or county is None:
            continue
        patrol = num(ws.cell(r, 4).value)
        paid = num(ws.cell(r, 6).value)
        if patrol <= 0:
            continue
        if county not in agg:
            agg[county] = {"display": display, "b": 0, "p": 0, "paid": 0, "cum": 0, "cump": 0}
            order.append(county)
        item = agg[county]
        item["b"] += 1
        item["p"] += patrol
        item["paid"] += paid
        if paid >= patrol:
            item["cum"] += 1
            item["cump"] += patrol
    for name, extra in adjust.items():
        key = canon(name)
        if key not in agg:
            raise SystemExit("--adjust 指定的 %s 不在明细里" % name)
        agg[key]["paid"] += extra
        if agg[key]["paid"] > agg[key]["p"]:
            raise SystemExit("%s 实缴 %d 超过图斑 %d" % (name, agg[key]["paid"], agg[key]["p"]))
    return agg, order


def split_rows(agg, order):
    unfinished, finished = [], []
    for key in order:
        item = agg[key]
        rem_b = item["b"] - item["cum"]
        rem_p = item["p"] - item["cump"]
        unpaid = item["p"] - item["paid"]
        if unpaid < 0:
            raise SystemExit("%s 未缴为负" % item["display"])
        row = {"key": key, "name": item["display"], "b": item["b"], "p": item["p"],
               "cb": item["cum"], "cp": item["cump"], "rb": rem_b, "rp": rem_p,
               "paid": rem_p - unpaid, "unpaid": unpaid}
        (finished if rem_b == 0 else unfinished).append(row)
    return unfinished, finished


def read_sys(path):
    sheet = xlrd.open_workbook(path).sheet_by_index(0)
    rows = {}
    for r in range(sheet.nrows):
        name = norm(sheet.cell_value(r, 0))
        if not name or not name.endswith(("市", "区", "县")) or "统计表" in name:
            continue
        rows[canon(name)] = {
            "total": num(sheet.cell_value(r, SYS_COL_TOTAL)),
            "demolish": num(sheet.cell_value(r, SYS_COL_DEMOLISH)),
            "demolish_done": num(sheet.cell_value(r, SYS_COL_DEMOLISH_DONE)),
            "patrols": num(sheet.cell_value(r, SYS_COL_PATROLS)),
            "done_all": num(sheet.cell_value(r, SYS_COL_DONE_ALL)),
            "rate": float(sheet.cell_value(r, SYS_COL_RATE) or 0),
        }
    return rows


def read_fees(path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    fees = {}
    for r in range(1, ws.max_row + 1):
        name = ws.cell(r, 1).value
        if not isinstance(name, str):
            name = ws.cell(r, 2).value
        if not isinstance(name, str) or not norm(name).endswith(("市", "区", "县")):
            continue
        fees[canon(name)] = {"paid": num(ws.cell(r, 2).value), "today": num(ws.cell(r, 3).value)}
    return fees


def master_rows(ws, first, name_col):
    rows = []
    r = first
    while r <= ws.max_row:
        raw = ws.cell(r, name_col).value
        if raw in (None, ""):
            break
        rows.append((r, norm(raw), canon(raw)))
        r += 1
    return rows


def fit_rows(ws, first, need, max_col):
    rows = master_rows(ws, first, 2)
    have = len(rows)
    if need == have:
        return
    if need > have:
        src = rows[-1][0]
        for _ in range(need - have):
            dst = ws.max_row + 1
            ws.insert_rows(dst)
            if ws.row_dimensions[src].height:
                ws.row_dimensions[dst].height = ws.row_dimensions[src].height
            for c in range(1, max_col + 1):
                ws.cell(dst, c)._style = copy.copy(ws.cell(src, c)._style)
    else:
        ws.delete_rows(first + need, have - need)


def order_rows(target, master):
    by_key = {canon(name): (row, raw) for row, raw, name in master}
    ordered = []
    for row, raw, key in master:
        if any(item["key"] == key for item in target):
            ordered.append((row, raw, key))
    known = {key for _, _, key in ordered}
    for item in target:
        if item["key"] not in known:
            ordered.append((None, item["name"], item["key"]))
    return ordered, by_key


def write_unfinished(path, master_path, rows, total, date, prev_agg, master_values, dry_run):
    wb = openpyxl.load_workbook(master_path)
    ws = wb["Sheet1"]
    if ws.cell(3, 9).value not in (None, ""):
        ws.cell(3, 9).value = "时间：%d年%d月%d日" % (date.year, date.month, date.day)

    master = master_rows(ws, UNFINISHED_FIRST, 2)
    ordered, _ = order_rows(rows, master)
    fit_rows(ws, UNFINISHED_FIRST, len(ordered), UNFINISHED_COLS)

    by_key = {item["key"]: item for item in rows}
    for i, (_, raw_name, key) in enumerate(ordered, 1):
        r = UNFINISHED_FIRST + i - 1
        item = by_key[key]
        if key in prev_agg:
            old_cb = prev_agg[key]["cum"]
        else:
            old_cb = master_values.get(key, {}).get("cb", item["cb"])
        today = item["cb"] - old_cb
        ws.cell(r, 1).value = i
        ws.cell(r, 2).value = raw_name
        ws.cell(r, 3).value = item["b"]
        ws.cell(r, 4).value = item["p"]
        ws.cell(r, 5).value = today or None
        ws.cell(r, 6).value = item["cb"] or None
        ws.cell(r, 7).value = item["cp"] or None
        ws.cell(r, 8).value = item["rb"] or None
        ws.cell(r, 9).value = item["rp"] or None
        ws.cell(r, 10).value = item["paid"] or None
        ws.cell(r, 11).value = item["unpaid"] or None
        ws.cell(r, 12).value = None

    for c, key in ((3, "b"), (4, "p"), (5, "today"), (6, "cb"), (7, "cp"),
                   (8, "rb"), (9, "rp"), (10, "paid"), (11, "unpaid")):
        ws.cell(6, c).value = total[key] or None
    if not dry_run:
        wb.save(path)
    return ordered


def write_finished(path, master_path, rows, sys_today, sys_prev, fees, date, dry_run):
    wb = openpyxl.load_workbook(master_path)
    ws = wb["Sheet1"]
    if ws.cell(3, 11).value not in (None, ""):
        ws.cell(3, 11).value = "时间：%d年%d月%d日" % (date.year, date.month, date.day)

    master = master_rows(ws, FINISHED_FIRST, 2)
    ordered, master_by_key = order_rows(rows, master)
    fit_rows(ws, FINISHED_FIRST, len(ordered), FINISHED_COLS)

    by_key = {item["key"]: item for item in rows}
    missing = []
    carried = []
    blank = []
    for i, (_, raw_name, key) in enumerate(ordered, 1):
        r = FINISHED_FIRST + i - 1
        stat = sys_today.get(key)
        if not stat:
            missing.append(raw_name)
            continue
        prev = sys_prev.get(key)
        c = stat["total"]
        d = stat["done_all"]
        g = stat["demolish"]
        h = stat["demolish_done"]
        old = master_by_key.get(key)
        old_row = old[0] if old else None
        if key in fees:
            paid = fees[key]["paid"]
            today_fee = fees[key]["today"]
        elif old_row:
            paid = num(ws.cell(old_row, 12).value)
            today_fee = num(ws.cell(old_row, 14).value)
            carried.append(raw_name)
        else:
            paid = None
            today_fee = None
            blank.append(raw_name)

        ws.cell(r, 1).value = i
        ws.cell(r, 2).value = raw_name
        ws.cell(r, 3).value = c
        ws.cell(r, 4).value = d
        ws.cell(r, 5).value = c - d
        ws.cell(r, 6).value = d / c if c else None
        ws.cell(r, 7).value = g
        ws.cell(r, 8).value = h
        ws.cell(r, 9).value = g - h
        ws.cell(r, 10).value = h - prev["demolish_done"] if prev else 0
        ws.cell(r, 11).value = c - d - (g - h)
        ws.cell(r, 12).value = paid
        ws.cell(r, 13).value = (c - d - (g - h)) - paid if paid is not None else None
        ws.cell(r, 14).value = today_fee
        ws.cell(r, 16).value = by_key[key]["p"]
    if not dry_run:
        wb.save(path)
    return ordered, missing, carried, blank


def main():
    parser = argparse.ArgumentParser(description="NF 明细表拆成未完成/已完成两张统计表")
    parser.add_argument("--dir", required=True, help="业务目录")
    parser.add_argument("--nf", help="NF 明细表，默认取目录里文件名含 NF 和 整改 的最新 xlsx")
    parser.add_argument("--unfinished-master", help="未完成表母版，默认取目录里含 统计表 和 未完成 的 xlsx")
    parser.add_argument("--finished-master", help="已完成表母版，默认取目录里含 统计表 和 已完成 的 xlsx")
    parser.add_argument("--out-unfinished", help="未完成表输出路径，默认 目录\\…(未完成M.D).xlsx")
    parser.add_argument("--out-finished", help="已完成表输出路径，默认 目录\\…(已完成).xlsx")
    parser.add_argument("--sys", help="当日省系统通报，默认取目录里最新的 通报 xls")
    parser.add_argument("--sys-prev", help="前一日通报，默认取第二新的 通报 xls")
    parser.add_argument("--nf-prev", help="上一期 NF 明细，默认取目录里日期早于当天的最新一份")
    parser.add_argument("--fees", help="开垦费台账 xlsx：县区/已缴费/今日进展")
    parser.add_argument("--adjust", action="append", default=[],
                        help="明细之外补记的实缴，如 永年区=4，可重复")
    parser.add_argument("--date", help="数据日期 YYYY-MM-DD，默认取通报文件名")
    parser.add_argument("--dry-run", action="store_true", help="只算不写")
    args = parser.parse_args()

    directory = os.path.abspath(args.dir)
    nf_path = args.nf or pick_nf(directory)
    if not nf_path:
        raise SystemExit("没找到 NF 明细表")
    unf_master = args.unfinished_master or find(directory, UNFINISHED_PATTERN)
    fin_master = args.finished_master or find(directory, FINISHED_PATTERN)
    if not unf_master or not fin_master:
        raise SystemExit("没找到未完成/已完成表母版")

    sys_files = sorted([os.path.join(directory, n) for n in os.listdir(directory)
                        if re.search(SYS_PATTERN, n) and not n.startswith("~$")],
                       key=os.path.getmtime, reverse=True)
    sys_path = args.sys or (sys_files[0] if sys_files else None)
    sys_prev_path = args.sys_prev or (sys_files[1] if len(sys_files) > 1 else None)
    if not sys_path:
        raise SystemExit("没找到省系统通报，已完成表的图斑/拆除列没有来源")

    if args.date:
        date = datetime.date.fromisoformat(args.date)
    else:
        match = re.search(r"(\d{1,2})\.(\d{1,2})", os.path.basename(sys_path))
        date = (datetime.date(datetime.date.today().year, int(match.group(1)), int(match.group(2)))
                if match else datetime.date.today())

    adjust = {}
    for item in args.adjust:
        name, _, value = item.partition("=")
        adjust[norm(name)] = num(value)

    agg, order = read_nf(nf_path, adjust)
    unfinished, finished = split_rows(agg, order)
    fees = read_fees(args.fees) if args.fees else {}
    sys_today = read_sys(sys_path)
    sys_prev = read_sys(sys_prev_path) if sys_prev_path else {}

    prev_nf_path = args.nf_prev or find_prev_nf(directory, nf_path, date)
    prev_agg = read_nf(prev_nf_path, {})[0] if prev_nf_path else {}

    print("明细：%s" % os.path.basename(nf_path))
    if prev_nf_path:
        print("昨日明细：%s" % os.path.basename(prev_nf_path))
    else:
        print("  [提示] 没找到上一期明细，当日批次改用母版累计值做差")
    print("通报：%s" % os.path.basename(sys_path))
    print("合计 %d 批次 / %d 图斑；未完成 %d 县，已完成 %d 县"
          % (sum(v["b"] for v in agg.values()), sum(v["p"] for v in agg.values()),
             len(unfinished), len(finished)))
    if adjust:
        print("补记实缴：%s" % "、".join("%s+%d" % kv for kv in adjust.items()))

    total = {k: sum(v[k] for v in unfinished) for k in
             ("b", "p", "cb", "cp", "rb", "rp", "paid", "unpaid")}
    old_unf = openpyxl.load_workbook(unf_master, data_only=True)["Sheet1"]
    master_values = {}
    for _, raw, key in master_rows(old_unf, UNFINISHED_FIRST, 2):
        master_values[key] = {"cb": num(old_unf.cell(_, 6).value)}
    total["today"] = total["cb"] - sum(master_values.get(x["key"], {}).get("cb", x["cb"])
                                       for x in unfinished)
    print("未完成合计 %d/%d，累计 %d/%d，剩余 %d/%d，已缴 %d，未缴 %d"
          % (total["b"], total["p"], total["cb"], total["cp"],
             total["rb"], total["rp"], total["paid"], total["unpaid"]))

    if prev_agg:
        moves = []
        paid_delta = 0
        for key, item in agg.items():
            diff = item["paid"] - prev_agg.get(key, {}).get("paid", item["paid"])
            paid_delta += diff
            if diff:
                moves.append("%s%d" % (item["display"], diff))
        print("今日收缴 %d 个%s" % (paid_delta, "（%s）" % "、".join(moves) if moves else ""))

    for item in unfinished:
        if item["paid"] + item["unpaid"] != item["rp"]:
            raise SystemExit("%s 已缴+未缴≠剩余图斑" % item["name"])
    for item in unfinished + finished:
        stat = sys_today.get(item["key"])
        if stat and stat["patrols"] and stat["patrols"] != item["p"]:
            print("  [提示] %s 通报卷宗图斑 %d ≠ 明细图斑 %d"
                  % (item["name"], stat["patrols"], item["p"]))

    tag = "%d.%d" % (date.month, date.day)
    unf_path = args.out_unfinished or os.path.join(
        directory, "农房整治工作卷宗整改进展统计表(未完成%s).xlsx" % tag)
    fin_path = args.out_finished or os.path.join(
        directory, "农房整治工作卷宗整改进展统计表(已完成).xlsx")

    write_unfinished(unf_path, unf_master, unfinished, total, date, prev_agg,
                     master_values, args.dry_run)
    _, missing, carried, blank = write_finished(fin_path, fin_master, finished,
                                         sys_today, sys_prev, fees, date, args.dry_run)
    for name in missing:
        print("  [提示] %s 在通报里没有对应行，已完成表该行留空" % name)
    if carried:
        print("  [提示] 已完成表『已缴费/今日进展』沿用母版：%s" % "、".join(carried))
    if blank:
        print("  [提示] 已完成表『已缴费/今日进展』无来源、留空：%s（可用 --fees 提供）"
              % "、".join(blank))

    print("未完成表：%s" % unf_path)
    print("已完成表：%s" % fin_path)
    if args.dry_run:
        print("（dry-run，未写文件）")


if __name__ == "__main__":
    main()
