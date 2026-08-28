#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OA审批日报数据获取脚本（增强版）
从钉钉OA审批获取员工日报数据，包含完整审批流程信息
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

# 默认输出目录（工作空间根目录）
DEFAULT_OUTPUT_DIR = str(Path(__file__).parent.parent.parent.parent / "daily-reports")

# API配置
API_BASE_URL = "https://api.dingtalk.com"  # 新版API
OAPI_BASE_URL = "https://oapi.dingtalk.com"  # 旧版API
TOKEN_EXPIRE_BUFFER = 200


def parse_operation_records(records: List[Dict]) -> List[Dict]:
    """
    解析审批操作记录
    
    API返回格式:
    {
        "userid": "操作人userid",
        "date": "2026-03-12 22:03:40",
        "operation_type": "EXECUTE_TASK_NORMAL",
        "operation_result": "AGREE",
        "remark": "评论内容"
    }
    """
    parsed = []
    operation_type_map = {
        "EXECUTE_TASK_NORMAL": "正常执行",
        "EXECUTE_TASK_AGENT": "代理执行",
        "APPEND_TASK_BEFORE": "前加签",
        "APPEND_TASK_AFTER": "后加签",
        "REDIRECT_TASK": "转交",
        "START_PROCESS_INSTANCE": "发起流程",
        "TERMINATE_PROCESS_INSTANCE": "终止流程",
        "FINISH_PROCESS_INSTANCE": "结束流程",
        "ADD_REMARK": "添加评论",
        "REDIRECT_PROCESS": "审批退回",
        "PROCESS_CC": "抄送"
    }
    
    operation_result_map = {
        "AGREE": "同意",
        "REFUSE": "拒绝",
        "NONE": "无"
    }
    
    for record in records:
        parsed.append({
            "approver_id": record.get("userid", ""),
            "time": record.get("date", ""),
            "operation_type": record.get("operation_type", ""),
            "operation_type_name": operation_type_map.get(record.get("operation_type", ""), record.get("operation_type", "")),
            "result": record.get("operation_result", ""),
            "result_name": operation_result_map.get(record.get("operation_result", ""), record.get("operation_result", "")),
            "remark": record.get("remark", ""),
            "attachments": record.get("attachments", [])
        })
    
    return parsed


def parse_tasks(tasks: List[Dict]) -> List[Dict]:
    """
    解析审批任务列表
    
    API返回格式:
    {
        "userid": "任务处理人",
        "task_status": "COMPLETED",
        "task_result": "AGREE",
        "create_time": "2026-03-12 22:03:40",
        "finish_time": "2026-03-13 09:04:15",
        "taskid": "任务节点ID"
    }
    """
    parsed = []
    task_status_map = {
        "NEW": "未启动",
        "RUNNING": "处理中",
        "PAUSED": "暂停",
        "CANCELED": "取消",
        "COMPLETED": "完成",
        "TERMINATED": "终止"
    }
    
    task_result_map = {
        "AGREE": "同意",
        "REFUSE": "拒绝",
        "REDIRECTED": "转交"
    }
    
    for task in tasks:
        parsed.append({
            "handler_id": task.get("userid", ""),
            "status": task.get("task_status", ""),
            "status_name": task_status_map.get(task.get("task_status", ""), task.get("task_status", "")),
            "result": task.get("task_result", ""),
            "result_name": task_result_map.get(task.get("task_result", ""), task.get("task_result", "")),
            "create_time": task.get("create_time", ""),
            "finish_time": task.get("finish_time", ""),
            "task_id": task.get("taskid", "")
        })
    
    return parsed


def calculate_approval_efficiency(detail: Dict) -> Dict:
    """
    计算审批效率指标
    
    Args:
        detail: 审批实例详情
        
    Returns:
        审批效率指标
    """
    create_time = detail.get("create_time", "")
    finish_time = detail.get("finish_time", "")
    status = detail.get("status", "")
    operation_records = detail.get("operation_records", [])
    tasks = detail.get("tasks", [])
    
    efficiency = {
        "status": status,
        "create_time": create_time,
        "finish_time": finish_time,
        "total_duration_hours": 0,
        "first_approve_delay_hours": 0,
        "approval_nodes": len(operation_records),
        "task_count": len(tasks),
        "is_completed": status == "COMPLETED"
    }
    
    try:
        if create_time:
            create_dt = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
            
            # 计算总耗时
            if finish_time and status == "COMPLETED":
                finish_dt = datetime.strptime(finish_time, "%Y-%m-%d %H:%M:%S")
                efficiency["total_duration_hours"] = round((finish_dt - create_dt).total_seconds() / 3600, 2)
            
            # 计算首次审批延迟（从提交到第一个审批人操作）
            if len(operation_records) >= 2:
                # operation_records[0] 是发起人提交，[1] 是第一个审批
                first_approve_time = operation_records[1].get("date", "")
                if first_approve_time:
                    first_approve_dt = datetime.strptime(first_approve_time, "%Y-%m-%d %H:%M:%S")
                    efficiency["first_approve_delay_hours"] = round((first_approve_dt - create_dt).total_seconds() / 3600, 2)
    
    except Exception as e:
        pass
    
    return efficiency


