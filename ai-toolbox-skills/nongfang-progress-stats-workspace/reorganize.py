# -*- coding: utf-8 -*-
"""把 <config>/workdir 整理成 skill-creator 要求的 <config>/run-1/outputs 结构。"""
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IT = r"C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1"
TEMPLATE_NAME = "农房整治工作卷宗整改进展统计表(修改后).xlsx"
EVALS = ("eval-0-first-run", "eval-1-rolling", "eval-2-missing-county")
CONFIGS = ("with_skill", "without_skill")

for eval_name in EVALS:
    eval_dir = os.path.join(IT, eval_name)
    meta_path = os.path.join(eval_dir, "eval_metadata.json")
    for config in CONFIGS:
        config_dir = os.path.join(eval_dir, config)
        workdir = os.path.join(config_dir, "workdir")
        run_dir = os.path.join(config_dir, "run-1")
        outputs = os.path.join(run_dir, "outputs")
        os.makedirs(outputs, exist_ok=True)
        for name in os.listdir(workdir):
            src = os.path.join(workdir, name)
            if not os.path.isfile(src):
                continue
            if name == TEMPLATE_NAME:
                continue
            if "nf" in name.lower() and "整改" in name:
                continue
            keep = name == "agent_answer.txt" or (
                name.lower().endswith(".xlsx") and not name.startswith(".nongfang")
            )
            if not keep:
                continue
            shutil.copy2(src, os.path.join(outputs, name))
        if os.path.exists(meta_path):
            shutil.copy2(meta_path, os.path.join(run_dir, "eval_metadata.json"))
        print("%-22s %-14s -> %s" % (eval_name, config,
                                     ", ".join(sorted(os.listdir(outputs))) or "(empty)"))

print()
print("done")
