#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资料目录提取脚本 v4
从钉钉OA审批日报数据中提取员工手里的资料清单

核心思路（反转逻辑）：
  不是"过滤掉工作句子"，而是"直接提取资料名称"
  用模式匹配找 "项目名/地名 + 资料类型" 组合
  例如：从"正在编写邯郸市供热管网初步设计"中提取 "邯郸市供热管网初步设计"
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

DEFAULT_REPORTS_DIR = str(Path(__file__).parent.parent.parent.parent.parent / "ding-reports")


class MaterialExtractor:
    """资料目录提取器 v4 - 模式匹配版"""

    def __init__(self):
        # 资料类型词（从具体到宽泛排序，匹配时优先匹配更具体的）
        self.material_type_words = [
            # 设计类（最具体的优先）
            "施工图", "竣工图", "规划图", "初步设计", "设计方案",
            "平面图", "立面图", "剖面图", "效果图", "规划图则",
            "图纸", "图册", "图集",
            # 文档类
            "调研报告", "研究报告", "考察报告", "评估报告",
            "可行性报告", "申请报告",
            "方案", "报告", "总结", "说明书", "建议书", "计划书",
            "指南", "手册", "白皮书", "论文", "可研",
            # 规范类
            "规范", "标准", "规程", "规定",
            # 数据类
            "台账", "清单", "统计表", "汇总表", "花名册", "调查表",
            "报表", "数据库",
            # 演示类
            "PPT", "课件", "讲义", "培训资料",
        ]

        # 资料分类映射
        self.type_category_map = {
            "施工图": "设计类", "竣工图": "设计类", "规划图": "设计类",
            "初步设计": "设计类", "设计方案": "设计类",
            "平面图": "设计类", "立面图": "设计类", "剖面图": "设计类",
            "效果图": "设计类", "规划图则": "设计类",
            "图纸": "设计类", "图册": "设计类", "图集": "设计类",
            "设计": "设计类",
            "调研报告": "调研类", "研究报告": "调研类",
            "考察报告": "调研类", "评估报告": "调研类",
            "可行性报告": "调研类", "申请报告": "文档类",
            "方案": "文档类", "报告": "文档类", "总结": "文档类",
            "说明书": "文档类", "建议书": "文档类", "计划书": "文档类",
            "指南": "文档类", "手册": "文档类", "白皮书": "文档类",
            "论文": "文档类", "可研": "文档类",
            "规范": "标准类", "标准": "标准类", "规程": "标准类", "规定": "标准类",
            "台账": "数据类", "清单": "数据类", "统计表": "数据类",
            "汇总表": "数据类", "花名册": "数据类", "调查表": "数据类",
            "报表": "数据类", "数据库": "数据类",
            "PPT": "演示类", "课件": "演示类", "讲义": "演示类",
            "培训资料": "演示类",
        }

        # 分类图标
        self.category_icons = {
            "文档类": "📄", "设计类": "🎨", "数据类": "📊",
            "演示类": "📽️", "标准类": "📋", "调研类": "🔍",
            "代码类": "💻",
        }

        # 具体标识符（地名/项目名/编号等）
        # 资料名称前缀必须包含至少一个，才认为是具体资料
        self.specific_patterns = [
            r'[\u4e00-\u9fa5]{2,}(区|县|市|镇|村|路|街|道)',  # 地名
            r'[\u4e00-\u9fa5]{2,}(项目|工程|标段|地块|片区)',    # 项目
            r'(一期|二期|三期|[一二三四五六七八九十]+期)',        # 期数
            r'(20\d{2})',                                       # 年份
            r'(第[一二三四五六七八九十\d]+[批次标])',             # 编号
        ]

        # 剥离的动作前缀（从提取结果中去掉这些，只保留资料名）
        self.strip_prefixes = [
            # 明确的产出动作（编写/修改类）
            r'^(正在|继续|持续)?(编写|撰写|修改|修订|制作|创建|绘制|开发|整理|梳理|审核|审批|完善|优化|更新|编制|起草|拟定)',
            # 工作动作
            r'^(外出|送|排版|沟通|收到|今日收到|查询|查阅|检索|研读|解读|细化|同步|催促)',
            # 搭配介词的动作
            r'^(给\S{1,6}汇报|与\S{1,6}沟通|主要参加|整理省|对|按要求|按格式|按省厅\S{0,6}文件)',
            r'^(依据|按照|围绕|关于|关于印发|进行|完成|将)',
            # AI工具相关
            r'^(使用|利用|借助|应用)(豆包|AI|deepseek|ChatGPT|kimi|文心|通义)\S{0,6}(解读|分析|查询|检索|对比)?',
            # 时间/序号
            r'^(上午|下午|今天|昨日|同时|继续)(昨天|今日|当天)?(对|对社区)?',
            r'^[、\d\-\s]+[.、\s]*',
            # 剩余杂项
            r'^(未完成|已出|已提交|建设)',
            # 部门名前缀
            r'^(利用科|规划科|用地科|测绘科|设计科|综合科)\S*',
        ]

        # 剥离的后缀动作（名称末尾的动作描述）
        self.strip_suffixes = [
            r'(盖章|打印|报送|提交|发送|移交|交付|备案|归档)(及\S*)?$',
            r'及(打印|报送|提交|发送|归档)\S*$',
        ]

        # 纯动作+资料类型的组合（不是资料名，是工作描述）
        self.action_material_combos = [
            r'汇报会议',  # 包含"汇报会议"的都不是资料名
        ]

        # 部门名前缀（从名称中去掉）
        self.dept_prefixes = [
            r'^(利用科|规划科|用地科|测绘科|设计科|综合科)\S*',
        ]

        # 状态识别
        self.status_patterns = {
            "正在编写": ["编写", "撰写", "起草", "拟", "编制"],
            "正在修改": ["修改", "修订", "完善", "优化"],
            "正在制作": ["制作", "创建", "绘制", "开发", "建设"],
            "正在整理": ["整理", "梳理", "汇总", "归档"],
            "正在审核": ["审核", "审批", "审查", "校对", "复核", "评审"],
            "已完成": ["完成", "已出", "已提交", "已交付", "定稿"]
        }

    def detect_status(self, text: str) -> str:
        """检测资料状态"""
        for status, patterns in self.status_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return status
        return "进行中"

    def extract_material_name(self, text: str, type_word: str, type_pos: int) -> Optional[str]:
        """
        从文本中提取资料名称
        策略：从类型词往前截取，找到资料名的起点
        """
        # 类型词及之后的内容（可能还有后缀如"初步设计"）
        after = text[type_pos + len(type_word):]

        # 往前找：最多取30个字符作为前缀
        max_prefix = 30
        start = max(0, type_pos - max_prefix)
        prefix = text[start:type_pos]

        # 从前缀中找资料名的起点
        # 资料名通常以地名/项目名开头
        # 从后往前找分隔点（逗号、句号、顿号、空格、序号等）
        separators = ['，', '、', '。', '；', ' ', '\t', '\n']
        
        best_start = 0
        for i in range(len(prefix) - 1, -1, -1):
            if prefix[i] in separators:
                best_start = i + 1
                break

        name_prefix = prefix[best_start:]
        name = name_prefix + type_word

        # 剥离动作前缀（循环剥离直到干净）
        changed = True
        while changed:
            changed = False
            name_before = name
            for pattern in self.strip_prefixes:
                name = re.sub(pattern, '', name).strip()
                if name != name_before:
                    changed = True

        # 去掉"的"字、"将"字
        name = name.lstrip("将").rstrip("的")

        # 清理开头标点和空格
        name = re.sub(r'^[^\w\u4e00-\u9fa5《"]+', '', name)

        # 处理书名号：《XXX方案》→ 提取书名号内容
        if '《' in name and '》' in name:
            book_match = re.search(r'《(.+?)》', name)
            if book_match:
                return book_match.group(1)
        elif '《' in name and '》' not in name:
            # 未闭合的书名号：取《之后的内容
            idx = name.find('《')
            candidate = name[idx + 1:]
            if len(candidate) >= 4:
                return candidate.rstrip("的》")

        # 剥离后缀动作
        for pattern in self.strip_suffixes:
            name = re.sub(pattern, '', name).strip()

        # 清理结尾标点
        name = re.sub(r'[，、。；：\s）)]+$', '', name)

        # 清理不完整的括号（如"各县区（清单" → 去掉"（清单"）
        name = re.sub(r'[（(][^）)]*$', '', name)
        name = name.rstrip('（(')

        # 如果剥离后只剩资料类型词，说明原文是纯动作描述
        bare_types = {"图纸", "方案", "报告", "设计", "规范", "标准", "模型", "PPT", "系统", "平台",
                      "台账", "清单", "数据库", "统计表", "施工图", "初步设计", "规划图"}
        if name in bare_types:
            return None

        # 过滤"动作+资料类型"组合（如"汇报会议"、"巡查数据清单"）
        for pattern in self.action_material_combos:
            if re.search(pattern, name):
                return None

        return name if name else None

    def has_specific_identifier(self, name: str) -> bool:
        """检查资料名是否包含具体标识符"""
        for pattern in self.specific_patterns:
            if re.search(pattern, name):
                return True
        return False

    def find_materials_in_text(self, text: str) -> List[Dict]:
        """从一段文本中找出所有资料名称"""
        results = []

        for type_word in self.material_type_words:
            # 找到所有出现位置
            for match in re.finditer(re.escape(type_word), text):
                pos = match.start()
                name = self.extract_material_name(text, type_word, pos)

                if not name or len(name) < 6:
                    continue

                # 必须有具体标识符
                if not self.has_specific_identifier(name):
                    continue

                # 去重：同一类型词的同一位置不重复
                category = self.type_category_map.get(type_word, "文档类")

                results.append({
                    "name": name[:60],  # 限制长度
                    "category": category,
                    "type_word": type_word,
                })

        return results

    def analyze_report(self, report: Dict) -> List[Dict]:
        """分析单份日报"""
        contents = report.get("contents", [])

        # 处理日期
        create_time = report.get("create_time", "")
        if isinstance(create_time, (int, float)):
            date_str = datetime.fromtimestamp(create_time / 1000).strftime("%Y-%m-%d")
        elif isinstance(create_time, str):
            date_str = create_time[:10]
        else:
            date_str = ""

        employee = report.get("creator_name", report.get("user_name", "未知"))
        department = report.get("dept_name", report.get("department", "未知"))

        # 合并文本
        all_text = []
        for item in contents:
            value = item.get("value", "")
            if value and value not in ["null", "无"]:
                all_text.append(value)
        full_text = "\n".join(all_text)

        # 提取资料
        found = self.find_materials_in_text(full_text)

        materials = []
        seen_names = set()  # 同一份日报内去重

        for f in found:
            if f["name"] in seen_names:
                continue
            seen_names.add(f["name"])

            status = self.detect_status(full_text)

            materials.append({
                "name": f["name"],
                "category": f["category"],
                "status": status,
                "employee": employee,
                "department": department,
                "date": date_str,
            })

        return materials

    def extract_from_reports(self, reports: List[Dict]) -> Dict:
        """从所有日报中提取资料目录"""
        all_materials = []
        for report in reports:
            materials = self.analyze_report(report)
            all_materials.extend(materials)

        deduplicated = self.deduplicate(all_materials)
        categorized = self.categorize(deduplicated)

        return {
            "total_count": len(deduplicated),
            "materials": deduplicated,
            "categorized": categorized,
            "employee_summary": self.summarize_by_employee(deduplicated),
            "department_summary": self.summarize_by_department(deduplicated),
        }

    def deduplicate(self, materials: List[Dict]) -> List[Dict]:
        """去重（支持模糊匹配合并相似条目）"""
        seen: Dict[str, Dict] = {}
        for m in materials:
            key = m["name"]
            # 模糊去重：如果一个名称是另一个的子串，合并
            merged = False
            for existing_key in list(seen.keys()):
                if key in existing_key or existing_key in key:
                    # 保留更长的名称（更完整）
                    if len(key) > len(existing_key):
                        seen[key] = seen.pop(existing_key)
                        existing_key = key
                    # 合并员工
                    if m["employee"] not in seen[existing_key]["employees"]:
                        seen[existing_key]["employees"].append(m["employee"])
                    if m["date"] > seen[existing_key]["date"]:
                        seen[existing_key]["date"] = m["date"]
                    merged = True
                    break

            if not merged:
                seen[key] = {
                    "name": m["name"],
                    "category": m["category"],
                    "status": m["status"],
                    "date": m["date"],
                    "employees": [m["employee"]],
                    "department": m["department"],
                }
        return list(seen.values())

    def categorize(self, materials: List[Dict]) -> Dict:
        """按分类组织"""
        categorized = defaultdict(list)
        for m in materials:
            categorized[m["category"]].append(m)
        return dict(sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True))

    def summarize_by_employee(self, materials: List[Dict]) -> List[Dict]:
        """按员工汇总"""
        emp_map: Dict[str, Dict] = {}
        for m in materials:
            for emp in m["employees"]:
                if emp not in emp_map:
                    emp_map[emp] = {"employee": emp, "department": m["department"],
                                   "material_count": 0, "materials": []}
                emp_map[emp]["material_count"] += 1
                emp_map[emp]["materials"].append(m["name"])
        return sorted(emp_map.values(), key=lambda x: x["material_count"], reverse=True)

    def summarize_by_department(self, materials: List[Dict]) -> List[Dict]:
        """按部门汇总"""
        dept_map: Dict[str, Dict] = {}
        for m in materials:
            dept = m["department"]
            if dept not in dept_map:
                dept_map[dept] = {"department": dept, "material_count": 0,
                                 "employees": set(), "categories": set()}
            dept_map[dept]["material_count"] += 1
            dept_map[dept]["employees"].update(m["employees"])
            dept_map[dept]["categories"].add(m["category"])

        result = []
        for dept in sorted(dept_map.values(), key=lambda x: x["material_count"], reverse=True):
            result.append({
                "department": dept["department"], "material_count": dept["material_count"],
                "employee_count": len(dept["employees"]), "categories": sorted(dept["categories"])
            })
        return result

    def generate_markdown(self, result: Dict, date: str) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# 员工资料目录提取报告 - {date}", "",
            f"> 提取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 资料总数：{result['total_count']}项",
            "", "---", ""
        ]

        # 按分类
        lines.append("## 一、按资料分类")
        lines.append("")
        for cat, mats in result["categorized"].items():
            icon = self.category_icons.get(cat, "📁")
            lines.append(f"### {icon} {cat}（{len(mats)}项）")
            lines.append("")
            lines.append("| 资料名称 | 状态 | 涉及员工 | 所属部门 | 最后更新 |")
            lines.append("|---------|------|---------|---------|---------|")
            for m in sorted(mats, key=lambda x: x["date"], reverse=True):
                emps = ", ".join(m["employees"])
                si = "✅" if m["status"] == "已完成" else "🔄"
                lines.append(f"| {m['name']} | {si} {m['status']} | {emps} | {m['department']} | {m['date']} |")
            lines.append("")

        # 按员工
        if result["employee_summary"]:
            lines.append("## 二、按员工汇总")
            lines.append("")
            lines.append("| 员工 | 部门 | 资料数量 | 资料清单 |")
            lines.append("|------|------|---------|---------|")
            for emp in result["employee_summary"]:
                ms = "、".join(emp["materials"][:5])
                if len(emp["materials"]) > 5:
                    ms += f" 等{len(emp['materials'])}项"
                lines.append(f"| {emp['employee']} | {emp['department']} | {emp['material_count']} | {ms} |")
            lines.append("")

        # 按部门
        if result["department_summary"]:
            lines.append("## 三、按部门汇总")
            lines.append("")
            lines.append("| 部门 | 资料总数 | 涉及人数 | 资料类型 |")
            lines.append("|------|---------|---------|---------|")
            for dept in result["department_summary"]:
                cats = "、".join(dept["categories"])
                lines.append(f"| {dept['department']} | {dept['material_count']} | {dept['employee_count']} | {cats} |")
            lines.append("")

        lines.extend(["---", "", "*报告由 daily-report-analyzer v4 自动生成*"])
        return "\n".join(lines)

    def generate_excel_data(self, result: Dict) -> List[Dict]:
        """生成 Excel 数据"""
        rows = []
        for cat, mats in result["categorized"].items():
            for m in sorted(mats, key=lambda x: x["date"], reverse=True):
                rows.append({
                    "资料分类": cat, "资料名称": m["name"], "状态": m["status"],
                    "涉及员工": ", ".join(m["employees"]), "所属部门": m["department"],
                    "最后更新日期": m["date"]
                })
        return rows