class DingTalkOAApprovalClient:
    """钉钉OA审批API客户端"""
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.api_base = API_BASE_URL
        self.oapi_base = OAPI_BASE_URL
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0
        self._dept_member_count: Optional[Dict[str, int]] = None
    
    def get_department_list(self) -> List[Dict]:
        """
        获取部门列表
        
        需要权限: qyapi_get_department_list
        
        Returns:
            部门列表
        """
        token = self.get_access_token()
        
        all_depts = []
        
        def get_sub_depts(dept_id: int):
            """递归获取子部门"""
            url = f"{self.oapi_base}/topapi/v2/department/listsub"
            body = {"dept_id": dept_id}
            
            try:
                resp = requests.post(url, params={"access_token": token}, json=body, timeout=10)
                data = resp.json()
                
                if data.get("errcode") == 0:
                    depts = data.get("result", [])
                    for d in depts:
                        all_depts.append({
                            "dept_id": d.get("dept_id"),
                            "name": d.get("name"),
                            "parent_id": d.get("parent_id")
                        })
                        # 递归获取子部门
                        get_sub_depts(d.get("dept_id"))
            except Exception as e:
                print(f"[WARN] 获取部门列表失败: {e}")
        
        # 从根部门开始
        get_sub_depts(1)
        
        print(f"[INFO] 获取到 {len(all_depts)} 个部门")
        return all_depts
    
    def get_department_user_count(self, dept_id: int) -> int:
        """
        获取部门人数
        
        需要权限: qyapi_get_department_member
        
        Args:
            dept_id: 部门ID
            
        Returns:
            部门人数
        """
        token = self.get_access_token()
        
        url = f"{self.oapi_base}/topapi/user/count"
        body = {"only_active": True}
        params = {"access_token": token}
        
        try:
            resp = requests.post(url, params=params, json=body, timeout=10)
            data = resp.json()
            
            if data.get("errcode") == 0:
                return data.get("result", 0)
        except Exception as e:
            print(f"[WARN] 获取部门人数失败: {e}")
        
        return 0
    
    def get_dept_member_counts(self) -> Dict[str, int]:
        """
        获取所有部门的成员数量
        
        Returns:
            {部门名称: 人数}
        """
        if self._dept_member_count is not None:
            return self._dept_member_count
        
        token = self.get_access_token()
        dept_member_count = {}
        
        try:
            # 获取部门列表
            depts = self.get_department_list()
            
            for dept in depts:
                dept_id = dept.get("dept_id")
                dept_name = dept.get("name")
                
                # 获取部门成员数 - 通过list长度计算
                url = f"{self.oapi_base}/topapi/v2/user/list"
                body = {
                    "dept_id": dept_id,
                    "cursor": 0,
                    "size": 100
                }
                
                resp = requests.post(url, params={"access_token": token}, json=body, timeout=10)
                data = resp.json()
                
                if data.get("errcode") == 0:
                    result = data.get("result", {})
                    # 通过list长度获取人数
                    member_list = result.get("list", [])
                    count = len(member_list)
                    
                    # 如果有更多数据，继续获取
                    cursor = result.get("cursor")
                    while result.get("has_more") and cursor:
                        body["cursor"] = cursor
                        resp = requests.post(url, params={"access_token": token}, json=body, timeout=10)
                        data = resp.json()
                        if data.get("errcode") == 0:
                            result = data.get("result", {})
                            member_list = result.get("list", [])
                            count += len(member_list)
                            cursor = result.get("cursor")
                        else:
                            break
                    
                    if count > 0:
                        dept_member_count[dept_name] = count
                
                time.sleep(0.1)  # 避免频率限制
            
            print(f"[INFO] 获取到 {len(dept_member_count)} 个部门的人数")
            
        except Exception as e:
            print(f"[WARN] 获取部门人数失败: {e}")
        
        self._dept_member_count = dept_member_count
        return dept_member_count
    def get_access_token(self, force_refresh: bool = False) -> str:
        """获取access_token"""
        if not force_refresh and self._access_token and time.time() < self._token_expire_time:
            return self._access_token
        
        url = f"{self.oapi_base}/gettoken"
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
        
        print(f"[INFO] 成功获取access_token")
        return self._access_token
    
    def get_process_code(self, template_name: str) -> str:
        """根据模板名称获取processCode"""
        token = self.get_access_token()
        
        # 使用新版API
        url = f"{self.api_base}/v1.0/workflow/processCentres/schemaNames/processCodes"
        headers = {
            "x-acs-dingtalk-access-token": token,
            "Content-Type": "application/json"
        }
        params = {"name": template_name}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if data.get("result") and data["result"].get("processCode"):
            process_code = data["result"]["processCode"]
            print(f"[INFO] 获取到模板 '{template_name}' 的processCode: {process_code}")
            return process_code
        
        # 尝试旧版API
        url = f"{self.oapi_base}/topapi/process/get_by_name"
        params_url = {"access_token": token}
        body = {"name": template_name}
        
        response = requests.post(url, params=params_url, json=body, timeout=10)
        data = response.json()
        
        if data.get("errcode") == 0 and data.get("process_code"):
            return data["process_code"]
        
        raise Exception(f"未找到模板 '{template_name}' 的processCode，请确认模板名称是否正确")
    
    def get_instance_ids(
        self,
        process_code: str,
        start_time: datetime,
        end_time: datetime,
        statuses: List[str] = None,
        user_ids: List[str] = None
    ) -> List[str]:
        """获取审批实例ID列表"""
        token = self.get_access_token()
        
        url = f"{self.api_base}/v1.0/workflow/processes/instanceIds/query"
        headers = {
            "x-acs-dingtalk-access-token": token,
            "Content-Type": "application/json"
        }
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        all_ids = []
        next_token = 0
        page = 0
        
        print(f"[INFO] 开始获取审批实例ID: {start_time.strftime('%Y-%m-%d')} ~ {end_time.strftime('%Y-%m-%d')}")
        
        while True:
            body = {
                "processCode": process_code,
                "startTime": start_timestamp,
                "endTime": end_timestamp,
                "nextToken": next_token,
                "maxResults": 20
            }
            
            if statuses:
                body["statuses"] = statuses
            if user_ids:
                body["userIds"] = user_ids
            
            response = requests.post(url, headers=headers, json=body, timeout=30)
            data = response.json()
            
            if not data.get("success"):
                error_msg = data.get("message", "未知错误")
                raise Exception(f"获取实例ID失败: {error_msg}")
            
            result = data.get("result", {})
            ids = result.get("list", [])
            all_ids.extend(ids)
            page += 1
            
            print(f"[INFO] 已获取第{page}页，本页{len(ids)}条，累计{len(all_ids)}条")
            
            next_token = result.get("nextToken")
            if not next_token:
                break
        
        print(f"[INFO] 实例ID获取完成，共{len(all_ids)}条")
        return all_ids
    
    def get_instance_detail(self, instance_id: str) -> Dict[str, Any]:
        """获取审批实例详情"""
        token = self.get_access_token()
        
        url = f"{self.oapi_base}/topapi/processinstance/get"
        params = {"access_token": token}
        body = {"process_instance_id": instance_id}
        
        response = requests.post(url, params=params, json=body, timeout=30)
        data = response.json()
        
        if data.get("errcode") != 0:
            raise Exception(f"获取实例详情失败: {data.get('errmsg')}")
        
        return data.get("process_instance", {})
    
    def get_all_reports(
        self,
        process_code: str,
        start_date: datetime,
        end_date: datetime,
        statuses: List[str] = None
    ) -> List[Dict[str, Any]]:
        """获取所有日报数据（包含审批信息）"""
        # 获取实例ID列表
        instance_ids = self.get_instance_ids(
            process_code=process_code,
            start_time=start_date,
            end_time=end_date,
            statuses=statuses or ["COMPLETED"]
        )
        
        if not instance_ids:
            print("[WARN] 未找到任何审批实例")
            return []
        
        # 获取每个实例的详情
        all_reports = []
        for i, instance_id in enumerate(instance_ids):
            try:
                detail = self.get_instance_detail(instance_id)
                
                # 解析审批操作记录
                operation_records = parse_operation_records(detail.get("operation_records", []))
                
                # 解析审批任务
                tasks = parse_tasks(detail.get("tasks", []))
                
                # 计算审批效率
                efficiency = calculate_approval_efficiency(detail)
                
                # 提取创建人姓名（从title中提取，格式如"张毅提交的员工日报"）
                title = detail.get("title", "")
                creator_name = title.replace("提交的员工日报", "").strip() if title else detail.get("originator_userid", "")
                
                # 转换为统一格式
                report = {
                    "report_id": instance_id,
                    "creator_id": detail.get("originator_userid"),
                    "creator_name": creator_name,
                    "dept_name": detail.get("originator_dept_name"),
                    "template_name": "员工日报",
                    "create_time": int(datetime.strptime(detail.get("create_time", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S").timestamp() * 1000) if detail.get("create_time") else 0,
                    "contents": [],
                    # 审批信息
                    "approval": {
                        "title": title,
                        "status": detail.get("status"),
                        "result": detail.get("result"),
                        "create_time": detail.get("create_time"),
                        "finish_time": detail.get("finish_time"),
                        "approver_ids": detail.get("approver_userids", []),
                        "cc_ids": detail.get("cc_userids", []),
                        "operation_records": operation_records,
                        "tasks": tasks,
                        "efficiency": efficiency
                    }
                }
                
                # 解析表单数据
                form_values = detail.get("form_component_values", [])
                for fv in form_values:
                    report["contents"].append({
                        "key": fv.get("name", ""),
                        "value": fv.get("value", "")
                    })
                
                all_reports.append(report)
                
                if (i + 1) % 10 == 0:
                    print(f"[INFO] 已处理 {i + 1}/{len(instance_ids)} 条")
                
            except Exception as e:
                print(f"[WARN] 获取实例 {instance_id} 详情失败: {e}")
        
        print(f"[INFO] 日报数据获取完成，共{len(all_reports)}条")
        return all_reports


def get_config() -> Dict[str, str]:
    """获取配置"""
    app_key = os.environ.get("DINGTALK_APP_KEY")
    app_secret = os.environ.get("DINGTALK_APP_SECRET")
    
    if app_key and app_secret:
        return {"app_key": app_key, "app_secret": app_secret}
    
    config_path = Path.home() / ".dingtalk" / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return {
                "app_key": config.get("app_key"),
                "app_secret": config.get("app_secret")
            }
    
    raise Exception(
        "未找到钉钉配置。请设置环境变量 DINGTALK_APP_KEY 和 DINGTALK_APP_SECRET，"
        "或创建配置文件 ~/.dingtalk/config.json"
    )


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    if date_str == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        return datetime.strptime(date_str, "%Y-%m-%d")


def save_reports(reports: List[Dict], output_dir: Path, date: datetime) -> Path:
    """保存日报数据"""
    date_str = date.strftime("%Y-%m-%d")
    date_dir = output_dir / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = date_dir / "raw_reports.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 数据已保存到: {output_file}")
    return output_file


def generate_summary(reports: List[Dict], date: datetime, dept_member_count: Dict[str, int] = None) -> Dict:
    """生成数据概要"""
    total = len(reports)
    completed = sum(1 for r in reports if r.get("approval", {}).get("status") == "COMPLETED")
    
    # 部门统计
    dept_stats = {}
    for r in reports:
        dept = r.get("dept_name", "未知部门")
        if dept not in dept_stats:
            dept_stats[dept] = {"total": 0, "completed": 0}
        dept_stats[dept]["total"] += 1
        if r.get("approval", {}).get("status") == "COMPLETED":
            dept_stats[dept]["completed"] += 1
    
    # 计算部门提交比例
    dept_submission_rate = {}
    if dept_member_count:
        for dept, stats in dept_stats.items():
            dept_total = dept_member_count.get(dept, 0)
            if dept_total > 0:
                rate = round(stats["total"] / dept_total * 100, 1)
                dept_submission_rate[dept] = {
                    "submitted": stats["total"],
                    "dept_total": dept_total,
                    "submission_rate": rate
                }
    
    # 审批效率统计
    efficiencies = [r.get("approval", {}).get("efficiency", {}) for r in reports]
    completed_efficiencies = [e for e in efficiencies if e.get("is_completed")]
    
    avg_total_duration = round(
        sum(e.get("total_duration_hours", 0) for e in completed_efficiencies) / len(completed_efficiencies), 2
    ) if completed_efficiencies else 0
    
    avg_first_delay = round(
        sum(e.get("first_approve_delay_hours", 0) for e in completed_efficiencies) / len(completed_efficiencies), 2
    ) if completed_efficiencies else 0
    
    return {
        "date": date.strftime("%Y-%m-%d"),
        "total_count": total,
        "completed_count": completed,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "avg_approval_duration_hours": avg_total_duration,
        "avg_first_approve_delay_hours": avg_first_delay,
        "dept_stats": dept_stats,
        "dept_member_count": dept_member_count,
        "dept_submission_rate": dept_submission_rate,
        "fetch_time": datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="OA审批日报数据获取工具（增强版）")
    parser.add_argument(
        "--date", 
        default="today",
        help="目标日期，支持 YYYY-MM-DD 或 today/yesterday"
    )
    parser.add_argument(
        "--template",
        default="员工日报",
        help="审批模板名称 (默认: 员工日报)"
    )
    parser.add_argument(
        "--process-code",
        help="审批模板code（可选，不填则根据模板名称自动获取）"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--status",
        default="",
        help="审批状态: RUNNING/TERMINATED/COMPLETED，留空获取全部 (默认: 获取全部状态)"
    )
    parser.add_argument(
        "--fetch-dept-count",
        action="store_true",
        help="获取部门人数（需要额外权限）"
    )
    parser.add_argument(
        "--dept-config",
        help="部门人数配置文件（JSON格式，格式：{\"部门名\": 人数}）"
    )
    
    args = parser.parse_args()
    
    try:
        # 获取配置
        config = get_config()
        
        # 解析日期
        target_date = parse_date(args.date)
        end_date = target_date + timedelta(days=1)
        
        # 创建客户端
        client = DingTalkOAApprovalClient(
            app_key=config["app_key"],
            app_secret=config["app_secret"]
        )
        
        # 获取processCode
        if args.process_code:
            process_code = args.process_code
        else:
            process_code = client.get_process_code(args.template)
        
        # 获取日报数据（默认获取所有状态）
        if args.status:
            statuses = [args.status]
        else:
            statuses = ["RUNNING", "COMPLETED", "TERMINATED"]
        
        reports = client.get_all_reports(
            process_code=process_code,
            start_date=target_date,
            end_date=end_date,
            statuses=statuses
        )
        
        if not reports:
            print(f"[WARN] 未获取到 {target_date.strftime('%Y-%m-%d')} 的日报数据")
            return
        
        # 获取部门人数
        dept_member_count = None
        
        if args.fetch_dept_count:
            print("[INFO] 正在获取部门人数...")
            try:
                dept_member_count = client.get_dept_member_counts()
            except Exception as e:
                print(f"[WARN] 获取部门人数失败: {e}")
                print("[INFO] 可通过 --dept-config 参数手动指定部门人数配置")
        
        if args.dept_config:
            try:
                with open(args.dept_config, "r", encoding="utf-8") as f:
                    dept_member_count = json.load(f)
                print(f"[INFO] 已加载部门人数配置: {len(dept_member_count)} 个部门")
            except Exception as e:
                print(f"[WARN] 加载部门人数配置失败: {e}")
        
        # 保存数据
        output_dir = Path(args.output)
        save_reports(reports, output_dir, target_date)
        
        # 保存概要
        summary = generate_summary(reports, target_date, dept_member_count)
        summary_file = output_dir / target_date.strftime("%Y-%m-%d") / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        print(f"\n{'='*50}")
        print(f"数据获取完成")
        print(f"{'='*50}")
        print(f"总记录数: {summary['total_count']}")
        print(f"已完成: {summary['completed_count']} ({summary['completion_rate']}%)")
        print(f"平均审批耗时: {summary['avg_approval_duration_hours']}小时")
        print(f"平均首审延迟: {summary['avg_first_approve_delay_hours']}小时")
        
        # 打印部门提交比例
        if summary.get('dept_submission_rate'):
            print(f"\n{'='*50}")
            print("部门提交比例:")
            print(f"{'='*50}")
            for dept, rate_info in sorted(summary['dept_submission_rate'].items(), key=lambda x: x[1]['submission_rate'], reverse=True):
                print(f"  {dept}: {rate_info['submitted']}/{rate_info['dept_total']} = {rate_info['submission_rate']}%")
        
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()