#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按输入条件确定性选择模型与参数。

设计原则：**能查表判断的，不交给模型猜。**
条件全部可枚举（有没有几何控制图、要不要读图、几张参考图、要不要 mask、要不要 4K、走哪个套餐），
所以用一张表 + 一组硬约束，比让 LLM "看着选"稳定得多。

表的每一行都来自实测（2026-10-29，见 references/pipeline-fusion.md 与 known-issues.md）。

用法:
    python select_model.py --task render --base 1 --mood 1
    python select_model.py --task read --image 1
    python select_model.py --task mood --plan tp
    python select_model.py --list
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---- Token Plan 套餐白名单（2026-10-29 用 /compatible-mode/v1/models 实测拉取，共 21 个）----
TP_ENDPOINT = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
TP_WHITELIST = {
    "auto", "decision-model-preview",
    "deepseek-v4-flash-0731", "deepseek-v4-pro", "deepseek-v4-pro-0813",
    "deepseek-v4.1-flash", "deepseek-v4.1-flash-1017",
    "glm-5.2", "glm-5.3",
    "qwen-audio-3.0-asr-flash", "qwen-audio-3.0-realtime-plus", "qwen-audio-3.0-tts-plus",
    "qwen-image-3.0-pro",
    "qwen3.6-flash", "qwen3.7-max", "qwen3.7-plus", "qwen3.8-flash", "qwen3.8-max",
    "wan2.7-image", "wan2.7-image-pro",
    "wan3.0-video",
}
TP_VISION_PREFIXES = ("qwen-vl", "qwen3-vl", "qwen-omni", "qwen3-omni")
# 模型能力表
CAPS = {
    "wan2.7-image-pro": {
        "provider": "dashscope", "kind": "image", "priority": 1,
        "refs_max": 9, "refs_ok": True,
        "max_px_with_ref": 2048 * 2048, "mask": False, "status": "ok",
        "note": "唯一能吃多张参考图的可用出图模型；带 ref 时上限 2048²",
    },
    "wan2.7-image": {
        "provider": "dashscope", "kind": "image", "priority": 2,
        "refs_max": 9, "refs_ok": True,
        "max_px_with_ref": 2048 * 2048, "mask": False, "status": "ok",
        "note": "同族较弱版本，仅在 pro 不可用时降级",
    },
    "qwen-image-3.0-pro": {
        "provider": "dashscope", "kind": "image", "priority": 3,
        "refs_max": 0, "refs_ok": False,
        "max_px_with_ref": 0, "mask": False, "status": "ok",
        "note": "只吃纯文本；图面质量最强，用来出氛围稿",
    },
    "qwen3.8-flash": {
        "provider": "dashscope", "kind": "vlm", "priority": 1,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": False, "status": "ok",
        "note": "读图默认档（TP 白名单内）。实测能读出 10 个房间名与两处卫生间标注",
    },
    "qwen3.8-max": {
        "provider": "dashscope", "kind": "vlm", "priority": 2,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": False, "status": "ok",
        "note": "读图高精度档（TP 白名单内）。实测额外读出面积标注与招牌文字：POS/拉卡拉/和平交易厅",
    },
    "qwen3.7-plus": {
        "provider": "dashscope", "kind": "vlm", "priority": 3,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": False, "status": "ok",
        "note": "读图备选（TP 白名单内）。房间名准确，街景细节略弱于 3.8",
    },
    "auto": {
        "provider": "dashscope", "kind": "vlm", "priority": 4,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": False, "status": "ok",
        "note": "路由模型（TP 白名单内）。平面图可读，街景返回空，仅作兜底",
    },
    "gemini-3-flash-preview": {
        "provider": "google", "kind": "vlm", "priority": 5,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": False, "status": "ok",
        "note": "跨厂商备用（GOOGLE_API_KEY）。实测可准确读白模与平面图",
    },
    "deepseek-v4.1-flash": {
        "provider": "dashscope", "kind": "vlm", "priority": 9,
        "refs_max": 0, "refs_ok": False,
        "max_px_with_ref": None, "mask": False, "status": "disabled",
        "note": "HTTP 200 但会编：街景把招牌读成『巴拉巴拉』『擦擦』，实际不存在。不可用于读图",
    },
    "qwen3-vl-plus": {
        "provider": "dashscope", "kind": "vlm", "priority": 9,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": False, "status": "disabled",
        "note": "TP 白名单不含 qwen-vl 系列（404 Model not exist）；按量付费才可用",
    },
    "gemini-3-pro-image": {
        "provider": "google", "kind": "image", "priority": 0,
        "refs_max": 99, "refs_ok": True,
        "max_px_with_ref": None, "mask": True, "status": "disabled",
        "note": "本机 key 该模型免费额度为 0；开通后把 status 改 ok 即自动进入选择",
    },
}

