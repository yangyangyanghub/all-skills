#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键执行脚本
执行完整的日报分析流程
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """执行命令并返回是否成功"""
    print(f"\n{'='*50}")
    print(f"[STEP] {description}")
    print(f"[CMD] {cmd}")
    print("=" * 50)
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"[ERROR] {description} 失败")
        return False
    
    print(f"[OK] {description} 完成")
    return True


def main():
    parser = argparse.ArgumentParser(description="日报分析一键执行")
    parser.add_argument(
        "--date",
        default="today",
        help="目标日期，支持 YYYY-MM-DD 或 today/yesterday"
    )
    parser.add_argument(
        "--template",
        default="员工日报",
        help="审批模板名称"
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent.parent.parent.parent / "daily-reports"),
        help="输出目录"
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="跳过钉钉推送"
    )
    parser.add_argument(
        "--users",
        help="推送通知的用户ID列表，逗号分隔"
    )
    parser.add_argument(
        "--use-oa",
        action="store_true",
        help="使用OA审批接口获取数据"
    )
    
    args = parser.parse_args()
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    output_dir = Path(args.output)
    
    # 检查部门人数配置文件
    dept_config_file = output_dir / "dept_member_count.json"
    dept_config_arg = f" --dept-config={dept_config_file}" if dept_config_file.exists() else ""
    
    if dept_config_file.exists():
        print(f"[INFO] 检测到部门人数配置文件: {dept_config_file}")
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    
    # 解析日期
    if args.date == "today":
        date_str = datetime.now().strftime("%Y-%m-%d")
    elif args.date == "yesterday":
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date_str = args.date
    
    print(f"\n{'#'*60}")
    print(f"# 日报智能分析")
    print(f"# 日期: {date_str}")
    print(f"# 模板: {args.template}")
    print(f"{'#'*60}")
    
    # 步骤1: 获取日报数据
    if args.use_oa:
        # 使用OA审批接口时，自动获取部门人数
        fetch_cmd = f'python "{script_dir}/fetch_oa_reports.py" --date={args.date} --template={args.template} --output={args.output} --fetch-dept-count{dept_config_arg}'
    else:
        fetch_cmd = f'python "{script_dir}/fetch_reports.py" --date={args.date} --template={args.template} --output={args.output}'
    
    if not run_command(fetch_cmd, "获取日报数据"):
        sys.exit(1)
    # 步骤2: 分析评分
    if not run_command(
        f'python "{script_dir}/analyze_reports.py" --date={args.date} --input={args.output}',
        "分析评分"
    ):
        sys.exit(1)
    
    # 步骤3: 生成Markdown报告
    if not run_command(
        f'python "{script_dir}/generate_report.py" --date={args.date} --input={args.output}',
        "生成Markdown报告"
    ):
        sys.exit(1)
    
    # 步骤4: 生成HTML可视化报告
    if not run_command(
        f'python "{script_dir}/generate_html_report.py" --date={args.date} --input={args.output}',
        "生成HTML可视化报告"
    ):
        print("[WARN] HTML报告生成失败，继续执行...")
    
    # 步骤5: 推送到钉钉
    if not args.skip_push:
        push_cmd = f'python "{script_dir}/push_dingtalk.py" --date={args.date} --input={args.output}'
        if args.users:
            push_cmd += f' --users={args.users}'
        
        if not run_command(push_cmd, "推送到钉钉"):
            print("[WARN] 推送失败，但其他步骤已完成")
    
    print(f"\n{'#'*60}")
    print(f"# 完成！")
    print(f"# 报告目录: {args.output}/{date_str}/")
    print(f"# - Markdown报告: daily-report.md")
    print(f"# - HTML可视化报告: report.html")
    print(f"# - Excel数据清单: data-list.xlsx")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()