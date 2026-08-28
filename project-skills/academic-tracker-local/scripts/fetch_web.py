import os, json, time
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

def load_env():
    env = {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                if line.strip() and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1); env[k.strip()] = v.strip()
    return env

def main():
    if not DDGS:
        print("[Web] duckduckgo-search not installed. Skipping. Run: pip install duckduckgo-search"); return
    
    env = load_env()
    keywords = json.loads(env.get('WEB_KEYWORDS', '["GeoAI trends 2026", "Spatial Intelligence news"]'))
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    existing_titles = {a.get('title', '').strip() for a in all_data}
    new_items = []

    print(f"[Web] Scanning internet via DuckDuckGo...")
    try:
        with DDGS() as ddgs:
            for kw in keywords:
                for r in ddgs.text(kw, max_results=5, timelimit='w'): # 仅限一周内
                    title = r.get('title', '')
                    if title and title not in existing_titles:
                        existing_titles.add(title)
                        new_items.append({
                            'title': title,
                            'summary': r.get('body', '')[:300],
                            'link': r.get('href', ''),
                            'source': 'Web',
                            'repo_name': 'News/Articles',
                            'is_new': True
                        })
                time.sleep(1.5)
    except Exception as e: print(f"[Web Error] {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[Web] Found {len(new_items)} new web items.")

if __name__ == '__main__': main()
