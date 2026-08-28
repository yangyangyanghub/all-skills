#!/usr/bin/env python3
"""SQLite 查询脚本 - 通过 SSH 用 Python 查询本地 .db 文件"""

import json
import sys
import io
import os
import paramiko
from pathlib import Path

# Windows 终端强制使用 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "settings.json"
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_sqlite_query(sql, max_rows=100):
    config = load_config()
    ssh_config = config["ssh"]
    db_path = config["sqlite"]["db_path"]
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        ssh_config["host"],
        port=ssh_config["port"],
        username=ssh_config["username"],
        password=ssh_config.get("password"),
        key_filename=ssh_config.get("key_file"),
        timeout=30
    )
    
    output = ""
    error = ""
    is_meta_cmd = False
    output_and_error = None
    
    try:
        # 处理元命令
        if sql.startswith(".tables"):
            cmd = f'sqlite3 {db_path} ".tables"'
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output, error = stdout.read().decode("utf-8"), stderr.read().decode("utf-8")
            is_meta_cmd = True
        elif sql.startswith(".schema"):
            table = sql.replace(".schema", "").strip()
            if table:
                cmd = f'sqlite3 {db_path} ".schema {table}"'
            else:
                cmd = f'sqlite3 {db_path} ".schema"'
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output, error = stdout.read().decode("utf-8"), stderr.read().decode("utf-8")
            is_meta_cmd = True
        elif sql.startswith("."):
            print(f"不支持的命令: {sql}")
            ssh.close()
            return False
        else:
            # SQL 查询
            if not sql.upper().strip().startswith(("SELECT", "PRAGMA")):
                print("仅支持 SELECT 查询")
                ssh.close()
                return False
            
            if "LIMIT" not in sql.upper():
                sql = f"{sql.rstrip(';')} LIMIT {max_rows}"
            
        # 用 SFTP 写入临时脚本后执行
        sftp = ssh.open_sftp()
        # 在脚本中设置 UTF-8 输出编码，避免中文乱码
        script_content = f'''import sqlite3, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
conn = sqlite3.connect("{db_path}")
conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
cursor = conn.cursor()
cursor.execute("""{sql}""")
rows = cursor.fetchall()
cols = [d[0] for d in cursor.description]
result = [dict(zip(cols, r)) for r in rows]
print(json.dumps(result, ensure_ascii=False, default=str))
conn.close()
'''
        sftp.putfo(io.StringIO(script_content), "/tmp/_sqlite_query.py")
        sftp.close()
        
        # 强制设置远程环境为 UTF-8
        stdin, stdout, stderr = ssh.exec_command("export LC_ALL=en_US.UTF-8; python3 /tmp/_sqlite_query.py; rm -f /tmp/_sqlite_query.py")
        output, error = stdout.read().decode("utf-8"), stderr.read().decode("utf-8")
        
        ssh.close()
        
        if error:
            print(f"执行错误: {error}")
            return False
        
        if is_meta_cmd:
            print(output)
        elif output.strip():
            try:
                results = json.loads(output.strip())
                if isinstance(results, list):
                    print(f"共 {len(results)} 行结果:\n")
                    for i, row in enumerate(results[:max_rows]):
                        print(f"行 {i+1}:")
                        for key, value in row.items():
                            print(f"  {key}: {str(value)[:100]}")
                        print()
                else:
                    print(output)
            except json.JSONDecodeError:
                print(output)
        else:
            print("查询无结果")
        
        return True
        
    except paramiko.AuthenticationException:
        print("SSH 认证失败")
        ssh.close()
        return False
    except Exception as e:
        print(f"查询失败: {e}")
        ssh.close()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python sqlite_query.py 'SQL 查询'")
        print('示例: python sqlite_query.py ".tables"')
        sys.exit(1)
    
    query = sys.argv[1]
    max_rows = 100
    
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "-n" and i + 1 < len(args):
            max_rows = int(args[i + 1])
    
    execute_sqlite_query(query, max_rows=max_rows)
