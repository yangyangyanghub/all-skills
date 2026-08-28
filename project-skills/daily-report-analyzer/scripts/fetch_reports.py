#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉日报数据获取脚本
从钉钉API获取员工日报数据
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# 默认输出目录
# 默认输出目录（工作空间根目录）
DEFAULT_OUTPUT_DIR = str(Path(__file__).parent.parent.parent.parent / "daily-reports")

# API配置
DINGTALK_BASE_URL = "https://oapi.dingtalk.com"
TOKEN_EXPIRE_BUFFER = 200  # 提前200秒过期


class DingTalkReportClient:
    """钉钉日报API客户端"""
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = DINGTALK_BASE_URL
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取access_token，带缓存
        
        Args:
            force_refresh: 是否强制刷新
            
        Returns:
            access_token字符串
        """
        # 检查缓存是否有效
        if not force_refresh and self._access_token and time.time() < self._token_expire_time:
            return self._access_token
        
        # 请求新token
        url = f"{self.base_url}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") != 0:
                raise Exception(f"获取token失败: {data.get('errmsg', '未知错误')}")
            
            self._access_token = data["access_token"]
            self._token_expire_time = time.time() + data.get("expires_in", 7200) - TOKEN_EXPIRE_BUFFER
            
            print(f"[INFO] 成功获取access_token，有效期至: {datetime.fromtimestamp(self._token_expire_time)}")
            return self._access_token
            
        except requests.RequestException as e:
            raise Exception(f"请求钉钉API失败: {e}")
    
    def get_all_reports(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        template_name: str = "日报",
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取全员日报数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            template_name: 日志模板名称
            max_retries: 最大重试次数
            
        Returns:
            日报数据列表
        """
        token = self.get_access_token()
        
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)
        
        cursor = 0
        all_reports = []
        page = 0
        
        print(f"[INFO] 开始获取日报数据: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        while True:
            for attempt in range(max_retries):
                try:
                    url = f"{self.base_url}/topapi/report/list"
                    params = {"access_token": token}
                    body = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "cursor": cursor,
                        "size": 20,
                        "template_name": template_name
                    }
                    
                    response = requests.post(url, params=params, json=body, timeout=30)
                    data = response.json()
                    
                    # 处理token过期
                    if data.get("errcode") in [40014, 42001]:
                        print(f"[WARN] Token已过期，正在刷新...")
                        token = self.get_access_token(force_refresh=True)
                        continue
                    
                    if data.get("errcode") != 0:
                        raise Exception(f"API返回错误: {data.get('errmsg', '未知错误')}")
                    
                    result = data.get("result", {})
                    reports = result.get("data_list", [])
                    all_reports.extend(reports)
                    page += 1
                    
                    print(f"[INFO] 已获取第{page}页，本页{len(reports)}条，累计{len(all_reports)}条")
                    
                    if not result.get("has_more"):
                        print(f"[INFO] 数据获取完成，共{len(all_reports)}条日报")
                        return all_reports
                    
                    cursor = result.get("next_cursor", 0)
                    break
                    
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"请求失败，已重试{max_retries}次: {e}")
                    print(f"[WARN] 请求失败，第{attempt + 1}次重试...")
                    time.sleep(2 ** attempt)  # 指数退避
        
        return all_reports
    
    def get_report_statistics(self, report_id: str) -> Dict[str, Any]:
        """
        获取日报统计数据（阅读、评论、点赞）
        
        Args:
            report_id: 日志ID
            
        Returns:
            统计数据
        """
        token = self.get_access_token()
        stats = {"read": [], "comment": [], "like": []}
        
        for stat_type, key in [(0, "read"), (1, "comment"), (2, "like")]:
            offset = 0
            all_items = []
            
            while True:
                url = f"{self.base_url}/topapi/report/statistics/listbytype"
                params = {"access_token": token}
                body = {
                    "report_id": report_id,
                    "type": stat_type,
                    "offset": offset,
                    "size": 100
                }
                
                try:
                    response = requests.post(url, params=params, json=body, timeout=10)
                    data = response.json()
                    
                    if data.get("errcode") != 0:
                        break
                    
                    result = data.get("result", {})
                    items = result.get("data_list", [])
                    all_items.extend(items)
                    
                    if len(items) < 100:
                        break
                    offset += 100
                    
                except requests.RequestException:
                    break
            
            stats[key] = all_items
        
        return stats