def load_reports(input_dir: Path) -> List[Dict]:
    """加载日报数据"""
    for fn in ["reports.json", "raw_reports.json"]:
        candidate = input_dir / fn
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
            reports = data if isinstance(data, list) else data.get("reports", [])
            print(f"[INFO] 从 {fn} 加载到 {len(reports)} 份日报")
            return reports
    print(f"[ERROR] 未找到日报数据: {input_dir}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="从日报中提取资料目录")
    parser.add_argument("--date", default="today")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", default="all", choices=["markdown", "excel", "all"])
    args = parser.parse_args()

    if args.date == "today":
        date_str = datetime.now().strftime("%Y-%m-%d")
    elif args.date == "yesterday":
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date_str = args.date

    input_dir = Path(args.input) if args.input else Path(DEFAULT_REPORTS_DIR) / date_str
    output_dir = Path(args.output) if args.output else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'#'*60}")
    print(f"# 资料目录提取 v4")
    print(f"# 日期: {date_str}")
    print(f"{'#'*60}\n")

    reports = load_reports(input_dir)
    extractor = MaterialExtractor()
    result = extractor.extract_from_reports(reports)

    print(f"[INFO] 共提取到 {result['total_count']} 项资料")

    if args.format in ["markdown", "all"]:
        md = extractor.generate_markdown(result, date_str)
        md_file = output_dir / "materials-catalog.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[OK] Markdown: {md_file}")

    if args.format in ["excel", "all"]:
        try:
            import pandas as pd
            df = pd.DataFrame(extractor.generate_excel_data(result))
            df.to_excel(output_dir / "materials-catalog.xlsx", index=False, engine="openpyxl")
            print(f"[OK] Excel: {output_dir / 'materials-catalog.xlsx'}")
        except ImportError:
            print("[WARN] 未安装 pandas/openpyxl，跳过Excel")

    print("[INFO] 完成")


if __name__ == "__main__":
    main()
