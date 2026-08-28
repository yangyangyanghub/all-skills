import os, json, time, feedparser

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
    env = load_env()
    limit = int(env.get('RSS_LIMIT', 10))
    sources = []
    rss_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rss_list.txt')
    if os.path.exists(rss_file):
        with open(rss_file, encoding='utf-8') as f:
            sources = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    existing_links = {a.get('link', a.get('id', '')) for a in all_data}
    new_art = []

    print(f"[RSS] Fetching {len(sources)} sources...")
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for i, e in enumerate(feed.entries):
                if i >= limit: break
                link = e.get('link', e.get('id', ''))
                if link and link not in existing_links:
                    existing_links.add(link)
                    new_art.append({
                        'title': e.get('title','').strip(), 
                        'summary': e.get('summary','').strip()[:500],
                        'link': link, 'source': 'RSS', 'repo_name': feed.feed.get('title', ''),
                        'is_new': True
                    })
            time.sleep(0.5)
        except Exception as e: print(f"[Error] {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_art)
    
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[RSS] Found {len(new_art)} new articles.")

if __name__ == '__main__': main()
