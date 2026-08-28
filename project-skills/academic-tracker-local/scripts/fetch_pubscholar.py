import os, json, time, re, requests

def main():
    print('[PubScholar] Starting mission...')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
        'Referer': 'https://pubscholar.cn/',
        'Accept': 'application/json, text/plain, */*'
    }
    keywords = ['遥感', '地理信息', '空间智能']
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    art_file = os.path.join(data_dir, 'all_sources.json')
    all_data = []
    if os.path.exists(art_file):
        with open(art_file, encoding='utf-8') as f: all_data = json.load(f)
    existing_titles = {a.get('title', '').strip() for a in all_data}
    new_items = []

    for kw in keywords:
        try:
            print(f'  - Searching "{kw}"...')
            url = f"https://pubscholar.cn/api/search/academic?keyword={kw}&type=&orderBy=publishYear&pageSize=3"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for item in data.get('data', {}).get('list', []):
                    title = re.sub(r'<[^>]+>', '', item.get('title', ''))
                    if title and title not in existing_titles:
                        content = re.sub(r'<[^>]+>', '', item.get('content', ''))
                        new_items.append({
                            'title': title, 'summary': content[:200],
                            'link': f"https://pubscholar.cn/detail?id={item.get('id')}",
                            'source': 'PubScholar', 'repo_name': kw,
                            'type': item.get('docType', ''), 'is_new': True
                        })
            time.sleep(1)
        except Exception as e: print(f'    Error: {e}')

    for art in all_data: art['is_new'] = False
    all_data.extend(new_items)
    
    with open(art_file, 'w', encoding='utf-8') as f: json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f'[PubScholar] Found {len(new_items)} new items.')
    if new_items:
        print('\\n--- NEW TITLES ---')
        for r in new_items: print(f'- [{r.get("type")}] {r["title"]}')

if __name__ == '__main__':
    main()
