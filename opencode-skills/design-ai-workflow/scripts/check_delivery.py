#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付闸门校验：把"我核对过了"变成可机器校验的结论。

用法:
    python check_delivery.py --manifest 交付清单.json
    python check_delivery.py --manifest 交付清单.json --json

退出码: 0 通过 / 1 有阻塞问题 / 2 清单本身无法解析

它只拦"自欺"这一层：状态机、字段完整性、证据文件真实性、矛盾。
它不能判断图好不好看、造型对不对——那必须人看。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STAGES = {"review", "design-draft", "design-final"}
DELIVERY = {"deliverable", "intent-only"}
CHECK_STATES = {"pass", "fail", "unverified"}
DRAWINGS = {
    "concept", "masterplan", "analysis",
    "render-interior", "render-facade", "render-renewal", "birdseye",
    "construction",
}
MAGIC = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8",
    "webp_riff": b"RIFF",
}
MIN_DIFF = 8
MIN_REASON = 10


def is_image(path: Path) -> bool:
    try:
        head = path.read_bytes()[:12]
    except OSError:
        return False
    if head[:8] == MAGIC["png"]:
        return True
    if head[:2] == MAGIC["jpg"]:
        return True
    if head[:4] == MAGIC["webp_riff"] and head[8:12] == b"WEBP":
        return True
    return False


def check(manifest: dict) -> list[str]:
    errs: list[str] = []

    stage = manifest.get("stage")
    if stage not in STAGES:
        errs.append(f"stage 必须是 {sorted(STAGES)} 之一，实际为 {stage!r}")
        stage = None

    images = manifest.get("images")
    if not isinstance(images, list) or not images:
        errs.append("images 必须是非空数组")
        return errs

    for i, it in enumerate(images):
        tag = f"images[{i}]"
        if not isinstance(it, dict):
            errs.append(f"{tag} 必须是对象")
            continue

        drawing = it.get("drawing")
        if drawing not in DRAWINGS:
            errs.append(f"{tag}.drawing 必须是 {sorted(DRAWINGS)} 之一，实际 {drawing!r}")

        delivery = it.get("delivery")
        if delivery not in DELIVERY:
            errs.append(f"{tag}.delivery 必须是 {sorted(DELIVERY)} 之一，实际 {delivery!r}")

        f = it.get("file")
        if not f:
            errs.append(f"{tag}.file 缺失")
        elif not Path(f).is_file():
            errs.append(f"{tag}.file 不存在：{f}")

        checks = it.get("checks")
        if not isinstance(checks, dict) or not checks:
            errs.append(f"{tag}.checks 必须是非空对象（至少含三查）")
            checks = {}
        else:
            for k, v in checks.items():
                if v not in CHECK_STATES:
                    errs.append(f"{tag}.checks.{k} 必须是 {sorted(CHECK_STATES)} 之一，实际 {v!r}")

        ctrl = it.get("control_input")
        if delivery == "deliverable":
            if not ctrl:
                errs.append(f"{tag} 标为 deliverable 但 control_input 为空——没有控制图的图不能当终稿")
            elif not Path(ctrl).is_file():
                errs.append(f"{tag}.control_input 不存在：{ctrl}")
            if any(v != "pass" for v in checks.values()):
                errs.append(f"{tag} 标为 deliverable 但三查未全部 pass：{checks}")

        if delivery == "intent-only":
            reason = (it.get("intent_reason") or "").strip()
            if len(reason) < MIN_REASON:
                errs.append(f"{tag} 标为 intent-only 但 intent_reason 少于 {MIN_REASON} 字（当前 {len(reason)}）")

        ev = it.get("evidence")
        if not isinstance(ev, list) or not ev:
            errs.append(f"{tag}.evidence 必须是非空数组（截图或对照图路径）")
        else:
            for p in ev:
                pp = Path(p)
                if not pp.is_file():
                    errs.append(f"{tag}.evidence 文件不存在：{p}")
                elif not is_image(pp):
                    errs.append(f"{tag}.evidence 不是 PNG/JPEG/WebP：{p}")

        diff = (it.get("differences") or "").strip()
        if len(diff) < MIN_DIFF:
            errs.append(f"{tag}.differences 少于 {MIN_DIFF} 字（当前 {len(diff)}）——写不出差异说明没真核对")

    if stage == "design-final":
        for i, it in enumerate(images):
            if it.get("delivery") != "deliverable":
                errs.append(f"images[{i}] 在 design-final 档却未标 deliverable")
    if stage in {"review", "design-draft"}:
        for i, it in enumerate(images):
            if it.get("delivery") == "deliverable":
                errs.append(f"images[{i}] 在 {stage} 档不得标 deliverable")

    return errs


def main() -> None:
    ap = argparse.ArgumentParser(description="交付闸门校验")
    ap.add_argument("--manifest", required=True, help="交付清单 JSON 路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    a = ap.parse_args()

    p = Path(a.manifest)
    if not p.is_file():
        sys.exit(f"清单不存在：{p}")
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"清单 JSON 解析失败：{e}")

    errs = check(manifest)
    ok = not errs

    if a.json:
        print(json.dumps({"ok": ok, "errors": errs}, ensure_ascii=False, indent=2))
    else:
        if ok:
            print(f"通过：{len(manifest.get('images', []))} 个交付项，stage={manifest.get('stage')}")
            print("注意：脚本通过 != 可以交付。照片相似度、造型、截图真实性仍须人看。")
        else:
            print(f"未通过，{len(errs)} 个阻塞问题：")
            for e in errs:
                print(" - " + e)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
