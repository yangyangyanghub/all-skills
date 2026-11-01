#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""断言评分器：按关键词族判定每条断言是否满足，输出 grading.json。

为什么用关键词族而不是纯人工：同一批答案要反复评（迭代多轮），
脚本能保证同一标准不漂移；关键词族允许同义表达，避免"必须原句"的过拟合。

用法: python grade.py <iteration_dir>
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

# 每条断言 = (断言原文, 命中任一即算过 的关键词族)
RULES = {
    "judge-deliverable": [
        ("明确指出手绘总平直接转鸟瞰会导致布局漂移或重排",
         [["漂移", "重排", "不一致", "走样", "改动", "变形"], ["布局", "方案", "路网", "建筑位置"]]),
        ("明确说明该图不能作为施工参考或不可交付，只能当意向图",
         [["意向图", "参考图", "不能用于施工", "不能作为施工", "不可交付", "不能直接交付", "仅供", "示意"]]),
        ("给出至少一条可保真的替代路径（体块模型/分区涂鸦/三维出图）",
         [["体块", "白模", "三维", "SU", "SketchUp", "分区涂鸦", "涂鸦", "建模"]]),
        ("没有把「换更强的模型」当作解决办法",
         [["NEG:换更强", "NEG:换个更强", "NEG:用更强的模型", "NEG:模型不行就换"]]),
    ],
    "pick-model-two-stage": [
        ("给出两段式或双参考方案（先氛围/材质稿，再双参考融合）",
         [["两段", "两步", "双参考", "两张参考", "氛围稿", "两个阶段"]]),
        ("指出 qwen 系列不吃参考图（只能纯文生图）",
         [["qwen"], ["不吃", "不支持参考", "不能带参考", "纯文生图", "只吃文本", "无参考"]]),
        ("指出带参考图时有分辨率上限（2048/2K），拿不到 4K",
         [["2048", "2K", "2k", "4K"], ["上限", "限制", "拿不到", "不能出", "最多", "顶到"]]),
        ("提到出图后要实际看图核对结构，而不是只看接口成功",
         [["看图", "核对", "检查画面", "验收", "肉眼", "比对", "三查"]]),
    ],
    "analysis-two-stage": [
        ("区分分析逻辑（人定/矢量）与分析表现（可由 AI 重绘）",
         [["逻辑"], ["矢量", "人工", "人定", "自己画"], ["表现", "重绘", "出图"]]),
        ("给出两步法：先出结构稿，再用「原底图 + 该结构稿」双参考出定稿",
         [["两段", "两步", "双参考", "结构稿", "第一轮", "再融合"]]),
        ("强调第二张参考图必须与底图结构一致，不能用其它场地的图",
         [["结构一致", "同一个底图", "同结构", "不能用其它", "会被平均", "互相平均", "布局平均", "必须来自同一"]]),
        ("没有承诺一次单模型就能出可交付的分析图",
         [["NEG:一次就能出", "NEG:直接就能出", "NEG:单模型就够"]]),
    ],
    "concept-no-model": [
        ("概念阶段可以先不建模，用草图/体块直接出，允许结构变化",
         [["不必", "不用", "可以不", "无需", "不需要"], ["建模", "建模型", "建个模", "模型"]]),
        ("明确概念图不能当方案图、不能拿来对图纸",
         [["当方案", "作为方案", "方案图", "对图", "对图纸", "只能定方向"],
          ["不能", "不得", "不可", "不是", "别"]]),
        ("说清若要『能对图纸』才必须上白模或线稿",
         [["白模", "线稿", "体块模型", "几何控制", "三维模型"]]),
    ],
    "masterplan-root-cause": [
        ("把原因归为换视角导致重排布局，而不是模型不够强",
         [["换视角", "视角变", "从平面到鸟瞰", "视角不同"], ["重排", "漂", "不一致", "重画", "对不上"]]),
        ("给出体块模型鸟瞰 + 分区涂鸦的路线",
         [["体块", "白模", "三维"], ["涂鸦", "分区"]]),
        ("提到出图后要数水体/栋数/对路网这类具体核对",
         [["水体", "栋数", "路网", "道路", "建筑数量", "开口"]]),
    ],
    "construction-dwg": [
        ("明确位图『施工图』不可交付，必须落真图元",
         [["位图", "图片", "PNG", "生成的图"], ["不能", "不可", "不算", "不是"]]),
        ("给出 CAD 落图路线（plan.json → 校验 → 落图 → 导出核对）",
         [["CAD", "DWG", "AutoCAD"], ["落图", "图元", "画进", "实体"]]),
        ("声明专业规范未自动校验、需人工审图",
         [["规范", "专业"], ["人工", "复核", "审查", "自审", "校审"]]),
    ],
    "renewal-keep-structure": [
        ("指出整图重绘会画成重建",
         [["重建", "拆掉", "拆了", "推倒"], ["整图", "一次性", "直接", "重绘", "全图"]]),
        ("给出分区涂鸦/局部重绘 + 生成后合成的方案",
         [["涂鸦", "局部重绘", "mask", "蒙版", "分区"], ["合成", "叠加", "拼"]]),
        ("强调保留区域的像素不能动（不是靠 prompt 写『保持不变』）",
         [["像素"], ["不能动", "不变", "不动", "保留", "原样"]]),
    ],
    "delivery-declaration": [
        ("提到三查的具体项（数元素/数楼层/对路网或开口）",
         [["水体", "栋", "楼层", "路网", "开口", "门窗", "构件"]]),
        ("要求区分可交付与仅意向，并写明降级原因",
         [["可交付"], ["意向"], ["原因", "理由", "说明"]]),
        ("要求有证据（截图/对照图），而不是口头说看过了",
         [["截图", "对照图", "证据", "并排", "留痕"]]),
    ],
    "diagnose-white-window": [
        ("把原因归到可控环节（参考图/prompt/负向约束），而不是归咎模型能力",
         [["参考", "prompt", "负向", "氛围稿", "约束", "第一段", "第二段"],
          ["没", "未", "缺", "不足", "不存在", "少"]]),
        ("修法给出加一张氛围稿做第二参考（双参考）",
         [["氛围稿", "第二参考", "两张参考", "双参考", "再加一张"]]),
        ("给出负向约束：不得新增参考图里没有的构件",
         [["不得新增", "不要新增", "负向", "禁止新增"], ["构件", "墙板", "元素", "部件"]]),
    ],
}


