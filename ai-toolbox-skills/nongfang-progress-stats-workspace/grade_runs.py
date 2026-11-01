# -*- coding: utf-8 -*-
"""按断言逐项核对每个 run 产出的 xlsx，写出 grading.json。

断言里能用数字判定的，全部程序化检查；语义类断言（有没有指出武安缺数据）
由文本关键字检查，结果在 evidence 里给出原文片段供人工复核。
"""
import hashlib
import json
import os
import re
import sys

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

WS = r"C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace"
IT = os.path.join(WS, "iteration-1")

TEMPLATE_NAME = "农房整治工作卷宗整改进展统计表(修改后).xlsx"
OUTPUT_PATTERN = re.compile(r"_\d{8}(_\d{4})?\.xlsx$")

# 邯郸市行各列下标（1 基）：C=3 总批次, D=4 总图斑, E=5 当日批次,
# F=6 累计批次, G=7 累计图斑, H=8 剩余批次, I=9 剩余图斑, J=10 已缴, K=11 未缴
CITY_EXPECT = {
    "eval-0-first-run": {
        "总批次": (3, 109), "总图斑": (4, 2741), "累计批次": (6, 43),
        "累计图斑": (7, 571), "剩余批次": (8, 66), "剩余图斑": (9, 2170),
        "已缴费": (10, 1075), "未缴费": (11, 1095),
    },
    "eval-1-rolling": {
        "总批次": (3, 109), "总图斑": (4, 2741), "当日批次": (5, 2),
        "累计批次": (6, 45), "累计图斑": (7, 606), "剩余批次": (8, 64),
        "剩余图斑": (9, 2135), "已缴费": (10, 1050), "未缴费": (11, 1085),
    },
    "eval-2-missing-county": {
        "总批次": (3, 109),
        "总图斑": (4, 2741),
    },
}

COUNTY_EXPECT = {
    "eval-2-missing-county": [
        ("武安市", "总批次（应为空）", 3, 0),
    ],
    "eval-0-first-run": [
        ("永年区", "总批次", 3, 17),
        ("永年区", "总图斑", 4, 509),
        ("永年区", "累计批次", 6, 1),
        ("永年区", "累计图斑", 7, 30),
        ("永年区", "剩余批次", 8, 16),
        ("永年区", "剩余图斑", 9, 479),
        ("永年区", "已缴费", 10, 316),
        ("永年区", "未缴费", 11, 163),
    ],
    "eval-1-rolling": [
        ("永年区", "当日批次", 5, 1),
        ("磁县", "当日批次", 5, 1),
    ],
}

