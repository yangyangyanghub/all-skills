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
    # ADS API Key helps with rate limits, but public access is allowed
    api_key = env.get('NASA_ADS_API_KEY', '')
    headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
    
    # 精准定位：空间科学、遥感、卫星
    queries = ['"remote sensing" AND "machine learning"', '"geospatial intelligence"', '"spatial computing"']
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    art_file = os.path.join(data_dir, 'all_sources.json')
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    existing_links = {a.get('link', a.get('id', '')) for a in all_data}
    new_items = []
    
    print(f"[NASA ADS] Scanning space & geospatial literature...")
    for q in queries:
        try:
            url = "https://api.adsabs.harvard.edu/v1/search/query"
            params = {'q': q, 'fl': 'title,abstract,bibcode,pub_year,author', 'rows': 5, 'sort': 'date desc'}
            res = requests.get(url, params=params, headers=headers, timeout=10).json()
            for doc in res.get('response', {}).get('docs', []):
                link = f"https://ui.adsabs.harvard.edu/abs/{doc['bibcode']}/abstract"
                if link not in existing_links:
                    existing_links.add(link)
                    title = doc.get('title', [''])[0]
                    new_items.append({
                        'title': title, 
                        'summary': " ".join(doc.get('abstract', ['']))[:400],
                        'link': link, 
                        'source': 'NASA ADS', 
                        'repo_name': 'Space/Remote Sensing',
                        'pub_year': doc.get('pub_year', [''])[0],
                        'is_new': True
                    })
            time.sleep(0.5)
        except Exception as e: print(f"[Error] {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[NASA ADS] Found {len(new_items)} new items.")

if __name__ == '__main__': main()