def hit(text: str, families: list[list[str]]) -> bool:
    """families 之间是 AND，族内是 OR。NEG: 前缀表示"出现即不通过"。"""
    for fam in families:
        neg = [k[4:] for k in fam if k.startswith("NEG:")]
        pos = [k for k in fam if not k.startswith("NEG:")]
        if neg:
            if any(k in text for k in neg):
                return False
        elif pos:
            if not any(k in text for k in pos):
                return False
    return True


def grade(run_dir: str, eval_name: str, assertions: list[str]) -> dict:
    ans = os.path.join(run_dir, "outputs", "answer.md")
    text = io.open(ans, encoding="utf-8").read() if os.path.isfile(ans) else ""
    results = []
    for a, rule in zip(assertions, RULES[eval_name]):
        # 规则文本以 grade.py 为准；metadata 里的旧文案允许漂移，按顺序对应
        passed = hit(text, rule[1])
        results.append({
            "text": a,
            "passed": passed,
            "evidence": ("命中关键词族" if passed else "未命中：" + str(rule[1])),
        })
    return {
        "answer_exists": bool(text),
        "answer_chars": len(re.sub(r"\s", "", text)),
        "expectations": results,
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
    }


def main() -> None:
    it = sys.argv[1]
    rows = []
    for d in sorted(os.listdir(it)):
        p = os.path.join(it, d)
        if not os.path.isdir(p) or not d.startswith("eval-"):
            continue
        m = re.match(r"eval-\d+-(.+)", d)
        name = m.group(1) if m else d
        for cfg in ("with_skill", "without_skill", "old_skill"):
            rd = os.path.join(p, cfg)
            if not os.path.isdir(rd):
                continue
            meta = json.load(io.open(os.path.join(rd, "eval_metadata.json"), encoding="utf-8"))
            g = grade(rd, name, meta["assertions"])
            g.update({"run": d + "/" + cfg, "eval_name": name, "config": cfg})
            io.open(os.path.join(rd, "grading.json"), "w", encoding="utf-8").write(
                json.dumps(g, ensure_ascii=False, indent=1))
            rows.append(g)

    print(f"{'eval':28s} {'config':14s} {'pass':>5s} {'chars':>6s}")
    for r in rows:
        print(f"{r['eval_name'][:28]:28s} {r['config']:14s} {r['passed']}/{r['total']:<3d} {r['answer_chars']:>6d}")

    agg = {}
    for r in rows:
        s = agg.setdefault(r["config"], {"p": 0, "t": 0, "n": 0, "chars": 0})
        s["p"] += r["passed"]; s["t"] += r["total"]; s["n"] += 1; s["chars"] += r["answer_chars"]
    print()
    for cfg, s in agg.items():
        print(f"{cfg:14s} pass {s['p']}/{s['t']} = {s['p']/max(1,s['t']):.0%}   平均 {s['chars']//max(1,s['n'])} 字")
    json.dump(agg, io.open(os.path.join(it, "aggregate.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