TASKS = {
    "read": {"desc": "读图：识别空间/房间/尺寸，产出结构化描述", "kind": "vlm"},    "render": {"desc": "效果图（室内/外观/改造/鸟瞰）", "kind": "image", "needs_geometry": True},
    "masterplan": {"desc": "总平面图", "kind": "image", "needs_geometry": True},
    "concept": {"desc": "设计概念图（结构可变）", "kind": "image", "needs_geometry": False},
    "mood": {"desc": "只出材质氛围稿", "kind": "image", "needs_geometry": False},
    "edit": {"desc": "局部重绘 / 改图", "kind": "image", "needs_geometry": False},
    "analysis": {"desc": "分析图（不走图像模型）", "kind": "none"},
    "construction": {"desc": "施工图（走 CAD 落图）", "kind": "none"},
}


def decide(task, base, mood, refs, need_mask, want_4k, plan):
    out = {"task": task, "plan": plan, "steps": [], "warnings": [], "disabled_notes": []}
    if task not in TASKS:
        return {"error": f"未知 task: {task}，可选 {sorted(TASKS)}"}

    spec = TASKS[task]

    if spec["kind"] == "none":
        out["steps"].append({"provider": None, "model": None, "refs": [],
                             "reason": "该图种不走图像模型"})
        if task == "analysis":
            out["steps"][0]["reason"] = "分析图：底图可由 AI 出，色块/箭头/标注/图例必须矢量叠加"
        if task == "construction":
            out["steps"][0]["reason"] = "施工图：走 AutoCADMCP 落真图元，位图不可交付"
        return out

    # ---------- 读图 ----------
    if spec["kind"] == "vlm":
        cands = sorted([n for n, c in CAPS.items() if c["kind"] == "vlm" and c["status"] == "ok"],
                       key=lambda n: CAPS[n]["priority"])
        if not cands:
            out["error"] = "没有可用的视觉模型"
            return out
        pick = cands[0]
        cap = CAPS[pick]
        in_tp = pick in TP_WHITELIST
        out["steps"].append({
            "provider": cap["provider"], "model": pick,
            "refs": [{"role": "待读图", "arg": "--image"}],
            "reason": (cap["note"] if in_tp else
                       f"{pick} 不在 Token Plan 白名单内，走 {cap['provider']} 的独立凭据"),
        })
        for n, c in CAPS.items():
            if c["kind"] == "vlm" and c["status"] != "ok":
                out["disabled_notes"].append(f"{n}: {c['note']}")
        if plan == "tp" and not in_tp:
            out["warnings"].append(f"选中的 {pick} 不在 TP 白名单内，需要 {cap['provider']} 的 key")
        return out

    # ---------- 出图 ----------
    if need_mask:
        out["warnings"].append("当前 CLI 无 --mask；真 mask 重绘需 bl image edit 或生成后合成")
        out["steps"].append({
            "provider": "bailian-cli", "model": "bl image edit",
            "refs": [{"role": "待编辑图", "arg": "--image target"}],
            "reason": "需要 mask 编辑：用百炼 CLI 的 image edit，或退回 compose.py 合成",
        })

    used = (1 if base else 0) + (1 if mood else 0) + max(0, refs)

    if used > 0:
        cands = [n for n, c in CAPS.items() if c["kind"] == "image" and c["status"] == "ok" and c["refs_ok"]]
        if not cands:
            out["error"] = "没有可用出图模型能接受参考图"
            return out
        cands.sort(key=lambda n: CAPS[n]["priority"])
        pick = cands[0]
        cap = CAPS[pick]
        if used > cap["refs_max"]:
            out["warnings"].append(f"参考图 {used} 张超过 {pick} 上限 {cap['refs_max']} 张")
        rs = []
        if base:
            rs.append({"role": "结构依据", "arg": "--ref base"})
        if mood:
            rs.append({"role": "材质/氛围依据", "arg": "--ref mood"})
        if refs:
            rs.append({"role": "额外参考", "arg": f"--ref x{refs}"})
        out["steps"].append({
            "provider": cap["provider"], "model": pick, "refs": rs,
            "reason": f"本轮有 {used} 张参考图，只有能吃 ref 的模型才保得住输入",
        })
        if want_4k:
            out["warnings"].append(f"带 ref 时 {pick} 上限 2048²，拿不到 4K；按 2K 出图后放大")
    else:
        if spec.get("needs_geometry"):
            out["warnings"].append("该任务需要几何保真，但没有基础图；只能出意向图，不可标可交付")
        out["steps"].append({
            "provider": "dashscope", "model": "qwen-image-3.0-pro", "refs": [],
            "reason": "纯文本出图，图面质量优先；无几何输入，不承诺结构保真",
        })

    # ---------- 套餐白名单校验 ----------
    for s in out["steps"]:
        if s["provider"] == "dashscope" and plan == "tp" and s["model"] not in TP_WHITELIST:
            out["warnings"].append(f"{s['model']} 不在 Token Plan 白名单内，调用会报 Model not exist")
    for n, c in CAPS.items():
        if c["status"] != "ok" and c["kind"] == "image":
            out["disabled_notes"].append(f"{n}: {c['note']}")
    return out


