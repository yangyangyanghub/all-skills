#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日报分析评分脚本（增强版）
对获取的日报数据进行智能分析和评分
新增：日报完成率、审批效率、流水账检测、AI工具应用分析
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# 默认目录（工作空间根目录）
DEFAULT_REPORTS_DIR = str(Path(__file__).parent.parent.parent.parent / "daily-reports")


class ReportAnalyzer:
    """日报分析器（增强版）"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化分析器
        
        Args:
            config_path: 配置文件路径
        """
        # 评分权重（AI工具权重提高到20%）
        self.weights = {
            "completeness": 0.20,      # 完整度
            "content_quality": 0.25,   # 内容质量（新增：含流水账检测）
            "ai_application": 0.20,    # AI工具应用（权重提高）
            "timeliness": 0.15,        # 及时性
            "workload": 0.10,          # 工作量
            "planning": 0.10           # 计划性（新增）
        }
        
        # 流水账特征词（只有项目名没有具体工作）
        self.lazy_patterns = [
            r'^[\u4e00-\u9fa5]{2,8}$',  # 只有2-8个汉字
            r'^.{1,10}$',               # 总共少于10个字
        ]
        
        # 流水账关键词（只有项目名/工作名，没有具体描述）
        self.lazy_keywords = [
            "施工图", "方案", "设计", "修改", "调整", "整理", "对接",
            "审核", "审批", "报告", "规划", "调研", "测量", "测绘"
        ]
        
        # AI工具关键词
        self.ai_keywords = [
            "ai", "AI", "豆包", "deepseek", "DeepSeek", "kimi", "Kimi",
            "chatgpt", "ChatGPT", "文心", "通义", "讯飞", "智谱",
            "建筑学长", "灵感渲染", "AI工具", "ai填写", "用ai"
        ]
        
        # 积极词汇
        self.positive_words = [
            "完成", "上线", "交付", "解决", "优化", "突破", "实现", "达成", "成功",
            "改进", "提升", "完善", "稳定", "高效", "圆满"
        ]
        
        # 项目相关词
        self.project_words = [
            "项目", "版本", "迭代", "需求", "功能", "模块", "系统",
            "平台", "服务", "组件", "接口", "工程"
        ]
        
        # 加载自定义配置
        if config_path and config_path.exists():
            self._load_config(config_path)
    
    def _load_config(self, config_path: Path):
        """加载配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "weights" in config:
                    self.weights.update(config["weights"])
                if "dept_member_count" in config:
                    self.dept_member_count = config["dept_member_count"]
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARN] 加载配置文件失败: {e}")
    
    def analyze_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单条日报（增强版）
        
        Args:
            report: 日报数据
            
        Returns:
            分析结果
        """
        contents = report.get("contents", [])
        raw_content = self._extract_raw_content(contents)
        
        # 提取各字段内容
        work_done = self._get_field_value(contents, "今日完成工作")
        ai_usage = self._get_field_value(contents, "AI工具应用情况")
        work_review = self._get_field_value(contents, "今日工作复盘")
        tomorrow_plan = self._get_field_value(contents, "明日重点计划")
        support_needed = self._get_field_value(contents, "需协调支持事项")
        
        # 评分（增强版）
        scores = {
            "completeness": self._score_completeness(report, work_done, work_review, tomorrow_plan),
            "content_quality": self._score_content_quality(work_done),
            "ai_application": self._score_ai_application(ai_usage),
            "timeliness": self._score_timeliness(report),
            "workload": self._score_workload(raw_content),
            "planning": self._score_planning(tomorrow_plan, support_needed)
        }
        
        # 计算综合分
        total_score = sum(scores[k] * self.weights.get(k, 0.15) for k in scores)
        scores["total"] = round(total_score, 2)
        
        # 流水账检测
        is_lazy, lazy_reason = self._detect_lazy_report(work_done)
        
        # 提取有价值信息
        valuable_info = self._extract_valuable_info(report, raw_content)
        
        return {
            "report_id": report.get("report_id"),
            "creator_id": report.get("creator_id"),
            "creator_name": report.get("creator_name"),
            "dept_name": report.get("dept_name"),
            "create_time": report.get("create_time"),
            "scores": scores,
            "is_lazy_report": is_lazy,
            "lazy_reason": lazy_reason,
            "ai_usage": self._get_valid_ai_usage(ai_usage),
            "valuable_info": valuable_info,
            "content_length": len(raw_content),
            "word_count": len(raw_content.split()),
            "work_done_length": len(work_done) if work_done else 0,
            "has_review": bool(work_review and work_review not in ["null", "无"]),
            "has_plan": bool(tomorrow_plan and tomorrow_plan not in ["null", "无"])
        }
    
    def _get_field_value(self, contents: List[Dict], field_name: str) -> str:
        """获取指定字段的值"""
        for item in contents:
            if item.get("key") == field_name:
                return item.get("value", "") or ""
        return ""
    
    def _get_valid_ai_usage(self, ai_usage: str) -> Optional[str]:
        """
        获取有效的AI应用描述（用于报告展示）
        只返回有实际价值的AI应用案例
        """
        if not ai_usage or ai_usage == "null":
            return None
        
        # 无效的填充词（精确匹配）
        no_use_exact = [
            "无", "暂无", "今日未使用", "未使用AI工具", "今日无应用",
            "今日工作无ai", "未使用", "今日无", "无应用", "wu", "无。",
            "今日工作无", "无AI相关", "今日工作无ai相关内容"
        ]
        
        if ai_usage.strip() in no_use_exact:
            return None
        
        # 检查是否包含表示未使用AI的关键词（模糊匹配）
        no_use_keywords = [
            "故未使用AI", "未使用AI", "无AI相关", "无ai相关",
            "今日无应用", "今日工作无", "无应用", "未使用"
        ]
        for kw in no_use_keywords:
            if kw in ai_usage:
                return None
        
        # 检查是否提到AI工具
        ai_used = any(keyword.lower() in ai_usage.lower() for keyword in self.ai_keywords)
        if not ai_used:
            return None
        
        # 检查是否有具体应用场景
        high_value_patterns = [
            "辅助", "协助", "解决", "生成", "开发", "分析", "处理", "完成",
            "查找", "搜索", "计算", "编写", "设计", "优化", "梳理",
            "学习", "查阅", "查询", "探索", "转换", "渲染"
        ]
        
        work_patterns = [
            "接口", "代码", "规范", "文档", "数据", "报告", "方案", "表格",
            "图纸", "效果图", "程序", "系统", "标准", "参数", "问题",
            "开发", "设计", "计算", "表格", "资料"
        ]
        
        has_value = any(p in ai_usage for p in high_value_patterns)
        has_work = any(p in ai_usage for p in work_patterns)
        
        # 有具体应用才返回
        if has_value or has_work or len(ai_usage) > 15:
            return ai_usage
        
        return None
    def _extract_raw_content(self, contents: List[Dict]) -> str:
        """提取原始内容文本"""
        text_parts = []
        for item in contents:
            key = item.get("key", "")
            value = item.get("value", "")
            if value and value != "null":
                text_parts.append(f"{key}: {value}")
        return " ".join(text_parts)
    
    def _score_completeness(self, report: Dict, work_done: str, work_review: str, tomorrow_plan: str) -> int:
        """
        评分：完整度（增强版）
        
        规则：
        - 5分: 工作内容+复盘+明日计划都完整
        - 4分: 工作内容+复盘或明日计划完整
        - 3分: 仅工作内容完整
        - 2分: 工作内容简单
        - 1分: 工作内容缺失或敷衍
        """
        has_work = bool(work_done and len(work_done) > 10)
        has_review = bool(work_review and work_review not in ["null", "无", ""])
        has_plan = bool(tomorrow_plan and tomorrow_plan not in ["null", "无", ""])
        
        # 检查工作内容质量
        work_quality = 0
        if work_done:
            if len(work_done) > 100:
                work_quality = 3
            elif len(work_done) > 50:
                work_quality = 2
            elif len(work_done) > 20:
                work_quality = 1
        
        if has_work and has_review and has_plan:
            return min(5, work_quality + 2)
        elif has_work and (has_review or has_plan):
            return min(4, work_quality + 1)
        elif has_work:
            return min(3, work_quality)
        elif work_done:
            return 2
        else:
            return 1
    
    def _score_content_quality(self, work_done: str) -> int:
        """
        评分：内容质量（新增）
        
        规则：
        - 5分: 内容详实，有具体工作描述+量化数据
        - 4分: 内容丰富，有具体工作描述
        - 3分: 内容一般，有基本工作描述
        - 2分: 内容简单，可能流水账
        - 1分: 流水账式记录
        """
        if not work_done or work_done == "null":
            return 1
        
        # 检查是否有量化数据
        has_numbers = bool(re.search(r'\d+[%％个条项处]', work_done))
        
        # 检查是否有具体动作描述
        action_words = ["完成", "进行", "开展", "实现", "处理", "解决", "修改", "设计", "开发", "整理"]
        has_actions = any(word in work_done for word in action_words)
        
        # 检查是否有具体细节（逗号、分号分隔的多项内容）
        has_details = work_done.count('，') > 1 or work_done.count('、') > 1 or work_done.count('\n') > 0
        
        # 检查内容长度
        length = len(work_done)
        
        if has_numbers and has_actions and length > 100:
            return 5
        elif has_actions and has_details and length > 50:
            return 4
        elif has_actions and length > 30:
            return 3
        elif length > 10:
            return 2
        else:
            return 1
    
    def _score_ai_application(self, ai_usage: str) -> int:
        """
        评分：AI工具应用（权重20%）
        
        评分规则：要体现AI解决了什么具体问题才得高分
        - 5分: 明确使用AI解决具体问题，有详细描述（如"用AI辅助开发XX接口"、"用豆包查找规范解决了XX问题"）
        - 4分: 使用AI，有应用场景但不够具体（如"查找规范"、"辅助设计"）
        - 3分: 只是提到AI工具名称，没有说明具体用途（如"AI豆包应用"、"建筑学长"）
        - 2分: 诚实填写未使用（如"无"、"今日未使用"）
        - 1分: 未填写或填null
        """
        if not ai_usage or ai_usage == "null":
            return 1
        
        # 检查是否实际使用了AI工具
        ai_used = any(keyword.lower() in ai_usage.lower() for keyword in self.ai_keywords)
        
        # 诚实填写未使用的情况
        no_use_patterns = ["无", "暂无", "今日未使用", "未使用AI工具", "今日无应用", 
                          "今日工作无ai", "未使用", "今日无", "无应用", "wu", "无。"]
        if ai_usage.strip() in no_use_patterns or len(ai_usage.strip()) <= 2:
            return 2
        
        if not ai_used:
            # 没有提到AI工具名称，可能是敷衍
            return 2
        
        # ====== 检查是否有具体应用场景 ======
        
        # 高价值应用词：体现AI解决了具体问题
        high_value_patterns = [
            "辅助", "协助", "解决", "生成", "开发", "分析", "处理", "完成",
            "查找", "搜索", "计算", "编写", "设计", "优化", "梳理",
            "学习", "查阅", "查询", "探索", "转换"
        ]
        
        # 具体工作词：体现AI用在什么工作上
        work_patterns = [
            "接口", "代码", "规范", "文档", "数据", "报告", "方案", "表格",
            "图纸", "效果图", "程序", "系统", "标准", "参数", "问题",
            "开发", "设计", "计算", "表格"
        ]
        
        # 敷衍词：只是提了工具名没有具体用途
        lazy_patterns = ["应用", "使用", "工具", "学习"]
        
        # 检查是否有高价值描述
        has_high_value = any(p in ai_usage for p in high_value_patterns)
        has_work = any(p in ai_usage for p in work_patterns)
        
        # 计算有效内容长度（排除无意义的词）
        meaningful_len = len(ai_usage)
        for p in lazy_patterns:
            meaningful_len = ai_usage.count(p) * 2  # 扣除敷衍词的影响
        
        # 评分逻辑
        if has_high_value and has_work:
            # 有具体问题+具体工作 = 5分
            # 例如："使用AI协助生产管理系统curd常用接口开发工作"
            # 例如："豆包搜索文化相关资料"
            # 例如："利用豆包梳理加固手册中关于剪力墙开洞难点条续"
            return 5
        elif has_high_value or (has_work and meaningful_len > 15):
            # 有具体工作或高价值描述 = 4分
            # 例如："查询相关规范标准号"
            # 例如："灵感渲染处理相应的效果图"
            return 4
        elif meaningful_len > 10:
            # 有一些描述但不具体 = 3分
            # 例如："AI豆包应用"
            # 例如："建筑学长灵感"
            return 3
        else:
            # 只是提到工具名 = 2分
            return 2
    def _score_timeliness(self, report: Dict) -> int:
        """
        评分：及时性
        
        规则：
        - 5分: 工作时间内提交 (9:00-18:00)
        - 4分: 下班后2小时内 (18:00-20:00)
        - 3分: 下班后4小时内 (20:00-22:00)
        - 2分: 当日24点前
        - 1分: 次日补交
        """
        create_time = report.get("create_time", 0)
        if not create_time:
            return 3
        
        # 支持字符串格式和毫秒时间戳
        if isinstance(create_time, str):
            try:
                dt = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return 3
        else:
            dt = datetime.fromtimestamp(create_time / 1000)
        hour = dt.hour
        
        if 9 <= hour < 18:
            return 5
        elif 18 <= hour < 20:
            return 4
        elif 20 <= hour < 22:
            return 3
        elif 22 <= hour < 24:
            return 2
        else:
            return 1
    
    def _score_workload(self, content: str) -> int:
        """
        评分：工作量
        """
        length = len(content)
        project_count = sum(1 for word in self.project_words if word in content)
        
        if length > 500 and project_count >= 2:
            return 5
        elif length > 300 and project_count >= 1:
            return 4
        elif length > 100:
            return 3
        elif length > 30:
            return 2
        else:
            return 1
    
    def _score_planning(self, tomorrow_plan: str, support_needed: str) -> int:
        """
        评分：计划性（新增）
        
        规则：
        - 5分: 有明确明日计划+需协调事项
        - 4分: 有明确明日计划
        - 3分: 有简单计划
        - 2分: 未填写计划
        - 1分: 计划敷衍
        """
        has_plan = bool(tomorrow_plan and tomorrow_plan not in ["null", "无", ""])
        has_support = bool(support_needed and support_needed not in ["null", "无", "暂无"])
        
        if has_plan and has_support:
            return 5
        elif has_plan:
            plan_length = len(tomorrow_plan)
            if plan_length > 30:
                return 4
            elif plan_length > 10:
                return 3
            else:
                return 2
        else:
            return 1
    
    def _detect_lazy_report(self, work_done: str) -> tuple:
        """
        检测流水账式日报
        
        Returns:
            (是否流水账, 原因)
        """
        if not work_done or work_done == "null":
            return True, "工作内容为空"
        
        # 检查1：内容过短
        if len(work_done) < 10:
            return True, "工作内容过短（少于10字）"
        
        # 检查2：只有项目名没有具体描述
        # 例如："邯郸道施工图"、"馆陶督导" 这种只有项目名
        lines = work_done.replace('，', '\n').replace('、', '\n').split('\n')
        lazy_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否只有项目名（没有动词）
            has_action = any(word in line for word in ["完成", "进行", "开展", "处理", "修改", "设计", "整理", "对接", "审核"])
            has_detail = len(line) > 15
            
            if not has_action and not has_detail:
                lazy_lines += 1
        
        total_lines = len([l for l in lines if l.strip()])
        if total_lines > 0 and lazy_lines / total_lines > 0.5:
            return True, "多行内容缺少具体工作描述（只写项目名）"
        
        # 检查3：没有具体工作描述
        action_words = ["完成", "进行", "开展", "处理", "修改", "设计", "整理", "对接", "审核", "绘制", "编制", "撰写", "开发"]
        has_any_action = any(word in work_done for word in action_words)
        
        if not has_any_action and len(work_done) < 50:
            return True, "缺少具体工作动作描述"
        
        return False, None
    
    def _extract_valuable_info(self, report: Dict, content: str) -> Dict[str, List]:
        """
        提取有价值信息
        """
        info = {
            "project_outputs": [],
            "data_resources": [],
            "risk_warnings": [],
            "ai_applications": [],
            "suggestions": []
        }
        
        contents = report.get("contents", [])
        ai_usage = self._get_field_value(contents, "AI工具应用情况")
        
        # AI应用情况 - 只提取有实际价值的
        valid_ai = self._get_valid_ai_usage(ai_usage)
        if valid_ai:
            info["ai_applications"].append({
                "content": valid_ai,
                "creator": report.get("creator_name"),
                "dept": report.get("dept_name")
            })
        
        # 项目产出
        work_done = self._get_field_value(contents, "今日完成工作")
        if work_done:
            for word in self.positive_words:
                if word in work_done:
                    info["project_outputs"].append({
                        "content": work_done[:100],
                        "creator": report.get("creator_name")
                    })
                    break
        
        # 风险预警
        risk_words = ["风险", "延期", "阻塞", "问题", "困难", "待解决", "需协调"]
        for word in risk_words:
            if word in content:
                info["risk_warnings"].append({
                    "content": content[:100],
                    "creator": report.get("creator_name"),
                    "dept": report.get("dept_name")
                })
                break
        
        return info
    
    def analyze_all(self, reports: List[Dict], dept_member_count: Dict[str, int] = None) -> Dict[str, Any]:
        """
        分析所有日报（增强版）
        """
        all_results = []
        dept_scores = defaultdict(list)
        dept_ai_usage = defaultdict(lambda: {"used": 0, "total": 0})
        dept_lazy_count = defaultdict(lambda: {"lazy": 0, "total": 0})
        dept_plan_count = defaultdict(lambda: {"has_plan": 0, "total": 0})
        dept_review_count = defaultdict(lambda: {"has_review": 0, "total": 0})
        
        all_valuable_info = {
            "project_outputs": [],
            "data_resources": [],
            "risk_warnings": [],
            "ai_applications": [],
            "suggestions": []
        }
        
        for report in reports:
            # 分析已完成和审批中的日报
            approval_status = report.get("approval", {}).get("status", "")
            if approval_status not in ["COMPLETED", "已结束", "RUNNING", "审批中"]:
                continue
            
            result = self.analyze_report(report)
            all_results.append(result)
            
            dept = report.get("dept_name", "未知部门")
            dept_scores[dept].append(result["scores"]["total"])
            
            # AI使用统计
            dept_ai_usage[dept]["total"] += 1
            if result.get("ai_usage"):
                dept_ai_usage[dept]["used"] += 1
            
            # 流水账统计
            dept_lazy_count[dept]["total"] += 1
            if result.get("is_lazy_report"):
                dept_lazy_count[dept]["lazy"] += 1
            
            # 计划性统计
            dept_plan_count[dept]["total"] += 1
            if result.get("has_plan"):
                dept_plan_count[dept]["has_plan"] += 1
            
            # 复盘统计
            dept_review_count[dept]["total"] += 1
            if result.get("has_review"):
                dept_review_count[dept]["has_review"] += 1
            
            # 汇总有价值信息
            for key, items in result["valuable_info"].items():
                all_valuable_info[key].extend(items)
        
        # 计算整体统计
        total_scores = [r["scores"]["total"] for r in all_results]
        total_ai_used = sum(1 for r in all_results if r.get("ai_usage"))
        total_lazy = sum(1 for r in all_results if r.get("is_lazy_report"))
        total_has_plan = sum(1 for r in all_results if r.get("has_plan"))
        total_has_review = sum(1 for r in all_results if r.get("has_review"))
        
        # 审批效率统计（如果有审批数据）
        approval_stats = self._calculate_approval_stats(reports)
        
        # 日报完成率（如果提供了部门人数配置）
        completion_stats = None
        total_should_submit = len(all_results)  # 默认用已提交人数
        
        if dept_member_count:
            completion_stats = self._calculate_completion_rate(reports, dept_member_count)
            # 计算总应提交人数
            total_should_submit = sum(dept_member_count.values())
            
            # 计算未提交人数（按流水账、无AI、无计划、未复盘统计）
            total_not_submitted = total_should_submit - len(all_results)
            total_lazy += total_not_submitted  # 未提交按流水账
            # 未提交的AI使用、计划、复盘都是0，所以不需要加
        
        # 计算各项率（分母用应提交人数）
        ai_usage_rate = round(total_ai_used / max(total_should_submit, 1) * 100, 1)
        lazy_report_rate = round(total_lazy / max(total_should_submit, 1) * 100, 1)
        plan_rate = round(total_has_plan / max(total_should_submit, 1) * 100, 1)
        review_rate = round(total_has_review / max(total_should_submit, 1) * 100, 1)
        
        # 计算部门统计（增强版，使用部门总人数作为分母）
        # 包含所有部门（含零提交），院部除外
        dept_stats = {}
        
        # 获取所有部门列表（优先从dept_member_count，否则用已提交部门）
        all_depts = set(dept_member_count.keys()) if dept_member_count else set(dept_scores.keys())
        
        for dept in all_depts:
            # 排除"院部"
            if dept == "院部":
                continue
            
            scores = dept_scores.get(dept, [])
            dept_total = dept_member_count.get(dept, len(scores)) if dept_member_count else len(scores)
            submitted = len(scores)
            not_submitted = dept_total - submitted
            
            # 各项统计（未提交的按负面统计）
            ai_used = dept_ai_usage.get(dept, {"used": 0, "total": 0})["used"]
            lazy = dept_lazy_count.get(dept, {"lazy": 0, "total": 0})["lazy"] + not_submitted  # 未提交按流水账
            has_plan = dept_plan_count.get(dept, {"has_plan": 0, "total": 0})["has_plan"]
            has_review = dept_review_count.get(dept, {"has_review": 0, "total": 0})["has_review"]
            
            dept_stats[dept] = {
                "count": submitted,
                "dept_total": dept_total,
                "submission_rate": round(submitted / max(dept_total, 1) * 100, 1),
                "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "ai_usage_rate": round(ai_used / max(dept_total, 1) * 100, 1),
                "lazy_report_rate": round(lazy / max(dept_total, 1) * 100, 1),
                "plan_rate": round(has_plan / max(dept_total, 1) * 100, 1),
                "review_rate": round(has_review / max(dept_total, 1) * 100, 1)
            }
        
        # 合并部门审批完成率到dept_stats
        if approval_stats and approval_stats.get("dept_approval_stats"):
            for dept, ap_stats in approval_stats["dept_approval_stats"].items():
                if dept in dept_stats:
                    dept_stats[dept]["approval_rate"] = ap_stats.get("completion_rate", 0)
        
        return {
            "total_count": len(all_results),
            "total_should_submit": total_should_submit,
            "avg_score": round(sum(total_scores) / len(total_scores), 2) if total_scores else 0,
            "score_distribution": self._calculate_distribution(total_scores),
            "ai_usage_rate": ai_usage_rate,
            "lazy_report_rate": lazy_report_rate,
            "plan_rate": plan_rate,
            "review_rate": review_rate,
            "dept_stats": dept_stats,
            "completion_stats": completion_stats,
            "approval_stats": approval_stats,
            "valuable_info": all_valuable_info,
            "lazy_reports": [r for r in all_results if r.get("is_lazy_report")],
            "details": all_results
        }
    
    def _calculate_approval_stats(self, reports: List[Dict]) -> Optional[Dict]:
        """
        计算审批效率统计
        
        Args:
            reports: 日报列表（需包含approval字段）
            
        Returns:
            审批效率统计，如果数据中没有审批信息则返回None
        """
        # 检查是否有审批数据
        has_approval = any(r.get("approval") for r in reports)
        if not has_approval:
            return None
        
        total = len(reports)
        completed = 0
        in_progress = 0
        
        total_duration = 0
        total_first_delay = 0
        
        dept_approval = defaultdict(lambda: {
            "total": 0,
            "completed": 0,
            "total_duration": 0,
            "total_first_delay": 0
        })
        
        approver_stats = defaultdict(lambda: {"approved_count": 0})
        
        for report in reports:
            approval = report.get("approval", {})
            if not approval:
                continue
            
            dept = report.get("dept_name", "未知部门")
            status = approval.get("status", "")
            efficiency = approval.get("efficiency", {})
            
            dept_approval[dept]["total"] += 1
            
            # 支持中文和英文状态
            if status in ["COMPLETED", "已结束"]:
                completed += 1
                dept_approval[dept]["completed"] += 1
                
                # 支持多种字段名
                duration = efficiency.get("total_duration_hours") or efficiency.get("total_duration", 0)
                first_delay = efficiency.get("first_approve_delay_hours") or efficiency.get("first_approve_delay", 0)
                
                if duration > 0:
                    total_duration += duration
                    dept_approval[dept]["total_duration"] += duration
                if first_delay > 0:
                    total_first_delay += first_delay
                    dept_approval[dept]["total_first_delay"] += first_delay
                    
            elif status in ["RUNNING", "NEW", "审批中"]:
                in_progress += 1
            
            # 统计审批人（从nodes中统计）
            for record in approval.get("nodes", []):
                role = record.get("role", "")
                action = record.get("action", "")
                # 支持中文和英文
                if role in ["部门主管", "主管"] and action in ["同意", "AGREE"]:
                    approver = record.get("approver", "")
                    if approver:
                        approver_stats[approver]["approved_count"] += 1
        
        # 计算部门平均耗时
        dept_stats = {}
        for dept, stats in dept_approval.items():
            avg_duration = round(stats["total_duration"] / stats["completed"], 2) if stats["completed"] > 0 else 0
            avg_first_delay = round(stats["total_first_delay"] / stats["completed"], 2) if stats["completed"] > 0 else 0
            dept_stats[dept] = {
                "total": stats["total"],
                "completed": stats["completed"],
                "completion_rate": round(stats["completed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
                "avg_duration_hours": avg_duration,
                "avg_first_delay_hours": avg_first_delay
            }
        
        return {
            "total_reports": total,
            "completed_count": completed,
            "in_progress_count": in_progress,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "avg_total_duration_hours": round(total_duration / completed, 2) if completed > 0 else 0,
            "avg_first_approve_delay_hours": round(total_first_delay / completed, 2) if completed > 0 else 0,
            "dept_approval_stats": dept_stats,
            "approver_stats": dict(approver_stats)
        }
    def _calculate_completion_rate(self, reports: List[Dict], dept_member_count: Dict[str, int]) -> Dict:
        """计算日报完成率"""
        dept_submitted = defaultdict(int)
        for report in reports:
            dept = report.get("dept_name", "未知部门")
            dept_submitted[dept] += 1
        
        completion = {}
        total_should = 0
        total_submitted = 0
        
        for dept, should_count in dept_member_count.items():
            submitted = dept_submitted.get(dept, 0)
            rate = round(submitted / should_count * 100, 1) if should_count > 0 else 0
            completion[dept] = {
                "should_submit": should_count,
                "submitted": submitted,
                "rate": rate
            }
            total_should += should_count
            total_submitted += submitted
        
        completion["总览"] = {
            "should_submit": total_should,
            "submitted": total_submitted,
            "rate": round(total_submitted / total_should * 100, 1) if total_should > 0 else 0
        }
        
        return completion
    
    def _calculate_distribution(self, scores: List[float]) -> Dict[str, int]:
        """计算分数分布"""
        distribution = {
            "excellent": 0,
            "good": 0,
            "average": 0,
            "poor": 0,
            "bad": 0
        }
        
        for score in scores:
            if score >= 4.5:
                distribution["excellent"] += 1
            elif score >= 3.5:
                distribution["good"] += 1
            elif score >= 2.5:
                distribution["average"] += 1
            elif score >= 1.5:
                distribution["poor"] += 1
            else:
                distribution["bad"] += 1
        
        return distribution


def generate_scores_file(results: Dict, output_path: Path):
    """生成评分详情文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 评分详情已保存到: {output_path}")


def generate_analysis_file(results: Dict, output_path: Path):
    """生成分析结果文件"""
    analysis = {
        "total_count": results["total_count"],
        "total_should_submit": results.get("total_should_submit", results["total_count"]),
        "avg_score": results["avg_score"],
        "score_distribution": results["score_distribution"],
        "ai_usage_rate": results["ai_usage_rate"],
        "lazy_report_rate": results["lazy_report_rate"],
        "plan_rate": results["plan_rate"],
        "review_rate": results["review_rate"],
        "dept_stats": results["dept_stats"],
        "completion_stats": results.get("completion_stats"),
        "approval_stats": results.get("approval_stats"),
        "valuable_info": results["valuable_info"],
        "lazy_reports_count": len(results.get("lazy_reports", []))
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 分析结果已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="日报分析评分工具（增强版）")
    parser.add_argument(
        "--date",
        default="today",
        help="目标日期，支持 YYYY-MM-DD 或 today/yesterday"
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_REPORTS_DIR,
        help=f"输入目录 (默认: {DEFAULT_REPORTS_DIR})"
    )
    parser.add_argument(
        "--config",
        help="配置文件路径"
    )
    
    args = parser.parse_args()
    
    try:
        # 解析日期
        if args.date == "today":
            date_str = datetime.now().strftime("%Y-%m-%d")
        elif args.date == "yesterday":
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_str = args.date
        
        # 读取日报数据
        input_dir = Path(args.input)
        raw_file = input_dir / date_str / "raw_reports.json"
        
        if not raw_file.exists():
            print(f"[ERROR] 未找到日报数据文件: {raw_file}")
            sys.exit(1)
        
        with open(raw_file, "r", encoding="utf-8") as f:
            reports = json.load(f)
        
        print(f"[INFO] 加载了 {len(reports)} 条日报数据")
        
        # 读取部门人数配置
        dept_member_count = None
        
        # 方式1：从summary.json读取
        summary_file = input_dir / date_str / "summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
                    dept_member_count = summary_data.get("dept_member_count")
                    if dept_member_count:
                        print(f"[INFO] 从summary.json加载部门人数配置: {len(dept_member_count)} 个部门")
            except Exception as e:
                print(f"[WARN] 读取summary.json失败: {e}")
        
        # 方式2：从dept_member_count.json读取（如果方式1没有数据）
        if not dept_member_count:
            dept_config_file = input_dir / "dept_member_count.json"
            if dept_config_file.exists():
                try:
                    with open(dept_config_file, "r", encoding="utf-8") as f:
                        dept_member_count = json.load(f)
                        if dept_member_count:
                            print(f"[INFO] 从dept_member_count.json加载部门人数配置: {len(dept_member_count)} 个部门")
                except Exception as e:
                    print(f"[WARN] 读取dept_member_count.json失败: {e}")
        # 初始化分析器
        config_path = Path(args.config) if args.config else None
        analyzer = ReportAnalyzer(config_path)
        
        # 执行分析
        results = analyzer.analyze_all(reports, dept_member_count)
        
        # 保存结果
        output_dir = input_dir / date_str
        generate_scores_file(results, output_dir / "scores.json")
        generate_analysis_file(results, output_dir / "analysis.json")
        
        # 打印摘要
        print("\n" + "=" * 50)
        print("[日报分析摘要]")
        print("=" * 50)
        print(f"日期: {date_str}")
        print(f"提交人数: {results['total_count']}")
        print(f"平均得分: {results['avg_score']}")
        print(f"\n[核心指标]:")
        print(f"  AI工具使用率: {results['ai_usage_rate']}%")
        print(f"  流水账占比: {results['lazy_report_rate']}%")
        print(f"  明日计划填写率: {results['plan_rate']}%")
        print(f"  工作复盘填写率: {results['review_rate']}%")
        print(f"\n[分数分布]:")
        for level, count in results["score_distribution"].items():
            level_name = {"excellent": "优秀", "good": "良好", "average": "一般", "poor": "较差", "bad": "差"}
            print(f"  - {level_name.get(level, level)}: {count}人")
        print(f"\n[警告] 流水账日报: {len(results.get('lazy_reports', []))}条")
        print(f"\n[有价值信息]:")
        print(f"  - AI应用案例: {len(results['valuable_info']['ai_applications'])}条")
        print(f"  - 项目产出: {len(results['valuable_info']['project_outputs'])}条")
        print(f"  - 风险预警: {len(results['valuable_info']['risk_warnings'])}条")
        print("=" * 50)
        
        print("\n[SUCCESS] 日报分析完成！")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()