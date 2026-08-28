import os, json, time, requests
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

def main():
    env = load_env()
    # CrossRef Keywords targeting Journals not on arXiv (IEEE, Springer, etc.)
    keywords = ['remote sensing', 'geospatial intelligence', 'urban computing']
    limit = int(env.get('CROSSREF_LIMIT', 5))
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    # CrossRef uses DOI as ID
    existing_dois = {a.get('id', '').lower().replace('https://doi.org/', '') for a in all_data}
    new_items = []
    
    print(f"[CrossRef] Scanning high-impact journals...")
    headers = {'User-Agent': 'AcademicTracker/1.0 (yang@example.com)'}
    
    for kw in keywords:
        try:
            print(f' - Searching: {kw}')
            # Filter for recent items, sort by date
            url = f'https://api.crossref.org/works?query={kw}&filter=from-pub-date:2024&rows={limit}&sort=published'
            res = requests.get(url, headers=headers, timeout=10).json()
            
            msg = res.get('message', {})
            items = msg.get('items', [])
            
            for item in items:
                doi = item.get('DOI', '')
                doi_normalized = doi.lower()
                
                if doi and doi_normalized not in existing_dois:
                    existing_dois.add(doi_normalized)
                    title = (item.get('title') or ['Untitled'])[0]
                    abstract = (item.get('abstract') or '')[:300]
                    
                    new_items.append({
                        'title': title,
                        'summary': abstract.replace('<jats:p>', '').replace('</jats:p>', ''),
                        'link': f"https://doi.org/{doi}",
                        'id': f"https://doi.org/{doi}", # Primary Key
                        'source': 'CrossRef',
                        'repo_name': item.get('container-title', ['Journal'])[0] if item.get('container-title') else 'Unknown',
                        'type': item.get('type', ''),
                        'pub_date': item.get('published-print', {}).get('date-parts', [['']])[0][0],
                        'is_new': True
                    })
            time.sleep(0.5)
        except Exception as e: print(f"    Error: {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[CrossRef] Found {len(new_items)} new journal papers.")
    if new_items:
        print('\n--- NEW JOURNAL PAPERS ---')
        for r in new_items: print(f"- [{r['repo_name']}] {r['title'][:60]}...")

if __name__ == '__main__': main()
