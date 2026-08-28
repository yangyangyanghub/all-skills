import os, json, time, httpx
from datetime import datetime

def load_env():
    env = {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                if line.strip() and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1); env[k.strip()] = v.strip()
    return env

def call_llm(messages, env):
    url = f"{env['LLM_BASE_URL'].rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {env.get('LLM_API_KEY', 'none')}"}
    payload = {"model": env.get('LLM_MODEL', 'qwen2.5:7b'), "messages": messages, "temperature": 0.3}
    response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def main():
    env = load_env()
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    if not os.path.exists(art_file):
        print("[INFO] No data found."); return

    with open(art_file, 'r', encoding='utf-8') as f: all_data = json.load(f)
    new_items = [a for a in all_data if a.get('is_new')]
    if not new_items: print("[INFO] No new items."); return

    items_str = ""
    for a in new_items:
        src_type = a.get('source', 'Unknown')
        if src_type == 'GitHub':
            items_str += f"[项目] {a['title']} (Stars: {a.get('stars',0)}, Lang: {a.get('language','')})\n简介: {a['summary']}\n链接: {a['link']}\n\n"
        else:
            items_str += f"[论文/文章] {a['title']} (来源: {a.get('repo_name','')}, 引用: {a.get('citationCount',0)})\n摘要: {a['summary'][:300]}\n链接: {a['link']}\n\n"

    topic = env.get('RESEARCH_TOPIC', '地理信息与空间智能')
    prompt = f"""你是一个情报分析专家。请综合分析以下最新发布的内容，筛选出与用户研究方向高度相关的部分。

【用户研究方向】
{topic}

【最新发布】
{items_str}

【任务要求】
1. 给每项内容打分（0-10 分）。
2. 仅保留 6 分及以上的内容。
3. 输出一份 Markdown 简报，包含以下内容：
   - 标题：📊 多维学术情报简报 | {datetime.now().strftime('%Y-%m-%d')}
   - 🔥 高分精选（论文和项目混合，按分数排序）：
     - 对于论文：提供标题、来源期刊/会议、核心摘要、与用户方向的关联。
     - 对于 GitHub 项目：提供项目名、Stars、语言、解决了什么问题。
   - 🔗 跨界关联：分析是否有论文提到了某些 GitHub 项目，或者 GitHub 项目实现了某篇论文的想法（若有）。
   - 💡 扫描总结：共扫描 X 篇（论文 Y 篇，项目 Z 个），筛选出 W 项高价值内容。

请直接输出 Markdown 报告内容，不要输出其他解释。"""

    msg = [{"role": "user", "content": prompt}]
    try:
        report = call_llm(msg, env)
        rep_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
        os.makedirs(rep_dir, exist_ok=True)
        rep_path = os.path.join(rep_dir, f"daily_{datetime.now().strftime('%Y-%m-%d')}.md")
        with open(rep_path, 'w', encoding='utf-8') as f: f.write(report)
        
        for art in all_data: 
            if art.get('is_new'): art['is_new'] = False; art['analyzed'] = True
        with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"[DONE] Report saved: {rep_path}\n{report}")
    except Exception as e: print(f"[ERROR] {e}")

if __name__ == '__main__': main()
