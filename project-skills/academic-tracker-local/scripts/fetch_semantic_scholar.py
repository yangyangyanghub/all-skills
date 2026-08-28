import os, json, time, requests

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
    keywords = ["spatial intelligence", "remote sensing", "geospatial foundation model"]
    year_range = env.get('SEMANTIC_YEAR_RANGE', '2024-2026')
    limit = int(env.get('SEMANTIC_LIMIT', 5))
    api_key = env.get('SEMANTIC_API_KEY', '')
    headers = {'x-api-key': api_key} if api_key else {}

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    existing_links = {a.get('link', a.get('id', '')) for a in all_data}
    new_items = []
    
    print(f"[Semantic Scholar] Fetching for: {keywords}")
    for kw in keywords:
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {'query': kw, 'year': year_range, 'limit': limit, 'fields': 'title,abstract,authors,url,year,citationCount,externalIds'}
            res = requests.get(url, params=params, headers=headers, timeout=10).json()
            for p in res.get('data', []):
                link = p.get('externalIds', {}).get('DOI', p.get('url', p.get('paperId', '')))
                if link and link not in existing_links:
                    existing_links.add(link)
                    new_items.append({
                        'title': p['title'], 'summary': p.get('abstract','')[:500],
                        'link': link, 'source': 'Semantic Scholar', 'repo_name': kw,
                        'citationCount': p.get('citationCount', 0), 'is_new': True
                    })
            time.sleep(0.5)
        except Exception as e: print(f"[Error] {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[Semantic Scholar] Found {len(new_items)} new papers.")

if __name__ == '__main__': main()
