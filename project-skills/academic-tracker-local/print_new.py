import json; data=json.load(open(r'E:\code\my-ai-workspace\.opencode\skill\academic-tracker-local\data\all_sources.json', encoding='utf-8')); [print(x['title'][:50]) for x in data if x.get('is_new')]
