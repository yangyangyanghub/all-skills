#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quiz-unlock-patch.py — 存量课件「答题可改 + 导航条居中」批量升级器
（v2026-09-29 定案：提交前可随时修改，提交后锁定；页码/翻页键恒在底部居中）

背景：2026-09-29 价格理论试点确认，第四代课件的旧答题引擎是「选择一次即锁定」，
需要升级为「提交前可随时修改、提交后立即锁定（防刷分）」。锁定共 3+2 层，缺一不可：

  L1 单选 JS 闸门   if (container._chosen[qi] >= 0) return;   → if (container._submitted) return;
  L2 多选 JS 闸门   if (container._chosen[qi] !== null) return;（toggle + confirm 两处）
                                                              → if (container._submitted) return;
  L3 选项 CSS 锁    .quiz-q.answered .opt{pointer-events:none} → .quiz-q.submitted .opt{...}
  L4 确认按钮隐藏   .quiz-q.answered .opt-confirm{display:none} → .quiz-q.submitted .opt-confirm{...}
                    ⚠ 只改 L3 不改 L4 的坑：多选确认后 answered 即加、确认按钮被隐藏，
                      学生重选后点不到「确认本题」→ 无法重新确认（jsdom click() 不受
                      display 影响，行为测试测不出；真实浏览器必现）。
  L5 submitQuiz 承接  qq.classList.add('answered'); 后必须补 qq.classList.add('submitted');
                    ⚠ 不补的后果：提交后 CSS 锁（挂 submitted 前缀）永不生效 = 提交后仍可改。
  L6 导航条加固     #navBtns 各定位属性加 !important，防其它 fixed/absolute 样式挤占。

⚠ 核心教训（来自实战）：不同课件同一逻辑的写法空格不一致（如「if(container._chosen[qi]>=0)」
  vs「if (container._chosen[qi] >= 0)」），精确字符串替换会静默漏改 → 必须用容忍空格差异的
  正则，且替换后用计数断言核实。

用法：
  python quiz-unlock-patch.py <index.html> [more.html ...]            # 原地升级
  python quiz-unlock-patch.py --check <index.html> [...]              # 只读体检，不写盘
  python quiz-unlock-patch.py --selftest                              # 内置单测