def main():
    ap = argparse.ArgumentParser(description="确定性选择模型")
    ap.add_argument("--task", default="render", choices=sorted(TASKS))
    ap.add_argument("--base", type=int, default=0, help="1=有几何控制图")
    ap.add_argument("--mood", type=int, default=0, help="1=已有氛围稿")
    ap.add_argument("--refs", type=int, default=0, help="额外参考图数量")
    ap.add_argument("--need-mask", type=int, default=0)
    ap.add_argument("--want-4k", type=int, default=0)
    ap.add_argument("--plan", default="tp", choices=["tp", "payg"],
                    help="tp=Token Plan 套餐（有白名单限制）；payg=按量付费")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        print("== 模型能力 ==")
        for n, c in CAPS.items():
            print(f"{n:24s} kind={c['kind']:<6} refs<={c['refs_max']:<3} mask={str(c['mask']):<5} {c['status']}")
            print(f"{'':24s} {c['note']}")
        vlm_in_tp = [n for n, c in CAPS.items()
                     if c["kind"] == "vlm" and c["status"] == "ok" and n in TP_WHITELIST]
        print(f"\n== Token Plan 白名单（{len(TP_WHITELIST)} 个）==")
        print("可读图的 TP 模型（实测）：" + "、".join(sorted(vlm_in_tp)))
        for m in sorted(TP_WHITELIST):
            print("  " + m)
        return

    r = decide(a.task, bool(a.base), bool(a.mood), a.refs, bool(a.need_mask), bool(a.want_4k), a.plan)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    if r.get("error"):
        print("错误：" + r["error"]); sys.exit(1)
    print(f"任务：{a.task}（{TASKS[a.task]['desc']}）  套餐：{a.plan}")
    for s in r["steps"]:
        print(f"\n→ {s['provider'] or '-'} / {s['model'] or '-'}")
        print("  理由：" + s["reason"])
        if s["refs"]:
            print("  参考：" + "；".join(f"{x['role']}={x['arg']}" for x in s["refs"]))
    for w in r["warnings"]:
        print("\n[!] " + w)
    if r["disabled_notes"]:
        print("\n未启用：")
        for d in r["disabled_notes"]:
            print("  - " + d)


if __name__ == "__main__":
    main()
