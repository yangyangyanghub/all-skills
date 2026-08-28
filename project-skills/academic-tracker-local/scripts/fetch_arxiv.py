import os, json, time, feedparser
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
    # arXiv Keywords for GeoAI/Remote Sensing
    keywords = ['"remote sensing" AND "deep learning"', '"geospatial foundation model"', '"spatial intelligence"']
    limit = int(env.get('ARXIV_LIMIT', 5))
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)

    # arXiv IDs are unique
    existing_ids = {a.get('id', '') for a in all_data}
    new_items = []
    
    print(f"[arXiv] Scanning for preprints...")
    # Using arXiv API URL format with feedparser (lightweight)
    # Constructing query URL: http://export.arxiv.org/api/query?search_query={}&max_results={}&sortBy=submittedDate&sortByDescending
    
    for q in keywords:
        try:
            # Clean query for URL
            print(f' - Searching: {q}')
            url = f'http://export.arxiv.org/api/query?search_query=all:{q}&max_results={limit}&sortBy=submittedDate&sortOrder=descending'
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                # entry.id is the arXiv unique ID
                aid = entry.id
                if aid not in existing_ids:
                    existing_ids.add(aid)
                    # Extract authors
                    authors = [a.name for a in entry.get('authors', [])]
                    
                    new_items.append({
                        'title': entry.get('title', '').replace('\n', ' '),
                        'summary': entry.get('summary', '')[:400].replace('\n', ' '),
                        'link': entry.get('link', ''),
                        'source': 'arXiv',
                        'repo_name': 'Preprints/GeoAI',
                        'authors': authors,
                        'id': aid,
                        'published': entry.get('published', ''),
                        'is_new': True
                    })
            time.sleep(2.5) # arXiv recommends 3s wait, we use 2.5s
        except Exception as e: print(f"    Error: {e}")

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[arXiv] Found {len(new_items)} new preprints.")
    if new_items:
        print('\n--- NEW PREPRINTS ---')
        for r in new_items: print(f"- {r['title'][:60]}...")

if __name__ == '__main__': main()