退出码：0 = 全部完成/无问题；1 = 有修改失败或断言不符；2 = --check 发现待升级项。
备份：写盘前自动备份到系统临时目录（本脚本不在自身目录产生 .bak 残留）。
"""
import os
import re
import sys
import shutil
import tempfile

# ---------------- 每类修改： (名称, 编译好的正则, 替换模板, 期望最少命中数) ----------------
# ⚠ 全部用 re.sub + 计数，禁止 str.replace（空格差异会静默漏改）
PATTERNS = [
    ("L1 单选闸门",
     re.compile(r"if\s*\(\s*container\._chosen\[qi\]\s*>=\s*0\s*\)\s*return;[^\n\r]*"),
     "if (container._submitted) return; // 已提交，锁定（提交前可随时改选）",
     1),
    ("L2 多选闸门(toggle+confirm)",
     re.compile(r"if\s*\(\s*container\._chosen\[qi\]\s*!==\s*null\s*\)\s*return;[^\n\r]*"),
     "if (container._submitted) return;  // 已提交，锁定（提交前可随时修改）",
     1),
    ("L3 选项CSS锁",
     re.compile(r"\.quiz-q\.answered \.opt\{pointer-events:none;opacity:\.85\}"),
     ".quiz-q.submitted .opt{pointer-events:none;opacity:.85}",
     0),
    ("L4 确认按钮隐藏CSS",
     re.compile(r"\.quiz-q\.answered \.opt-confirm\{display:none\}"),
     ".quiz-q.submitted .opt-confirm{display:none}",
     0),
    # L5 只在「answered 后紧跟 opts 遍历」的 submitQuiz 上下文里补 submitted 类，
    # 避免误伤 initQuiz 里同样存在 qq.classList.add('answered') 的即时反馈分支。
    # ⚠ submitted 行必须插在 answered 行与 querySelectorAll 行之间（分组顺序勿动）。
    ("L5 submitQuiz补submitted类",
     re.compile(r"(qq\.classList\.add\('answered'\);\s*\n)(\s*)(qq\.querySelectorAll\('\.opt'\))"),
     lambda m: (m.group(1) + m.group(2)
                + "qq.classList.add('submitted'); // 承接 .submitted CSS 锁（提交后防刷分）\n"
                + m.group(2) + m.group(3)),
     0),
    # L6 容忍单行/多行两种写法，锚定定位四件套后整体替换为加固版
    ("L6 navBtns加固",
     re.compile(
         r"#navBtns\{[^}]*?position\s*:\s*fixed(?:\s*!important)?\s*;[^}]*?bottom\s*:\s*20px(?:\s*!important)?\s*;[^}]*?left\s*:\s*50%(?:\s*!important)?\s*;[^}]*?\}"),
     "#navBtns{position:fixed !important;bottom:20px !important;left:50% !important;"
     "right:auto !important;top:auto !important;transform:translateX(-50%) !important;"
     "display:flex !important;align-items:center;justify-content:center;gap:16px;z-index:150}",
     0),
]

# 幂等判据：含 submitted 闸门（JS 层已升级）即视为已处理过
DONE_MARK = re.compile(r"if\s*\(\s*container\._submitted\s*\)\s*return;")
# 需要存在答题引擎才谈得上升级
ENGINE_MARK = re.compile(r"function\s+initQuiz\s*\(")


def detect(text):
    """返回 (是否含答题引擎, 各层旧模式计数 dict)"""
    return {
        "L1": len(re.findall(r"if\s*\(\s*container\._chosen\[qi\]\s*>=\s*0\s*\)\s*return;", text)),
        "L2": len(re.findall(r"if\s*\(\s*container\._chosen\[qi\]\s*!==\s*null\s*\)\s*return;", text)),
        "L3": len(re.findall(r"\.quiz-q\.answered \.opt\{pointer-events:none", text)),
        "L4": len(re.findall(r"\.quiz-q\.answered \.opt-confirm\{display:none\}", text)),
        "L5_missing": len(re.findall(
            r"qq\.classList\.add\('answered'\);\s*\n\s*qq\.querySelectorAll\('\.opt'\)", text)),
        "L6_unhardened": len(re.findall(
            r"#navBtns\{[^}]*?position\s*:\s*fixed\s*;[^}]*?left\s*:\s*50%\s*;[^}]*?\}", text)),
    }


def process(path, check_only=False):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not ENGINE_MARK.search(text):
        print("  SKIP 无答题引擎(initQuiz):", path)
        return "skip"
    counts = detect(text)
    # ⚠ 幂等判据必须是「有 submitted 闸门 且 全部旧模式为 0」——
    #   只查部分层会把「半升级」文件（如手工还原过单选闸门）误判为已完成。
    if DONE_MARK.search(text) and not any(counts.values()):
        print("  OK 已是新版(幂等跳过):", path)
        return "done"
    pending = [k for k, v in counts.items() if v]
    if not pending:
        print("  OK 无旧锁定模式:", path)
        return "done"

    if check_only:
        print("  NEED-PATCH 待升级 %s -> %s" % (path, counts))
        return "need"

    new_text = text
    report = []
    for name, pat, repl, _min in PATTERNS:
        if isinstance(repl, str):
            new_text, n = pat.subn(repl, new_text)
        else:
            new_text, n = pat.subn(repl, new_text)
        if n:
            report.append("%s=%d" % (name, n))

    # 终态断言：旧模式必须清零
    after = detect(new_text)
    residual = {k: v for k, v in after.items() if v}
    if residual:
        print("  FAIL 替换后仍有旧模式残留 %s -> %s" % (path, residual))
        return "fail"
    if "L5 submitQuiz补submitted类" not in " ".join(report) and \
            len(re.findall(r"qq\.classList\.add\('submitted'\)", new_text)) == \
            len(re.findall(r"qq\.classList\.add\('submitted'\)", text)):
        # 原文件本来就没有可承接点也没有新增 → 记为无 L5（有的课件 submitQuiz 写法完全不同，交人工）
        report.append("L5=0(无可承接点,请人工核对submitQuiz)")

    bak = os.path.join(tempfile.gettempdir(),
                       "quiz_unlock_bak_%s" % os.path.basename(path))
    shutil.copy2(path, bak)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    with open(path, encoding="utf-8") as fh:
        back = fh.read()
    if back != new_text:
        print("  FAIL 回读不一致:", path)
        return "fail"
    print("  PATCHED %s (%s) 备份:%s" % (path, ", ".join(report), bak))
    return "ok"


def selftest():
    old_multi = ("qq.classList.add('answered');\n    qq.querySelectorAll('.opt').forEach")
    html_old = (
        "<script>\n"
        "function initQuiz(quizId){\n"
        "  if (container._chosen[qi] >= 0) return; // 已选\n"
        "  if (container._chosen[qi] !== null) return;  // 已确认\n"
        "  if(container._chosen[qi]>=0)return;\n"
        "}\n"
        "</script>\n"
        "<style>\n"
        ".quiz-q.answered .opt{pointer-events:none;opacity:.85}\n"
        ".quiz-q.answered .opt-confirm{display:none}\n"
        "#navBtns{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);display:flex;gap:16px;z-index:150}\n"
        "</style>\n"
        "<script>\n"
        "function submitQuiz(){\n"
        "  " + old_multi + "\n"
        "}\n"
        "</script>\n")
    import contextlib
    tmpd = tempfile.mkdtemp()
    fp = os.path.join(tmpd, "t.html")
    with open(fp, "w", encoding="utf-8") as fh:
        fh.write(html_old)
    r1 = process(fp)
    with open(fp, encoding="utf-8") as fh:
        out = fh.read()
    assert r1 == "ok", "selftest: 首次处理应 ok"
    assert "container._chosen[qi] >= 0" not in out and "container._chosen[qi]>=0" not in out, "L1 未清"
    assert "container._chosen[qi] !== null" not in out, "L2 未清"
    assert ".quiz-q.submitted .opt{pointer-events:none;opacity:.85}" in out, "L3 未替换"
    assert ".quiz-q.submitted .opt-confirm{display:none}" in out, "L4 未替换"
    assert "qq.classList.add('submitted');" in out, "L5 未补"
    assert "position:fixed !important" in out and "left:50% !important" in out, "L6 未加固"
    assert "transform:translateX(-50%) !important" in out, "L6 居中变换缺失"
    # 幂等：再跑一次应 done
    r2 = process(fp)
    assert r2 == "done", "selftest: 二次处理应幂等 done"
    # 反测：把 submitted 闸门手工还原为旧闸门，detect 必须重新报 L1/L2
    bad = out.replace("if (container._submitted) return; // 已提交，锁定（提交前可随时改选）",
                      "if (container._chosen[qi] >= 0) return;")
    badfp = os.path.join(tmpd, "bad.html")
    with open(badfp, "w", encoding="utf-8") as fh:
        fh.write(bad)
    chk = detect(bad)
    assert chk["L1"] >= 1, "selftest: 反测 detect 应报 L1"  # 测试样例含 2 种空格写法，还原后计 2
    # --check 语义：need / done
    r3 = process(badfp, check_only=True)
    assert r3 == "need", "selftest: check 模式对旧版应报 need"
    print("SELFTEST ALL PASS")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    check_only = "--check" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 1
    results = [process(f, check_only) for f in files]
    if any(r == "fail" for r in results):
        return 1
    if check_only and any(r == "need" for r in results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
