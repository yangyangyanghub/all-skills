#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把配方 + 项目变量拼成最终提示词，并校验配方本身是否自洽。

用法:
    python compose_prompt.py --list
    python compose_prompt.py --check
    python compose_prompt.py --recipe render-arch --set style=安藤忠雄 --set materials=清水混凝土
    python compose_prompt.py --recipe analysis-planning --set palette="低饱和马卡龙" --out prompt.txt

设计要点：
- 占位符写错、变量没给，一律报错，不静默留空（留空会让模型自由发挥，比报错更危险）。
- --check 会逐个配方自检：有没有 anchor、骨架里的占位符能不能被解释。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RECIPE_DIR = Path(__file__).resolve().parent.parent / "references" / "style" / "recipes"
BUILTIN = {"constraint_block", "elements", "composition", "palette_map", "palette_note", "title", "id"}
PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def load_all() -> dict[str, dict]:
    out = {}
    for p in sorted(RECIPE_DIR.glob("*.json")):
        if p.stem.startswith("_"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        if "drawing" not in data or "prompt_skeleton" not in data:
            continue  # 例如 variables.json 这类参考数据，不是配方
        out[p.stem] = data
    return out


def render_builtin(r: dict, name: str) -> str | None:
    if name == "constraint_block":
        return r.get("constraint_block", "")
    if name == "elements":
        return "；".join(r.get("elements") or [])
    if name == "composition":
        return "，".join(r.get("composition") or [])
    if name == "palette_map":
        pm = r.get("palette_map") or {}
        return "；".join(f"{k}={v}" for k, v in pm.items())
    if name == "palette_note":
        return r.get("palette_note", "")
    if name == "title":
        return r.get("title", "")
    if name == "id":
        return r.get("id", "")
    return None


def placeholders(s: str) -> list[str]:
    return sorted(set(PLACEHOLDER.findall(s)))


def check_one(r: dict) -> list[str]:
    errs = []
    if not r.get("anchors"):
        errs.append("缺 anchor：没有『别人不会这么写』的那句话，配方只是在堆词")
    sk = r.get("prompt_skeleton", "")
    if not sk.strip():
        errs.append("缺 prompt_skeleton")
        return errs
    declared = set(r.get("vars") or [])
    for ph in placeholders(sk):
        if ph in BUILTIN:
            if ph == "palette_map" and not r.get("palette_map") and not r.get("palette_note"):
                errs.append("骨架用了 {palette_map} 但配方没有 palette_map/palette_note")
            continue
        if ph not in declared:
            errs.append(f"骨架占位符 {{{ph}}} 未在 vars 中声明")
    if r.get("delivery") == "deliverable" and not r.get("constraint_block"):
        errs.append("标为 deliverable 但没有 constraint_block（保真约束）")
    if r.get("delivery") == "concept-only" and "保持" in (r.get("constraint_block") or ""):
        errs.append("concept-only 却写了『保持…不变』，定位自相矛盾")
    return errs


def compose(r: dict, sets: dict[str, str], fuse: bool = False) -> str:
    sk = r["prompt_skeleton"]
    decl = set(r.get("vars") or [])
    given = dict(sets)
    given.setdefault("title", r.get("title", ""))

    missing = []
    for ph in placeholders(sk):
        if ph in BUILTIN:
            continue
        if ph not in given:
            missing.append(ph)
    if missing:
        raise SystemExit(
            "缺少变量：" + "、".join(f"--set {m}=…" for m in missing)
            + "\n本配方声明的变量：" + ("、".join(sorted(decl)) or "（无）")
        )

    def sub(m):
        name = m.group(1)
        v = render_builtin(r, name)
        if v is not None:
            return v
        return given[name]

    out = PLACEHOLDER.sub(sub, sk)
    if PLACEHOLDER.search(out):
        raise SystemExit("渲染后仍有未解析占位符：" + ",".join(placeholders(out)))

    head = f"# {r['title']}（{r['id']}）  交付定位={r['delivery']}\n"
    if r.get("anchors"):
        head += "# anchor：" + "；".join(r["anchors"]) + "\n"
    if fuse:
        fb = r.get("fusion_block")
        if not fb:
            raise SystemExit(f"配方 {r['id']} 没有 fusion_block，不支持 --fuse")
        head += "# 模式：双参考融合\n"
        out = fb + out
    return head + "\n" + out + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fuse", action="store_true", help="加双参考分工段（需配方有 fusion_block）")
    a = ap.parse_args()

    recipes = load_all()
    if not recipes:
        sys.exit(f"没有配方：{RECIPE_DIR}")

    if a.list:
        print(f"{'id':26s} {'图纸':10s} {'交付':14s} {'refs':>4s}  anchor")
        for k, r in recipes.items():
            print(f"{k:26s} {r['drawing']:10s} {r['delivery']:14s} "
                  f"{r['requires'].get('refs',0):>4d}  {len(r.get('anchors',[]))}")
        return

    if a.check:
        bad = 0
        for k, r in recipes.items():
            errs = check_one(r)
            if errs:
                bad += 1
                print(f"[FAIL] {k}")
                for e in errs:
                    print("   - " + e)
        print(f"\n共 {len(recipes)} 条，{len(recipes)-bad} 条通过，{bad} 条有问题")
        sys.exit(1 if bad else 0)

    if not a.recipe:
        ap.error("需要 --recipe，或用 --list / --check")

    if a.recipe not in recipes:
        sys.exit(f"没有配方 {a.recipe}；可用：{', '.join(recipes)}")

    sets = {}
    for kv in a.set:
        if "=" not in kv:
            sys.exit(f"--set 需要 KEY=VALUE，收到 {kv}")
        k, v = kv.split("=", 1)
        sets[k.strip()] = v.strip()

    text = compose(recipes[a.recipe], sets, fuse=a.fuse)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print("已写入 " + a.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
