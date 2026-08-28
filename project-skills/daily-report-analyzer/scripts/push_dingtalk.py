#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉推送脚本
将分析结果推送到钉钉日程/待办
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# API配置
DINGTALK_BASE_URL = "https://oapi.dingtalk.com"
TOKEN_EXPIRE_BUFFER = 200


class DingTalkPusher:
    """钉钉推送客户端"""
    
    def __init__(self, app_key: str, app_secret: str, agent_id: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.agent_id = agent_id
        self.base_url = DINGTALK_BASE_URL
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """获取access_token"""
        if not force_refresh and self._access_token and time.time() < self._token_expire_time:
            return self._access_token
        
        url = f"{self.base_url}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("errcode") != 0:
            raise Exception(f"获取token失败: {data.get('errmsg')}")
        
        self._access_token = data["access_token"]
        self._token_expire_time = time.time() + data.get("expires_in", 7200) - TOKEN_EXPIRE_BUFFER
        
        return self._access_token
    
    def create_calendar_event(
        self,
        summary: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 60,
        attendees: Optional[List[str]] = None,
        location: str = ""
    ) -> Dict[str, Any]:
        """
        创建钉钉日程
        
        Args:
            summary: 日程标题
            description: 日程描述
            start_time: 开始时间
            duration_minutes: 持续时间（分钟）
            attendees: 参与者userId列表
            location: 地点
            
        Returns:
            API响应
        """
        token = self.get_access_token()
        
        # 构建event对象
        start_timestamp = int(start_time.timestamp())
        end_timestamp = start_timestamp + duration_minutes * 60
        
        event = {
            "summary": summary,
            "description": description,
            "calendar_id": "primary",
            "notification_type": "NONE",
            "start": {
                "timezone": "Asia/Shanghai",
                "timestamp": str(start_timestamp)
            },
            "end": {
                "timezone": "Asia/Shanghai",
                "timestamp": str(end_timestamp)
            }
        }
        
        if location:
            event["location"] = {"place": location}
        
        if attendees:
            event["attendees"] = [{"userid": uid} for uid in attendees[:100]]  # 最多100人
            event["organizer"] = {"userid": attendees[0]}
        
        # 提醒设置
        event["reminder"] = {
            "method": "app",
            "minutes": "15"
        }
        
        # 调用API
        url = f"{self.base_url}/topapi/calendar/v2/event/create"
        params = {"access_token": token}
        payload = {
            "agentid": self.agent_id,
            "event": event
        }
        
        response = requests.post(url, params=params, json=payload, timeout=30)
        result = response.json()
        
        if result.get("errcode") != 0:
            raise Exception(f"创建日程失败: {result.get('errmsg')}")
        
        print(f"[INFO] 日程创建成功: {summary}")
        return result
    
    def send_work_notification(
        self,
        user_ids: List[str],
        msg: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送工作通知消息
        
        Args:
            user_ids: 接收者userId列表
            msg: 消息内容
            
        Returns:
            API响应
        """
        token = self.get_access_token()
        
        url = f"{self.base_url}/topapi/message/corpconversation/asyncsend_v2"
        params = {"access_token": token}
        payload = {
            "agent_id": self.agent_id,
            "userid_list": user_ids,
            "msg": msg
        }
        
        response = requests.post(url, params=params, json=payload, timeout=30)
        result = response.json()
        
        if result.get("errcode") != 0:
            raise Exception(f"发送消息失败: {result.get('errmsg')}")
        
        print(f"[INFO] 消息发送成功，接收人数: {len(user_ids)}")
        return result


def format_report_summary(analysis: Dict) -> str:
    """格式化报告摘要为日程描述"""
    lines = [
        f"📊 日报分析报告 - {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"📈 整体情况",
        f"• 提交人数: {analysis['total_count']}人",
        f"• 平均得分: {analysis['avg_score']}分",
        "",
        "📊 分数分布:"
    ]
    
    dist = analysis.get("score_distribution", {})
    levels = {
        "excellent": "优秀(4.5+)",
        "good": "良好(3.5-4.4)",
        "average": "一般(2.5-3.4)",
        "poor": "较差(1.5-2.4)",
        "bad": "差(0-1.4)"
    }
    
    for key, label in levels.items():
        count = dist.get(key, 0)
        lines.append(f"  • {label}: {count}人")
    
    # 有价值信息
    valuable = analysis.get("valuable_info", {})
    lines.extend([
        "",
        "💎 有价值信息:",
        f"  • 项目产出: {len(valuable.get('project_outputs', []))}条",
        f"  • 数据资源: {len(valuable.get('data_resources', []))}条",
        f"  • 风险预警: {len(valuable.get('risk_warnings', []))}条"
    ])
    
    # 风险预警详情
    risks = valuable.get("risk_warnings", [])
    if risks:
        lines.extend(["", "⚠️ 风险预警:"])
        for risk in risks[:3]:  # 最多显示3条
            lines.append(f"  • {risk.get('creator', '')}: {risk.get('content', '')[:30]}...")
    
    lines.append("")
    lines.append("---")
    lines.append("本报告由AI自动分析生成")
    
    return "\n".join(lines)


def push_daily_summary(
    pusher: DingTalkPusher,
    analysis: Dict,
    notify_users: Optional[List[str]] = None,
    create_event: bool = True
):
    """
    推送日报摘要
    
    Args:
        pusher: 推送客户端
        analysis: 分析结果
        notify_users: 通知的用户列表
        create_event: 是否创建日程
    """
    summary = format_report_summary(analysis)
    
    # 创建日程（明天早上提醒）
    if create_event:
        tomorrow_morning = datetime.now().replace(
            hour=9, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        
        try:
            pusher.create_calendar_event(
                summary=f"📋 日报分析报告 - {datetime.now().strftime('%Y-%m-%d')}",
                description=summary,
                start_time=tomorrow_morning,
                duration_minutes=30,
                attendees=notify_users,
                location="线上"
            )
        except Exception as e:
            print(f"[WARN] 创建日程失败: {e}")
    
    # 发送工作通知
    if notify_users:
        try:
            msg = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"日报分析报告 - {datetime.now().strftime('%Y-%m-%d')}",
                    "text": summary
                }
            }
            pusher.send_work_notification(notify_users, msg)
        except Exception as e:
            print(f"[WARN] 发送消息失败: {e}")


def get_config() -> Dict[str, str]:
    """获取配置"""
    app_key = os.environ.get("DINGTALK_APP_KEY")
    app_secret = os.environ.get("DINGTALK_APP_SECRET")
    agent_id = os.environ.get("DINGTALK_AGENT_ID")
    
    if app_key and app_secret and agent_id:
        return {
            "app_key": app_key,
            "app_secret": app_secret,
            "agent_id": agent_id
        }
    
    config_path = Path.home() / ".dingtalk" / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return {
                "app_key": config.get("app_key"),
                "app_secret": config.get("app_secret"),
                "agent_id": config.get("agent_id")
            }
    
    raise Exception(
        "未找到钉钉配置。请设置环境变量 DINGTALK_APP_KEY、DINGTALK_APP_SECRET、DINGTALK_AGENT_ID，"
        "或创建配置文件 ~/.dingtalk/config.json"
    )


def main():
    parser = argparse.ArgumentParser(description="钉钉推送工具")
    parser.add_argument(
        "--date",
        default="today",
        help="目标日期"
    )
    parser.add_argument(
        "--input",
        default="reports",
        help="输入目录"
    )
    parser.add_argument(
        "--users",
        help="通知用户ID列表，逗号分隔"
    )
    parser.add_argument(
        "--no-event",
        action="store_true",
        help="不创建日程"
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
        
        # 读取分析结果
        input_dir = Path(args.input)
        analysis_file = input_dir / date_str / "analysis.json"
        
        if not analysis_file.exists():
            print(f"[ERROR] 未找到分析结果文件: {analysis_file}")
            sys.exit(1)
        
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        
        # 获取配置
        config = get_config()
        
        # 解析用户列表
        notify_users = None
        if args.users:
            notify_users = [u.strip() for u in args.users.split(",") if u.strip()]
        
        # 创建推送器
        pusher = DingTalkPusher(
            app_key=config["app_key"],
            app_secret=config["app_secret"],
            agent_id=config["agent_id"]
        )
        
        # 推送
        push_daily_summary(
            pusher=pusher,
            analysis=analysis,
            notify_users=notify_users,
            create_event=not args.no_event
        )
        
        print("\n[SUCCESS] 推送完成！")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()