TEXT_KEYWORDS = {
    "eval-1-rolling": [("明确指出永年区有新增", ["永年"]), ("明确指出磁县有新增", ["磁县"])],
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def as_num(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(round(value))
    try:
        return int(round(float(str(value).replace(",", "").strip())))
    except ValueError:
        return None


def find_output(workdir):
    """任何非模板、非来源明细表的 xlsx 都算产出（agent 各自命名方式不同）。"""
    hits = []
    for name in os.listdir(workdir):
        if not name.lower().endswith(".xlsx") or name.startswith("~$"):
            continue
        if name == TEMPLATE_NAME:
            continue
        if "nf" in name.lower() and "整改" in name:
            continue
        hits.append(os.path.join(workdir, name))
    return hits


NEGATIVE_NEAR_WUAN = re.compile(
    r"(武安[^\n]{0,120}(缺|未报|没有|没数据|无数据|缺失|漏|为空|无对应)"
    r"|(缺|未报|没有|没数据|无数据|缺失|漏|为空|无对应)[^\n]{0,120}武安)"
)


def read_city_and_counties(path):
    ws = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
    city_row = None
    counties = {}
    for r in range(1, ws.max_row + 1):
        label = ws.cell(r, 1).value
        county = ws.cell(r, 2).value
        if label and "邯郸市" in str(label):
            city_row = r
        if county and str(county).strip() and str(county).strip() != "县（市、区）":
            counties[re.sub(r"\s+", "", str(county))] = r
    if city_row is None:
        return None, counties, ws
    return city_row, counties, ws


def grade(eval_dir):
    eval_name = os.path.basename(eval_dir)
    fixture = os.path.join(IT, "fixtures", {
        "eval-0-first-run": "day1", "eval-1-rolling": "day2", "eval-2-missing-county": "partial",
    }[eval_name])
    tpl_ref = os.path.join(fixture, TEMPLATE_NAME)
    tpl_hash = sha256(tpl_ref) if os.path.exists(tpl_ref) else None

    for config in ("with_skill", "without_skill"):
        config_dir = os.path.join(eval_dir, config)
        workdir = os.path.join(config_dir, "workdir")
        expectations = []

        def add(text, passed, evidence):
            expectations.append({"text": text, "passed": bool(passed), "evidence": evidence})

        if not os.path.isdir(workdir):
            add("workdir 存在", False, workdir)
            write(config_dir, expectations)
            continue

        outputs = find_output(workdir)
        add("输出目录出现一个非模板的 .xlsx 文件", len(outputs) > 0,
            "; ".join(os.path.basename(p) for p in outputs) or "没有找到")

        tpl_now = os.path.join(workdir, TEMPLATE_NAME)
        if os.path.exists(tpl_now):
            ok = tpl_hash == sha256(tpl_now)
            add("模板文件未被修改（内容与运行前一致）", ok,
                "sha256 一致" if ok else "sha256 已变化，模板被改动")
        else:
            add("模板文件未被修改（内容与运行前一致）", False, "模板文件不见了")

        city = counties = ws = None
        if outputs:
            try:
                city, counties, ws = read_city_and_counties(outputs[0])
            except Exception as exc:  # noqa: BLE001
                add("输出文件可被 openpyxl 读取", False, repr(exc))

        if city:
            for label, (col, want) in CITY_EXPECT.get(eval_name, {}).items():
                got = as_num(ws.cell(city, col).value)
                add("%s = %s" % (label, want), got == want, "实际 %r" % (ws.cell(city, col).value,))

            for county, field, col, want in COUNTY_EXPECT.get(eval_name, []):
                row = counties.get(county)
                if row is None:
                    add("%s %s = %s" % (county, field, want), False, "表里找不到县区 %s" % county)
                    continue
                got = as_num(ws.cell(row, col).value)
                add("%s %s = %s" % (county, field, want), got == want, "实际 %r" % (ws.cell(row, col).value,))

            if eval_name == "eval-0-first-run":
                add("输出表仍含 20 个县区行", len(counties) == 20,
                    "实际 %d 个：%s" % (len(counties), "、".join(counties)))
                merged = len(ws.merged_cells.ranges)
                add("输出表保留了模板的合并单元格", merged >= 8, "合并区域 %d 个" % merged)

        answer = ""
        answer_path = os.path.join(workdir, "agent_answer.txt")
        if os.path.exists(answer_path):
            answer = open(answer_path, encoding="utf-8", errors="replace").read()
        for label, keywords in TEXT_KEYWORDS.get(eval_name, []):
            hit = any(k in answer for k in keywords)
            snippet = ""
            for line in answer.splitlines():
                if any(k in line for k in keywords):
                    snippet = line.strip()[:160]
                    break
            add(label, hit, snippet or "回答里没有出现 " + "/".join(keywords))

        if eval_name == "eval-2-missing-county":
            match = NEGATIVE_NEAR_WUAN.search(answer)
            add("明确指出武安市缺数据", bool(match),
                match.group(0)[:120] if match else "回答里没有把武安和'缺数据'联系起来")
            alias = "武安市区" in answer
            add("指出'武安市区'这个模板里没有的县区名", alias,
                "回答里出现了武安市区" if alias else "回答没有提到武安市区")
            add("没有静默产出一份看似完整的结果", bool(match) and alias,
                "已提示武安缺失并指出错写的县区名" if (match and alias) else "异常未被完整暴露")

        write(config_dir, expectations)


def write(config_dir, expectations):
    """写到 <config>/run-1/grading.json，字段兼容 skill-creator 的聚合与 viewer。"""
    run_dir = os.path.join(config_dir, "run-1")
    os.makedirs(run_dir, exist_ok=True)
    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    payload = {
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total else 0,
        },
        "expectations": expectations,
    }
    with open(os.path.join(run_dir, "grading.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print("%-58s %d/%d" % (os.path.basename(os.path.dirname(config_dir)) + "/" + os.path.basename(config_dir), passed, total))


if __name__ == "__main__":
    for name in ("eval-0-first-run", "eval-1-rolling", "eval-2-missing-county"):
        grade(os.path.join(IT, name))
