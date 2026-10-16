# -*- coding: utf-8 -*-
"""orphan-css-fix.py — 孤儿 CSS 声明块检测与修复（母技能·通用工具）

背景（2026-09-29 大模型课件实测）：删除元素（如 #fullscreenBtn）时若只删选择器行、
留下裸声明块，CSS 解析器会把「裸声明 + } + 后续注释 + 下一条规则的选择器」并成
一条无效规则整体丢弃 → 紧随其后的 #navBtns{position:fixed...} 等规则静默失效。
表现为：源码 grep 规则明明存在，浏览器 computed style 却是 static。

功能：
  --check            只读检测，报告每个文件的孤儿块位置（退出码 1=发现孤儿）
  （默认）           修复：删除孤儿声明块（注释行保留），四步纪律
                     （备份→系统临时目录 / 写盘 / 回读比对 / 复检）
  --selftest         内置用例自测

用法: python orphan-css-fix.py [--check] <f1.html> [f2.html ...]
"""
import os, re, sys, shutil, tempfile, datetime

# 孤儿特征：某注释行（含「按钮/弹窗/容器」等常见词，泛化为任意 CSS 注释）之后，
# 紧跟裸声明行（无选择器的 `属性:值;`）直到孤立 '}' 行。
COMMENT_RE = re.compile(r"^\s*/\*[^*]*\*/\s*$")
DECL_RE = re.compile(r"^\s*(?:[a-z-]+\s*:\s*[^;{}]+;\s*)+$", re.I)  # 单行可含多个声明

def find_orphans(lines):
    """返回孤儿块 [(start, end) 行区间（含 '}' 行），start 为注释后第一裸声明行]。"""
    orphans, i, n = [], 0, len(lines)
    depth = 0  # 前缀花括号深度：>0 表示当前行在某规则体内
    while i < n:
        ln = lines[i]
        if DECL_RE.match(ln) and depth == 0:
            # 向下找孤立 '}'，且中间必须全是声明行
            k = i
            while k < n and lines[k].strip() != "}":
                if lines[k].strip() and not DECL_RE.match(lines[k]):
                    break  # 遇到非声明内容 → 不是孤儿块
                k += 1
            if k < n and lines[k].strip() == "}" and k > i:
                orphans.append((i, k))
                i = k + 1
                continue
        depth += ln.count("{") - ln.count("}")
        if depth < 0:
            depth = 0  # 容错：游离 '}'（孤儿块本身）不计入后续深度
        i += 1
    return orphans

def fix_text(text):
    lines = text.split("\n")
    orphans = find_orphans(lines)
    if not orphans:
        return text, []
    drop = set()
    for s, e in orphans:
        drop.update(range(s, e + 1))
    kept = [ln for idx, ln in enumerate(lines) if idx not in drop]
    info = ["行 %d-%d（%d 行）" % (s + 1, e + 1, e - s + 1) for s, e in orphans]
    return "\n".join(kept), info

def process(path, check_only):
    raw = open(path, "rb").read()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8")
    if crlf:
        text = text.replace("\r\n", "\n")
    new, info = fix_text(text)
    if not info:
        print("  OK 无孤儿块:", path)
        return 0
    print("  !! 孤儿块:", path, "->", "; ".join(info))
    if check_only:
        return 1
    bak = os.path.join(tempfile.gettempdir(),
                       "orphan_%s_%s.html" % (os.path.basename(os.path.dirname(path)) or "root",
                                              datetime.datetime.now().strftime("%H%M%S")))
    shutil.copy2(path, bak)
    data = (new.replace("\n", "\r\n") if crlf else new).encode("utf-8")
    open(path, "wb").write(data)
    back = open(path, "rb").read()
    if back != data:
        print("  !! 写盘校验失败:", path)
        return 2
    remain = find_orphans(new.split("\n"))
    print("  FIXED 备份=%s 复检残留=%d" % (bak, len(remain)))
    return 0 if not remain else 2

def selftest():
    # 用例1：标准孤儿（注释+裸声明+孤立}）
    bad = "<style>\n/* 全屏播放按钮 */\n  position:fixed;top:50px;right:14px;\n  width:40px;\n}\n#navBtns{position:fixed;bottom:20px}\n</style>"
    fixed, info = fix_text(bad)
    assert info, "用例1应检出孤儿"
    assert "position:fixed;top:50px" not in fixed, "用例1多声明行未被删除"
    assert "#navBtns{position:fixed;bottom:20px}" in fixed
    # 用例2：正常规则内声明不是孤儿
    good = "<style>\n.x{\n  color:red;\n  width:10px;\n}\n.y{margin:0 auto}\n</style>"
    _, info2 = fix_text(good)
    assert not info2, "用例2误报: %s" % info2
    # 用例3：幂等
    fixed2, info3 = fix_text(fixed)
    assert not info3, "修复后应无孤儿"
    # 用例4：反测——旧 bug（只删选择器行）产生的真实形态必须被检出
    real = "<style>\n/* ===== 全屏播放按钮（右上角） ===== */\n  position:fixed;top:50px;right:14px;z-index:210;\n  opacity:.85;\n}\n\n/* ===== 翻页按钮 ===== */\n#navBtns{position:fixed !important;bottom:20px !important}\n</style>"
    fixed4, info4 = fix_text(real)
    assert info4 and "position:fixed;top:50px" not in fixed4 and "#navBtns{position:fixed !important;bottom:20px !important}" in fixed4
    print("SELFTEST ALL PASS (4 用例)")
    return 0

def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    check = "--check" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__)
        sys.exit(2)
    rc = 0
    for f in files:
        if not os.path.isfile(f):
            print("!! 不存在:", f); rc = 2; continue
        rc = max(rc, process(f, check))
    sys.exit(rc)

if __name__ == "__main__":
    main()
