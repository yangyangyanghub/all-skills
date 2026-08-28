"""
学术追踪器 —— 推送模块
功能：根据配置推送最新报告到 cc-connect 或 邮件
"""
import os
import smtplib
import subprocess
from email.mime.text import MIMEText
from datetime import datetime

def load_env(path):
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip()
    return env

def push_via_cc(content, env):
    # 通过 cc-connect 执行命令
    # 假设用户已在 OpenCode 环境有 cc-connect
    cmd = f'cc-connect shell run "echo \'{content}\' | cc-connect chat send \'{env.get("CC_SYSTEM_PROMPT", "请发送以下学术简报")}\'"'
    # 更简单的做法是直接用 echo 发送或者调用 API
    # 这里提供一个通用的 cc-connect chat send 模板
    prompt = f"请发送以下学术简报给用户：\n\n{content}"
    subprocess.run(["cc-connect", "chat", "send", prompt], check=False)

def push_via_email(content, env):
    msg = MIMEText(content, 'html', 'utf-8')
    msg['Subject'] = f"📊 学术追踪简报 | {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = env['SMTP_USER']
    msg['To'] = env['TO_EMAIL']

    try:
        smtp = smtplib.SMTP_SSL(env.get('SMTP_SERVER', 'smtp.163.com'), int(env.get('SMTP_PORT', 465)))
        smtp.login(env['SMTP_USER'], env['SMTP_PASS'])
        smtp.sendmail(env['SMTP_USER'], [env['TO_EMAIL']], msg.as_string())
        smtp.quit()
        print("[DONE] Email sent.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

def main():
    env = load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    
    # 找最新报告
    if not os.path.exists(reports_dir):
        print("[INFO] No reports found.")
        return

    report_files = [f for f in os.listdir(reports_dir) if f.startswith('daily') and f.endswith('.md')]
    if not report_files:
        print("[INFO] No daily reports found.")
        return

    latest_report = sorted(report_files)[-1]
    report_path = os.path.join(reports_dir, latest_report)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    method = env.get('PUSH_METHOD', 'console')
    
    if method == 'cc':
        push_via_cc(content, env)
    elif method == 'email':
        push_via_email(content, env)
    else:
        # console 输出
        print("--- PUSHING REPORT TO CONSOLE ---")
        print(content)
        print("-------------------------------")

if __name__ == '__main__':
    main()
