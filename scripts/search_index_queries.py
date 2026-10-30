import json

with open('config/tv_logos_index.json', 'r', encoding='utf-8') as f:
    idx = json.load(f)

queries = ['sony', 'discovery', 'geographic', 'animal', 'tlc', 'nickelodeon', 'disney', 'ptv', 'sports', 'bein', 'dangal', 'colors']

for q in queries:
    matches = [x for x in idx if q in x.lower()]
    print(f"=== Query '{q}': {len(matches)} matches ===")
    for m in matches[:10]:
        print("  ", m)
