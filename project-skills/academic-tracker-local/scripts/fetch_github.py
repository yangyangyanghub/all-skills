import os, json, time, requests, datetime

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
    queries = ["geospatial+AI", "remote+sensing", "GIS"] # can be more
    token = env.get('GITHUB_TOKEN', '')
    headers = {'Authorization': f'token {token}'} if token else {}
    min_stars = int(env.get('GITHUB_MIN_STARS', 50))
    
    # Recent 7 days pushed
    pushed_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    existing_links = {a.get('link', a.get('id', '')) for a in all_data}
    new_items = []
    
    print(f"[GitHub] Fetching repos pushed after {pushed_date} with > {min_stars} stars")
    for q in queries:
        try:
            url = f"https://api.github.com/search/repositories?q={q}+pushed:>{pushed_date}&sort=updated&per_page=10"
            res = requests.get(url, headers=headers, timeout=10).json()
            for r in res.get('items', []):
                if r.get('stargazers_count', 0) >= min_stars:
                    link = r['html_url']
                    if link not in existing_links:
                        existing_links.add(link)
                        new_items.append({
                            'title': r['full_name'], 'summary': r.get('description','')[:300],
                            'link': link, 'source': 'GitHub', 'repo_name': q,
                            'stars': r.get('stargazers_count', 0), 'language': r.get('language', ''),
                            'is_new': True
                        })
            time.sleep(1)
        except Exception as e: print(f"[Error] {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[GitHub] Found {len(new_items)} new repos.")

if __name__ == '__main__': main()