def get_config() -> Dict[str, str]:
    """
    获取配置信息（从环境变量或配置文件）
    
    Returns:
        包含app_key和app_secret的字典
    """
    # 优先从环境变量获取
    app_key = os.environ.get("DINGTALK_APP_KEY")
    app_secret = os.environ.get("DINGTALK_APP_SECRET")
    
    if app_key and app_secret:
        return {"app_key": app_key, "app_secret": app_secret}
    
    # 尝试从配置文件读取
    config_path = Path.home() / ".dingtalk" / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return {
                    "app_key": config.get("app_key"),
                    "app_secret": config.get("app_secret")
                }
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] 读取配置文件失败: {e}")
    
    raise Exception(
        "未找到钉钉配置信息。请设置环境变量 DINGTALK_APP_KEY 和 DINGTALK_APP_SECRET，"
        "或创建配置文件 ~/.dingtalk/config.json"
    )


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串，支持 "today"、"yesterday" 或 "YYYY-MM-DD"
        
    Returns:
        datetime对象
    """
    if date_str == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"无效的日期格式: {date_str}，请使用 YYYY-MM-DD 格式或 'today'/'yesterday'")


def save_reports(reports: List[Dict], output_dir: Path, date: datetime) -> Path:
    """
    保存日报数据到文件
    
    Args:
        reports: 日报数据列表
        output_dir: 输出目录
        date: 日期
        
    Returns:
        保存的文件路径
    """
    # 创建日期目录
    date_str = date.strftime("%Y-%m-%d")
    date_dir = output_dir / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存原始数据
    output_file = date_dir / "raw_reports.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 数据已保存到: {output_file}")
    return output_file


def generate_summary(reports: List[Dict], output_dir: Path, date: datetime) -> Dict:
    """
    生成数据概要统计
    
    Args:
        reports: 日报数据列表
        output_dir: 输出目录
        date: 日期
        
    Returns:
        统计数据
    """
    # 按部门统计
    dept_stats: Dict[str, int] = {}
    # 按模板统计
    template_stats: Dict[str, int] = {}
    # 提交时间分布
    time_distribution: Dict[str, int] = {
        "morning": 0,    # 6:00-12:00
        "afternoon": 0,  # 12:00-18:00
        "evening": 0,    # 18:00-24:00
        "late": 0        # 0:00-6:00
    }
    
    for report in reports:
        # 部门统计
        dept = report.get("dept_name", "未知部门")
        dept_stats[dept] = dept_stats.get(dept, 0) + 1
        
        # 模板统计
        template = report.get("template_name", "未知模板")
        template_stats[template] = template_stats.get(template, 0) + 1
        
        # 时间分布
        create_time = report.get("create_time", 0)
        if create_time:
            hour = datetime.fromtimestamp(create_time / 1000).hour
            if 6 <= hour < 12:
                time_distribution["morning"] += 1
            elif 12 <= hour < 18:
                time_distribution["afternoon"] += 1
            elif 18 <= hour < 24:
                time_distribution["evening"] += 1
            else:
                time_distribution["late"] += 1
    
    summary = {
        "date": date.strftime("%Y-%m-%d"),
        "total_count": len(reports),
        "dept_stats": dept_stats,
        "template_stats": template_stats,
        "time_distribution": time_distribution,
        "fetch_time": datetime.now().isoformat()
    }
    
    # 保存概要
    date_str = date.strftime("%Y-%m-%d")
    summary_file = output_dir / date_str / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 概要已保存到: {summary_file}")
    
    # 打印统计
    print("\n========== 数据概要 ==========")
    print(f"日期: {date.strftime('%Y-%m-%d')}")
    print(f"总条数: {len(reports)}")
    print("\n部门分布:")
    for dept, count in sorted(dept_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {dept}: {count}条")
    print("\n提交时间分布:")
    print(f"  - 上午(6:00-12:00): {time_distribution['morning']}条")
    print(f"  - 下午(12:00-18:00): {time_distribution['afternoon']}条")
    print(f"  - 晚间(18:00-24:00): {time_distribution['evening']}条")
    print(f"  - 深夜(0:00-6:00): {time_distribution['late']}条")
    print("=" * 30)
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="钉钉日报数据获取工具")
    parser.add_argument(
        "--date", 
        default="today",
        help="目标日期，支持 YYYY-MM-DD 或 today/yesterday (默认: today)"
    )
    parser.add_argument(
        "--template",
        default="日报",
        help="日志模板名称 (默认: 日报)"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    
    try:
        # 获取配置
        config = get_config()
        
        # 解析日期
        target_date = parse_date(args.date)
        end_date = target_date + timedelta(days=1)
        
        # 创建客户端
        client = DingTalkReportClient(
            app_key=config["app_key"],
            app_secret=config["app_secret"]
        )
        
        # 获取日报数据
        reports = client.get_all_reports(
            start_date=target_date,
            end_date=end_date,
            template_name=args.template
        )
        
        if not reports:
            print(f"[WARN] 未获取到 {target_date.strftime('%Y-%m-%d')} 的日报数据")
            return
        
        # 保存数据
        output_dir = Path(args.output)
        save_reports(reports, output_dir, target_date)
        
        # 生成概要
        generate_summary(reports, output_dir, target_date)
        
        print("\n[SUCCESS] 日报数据获取完成！")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()