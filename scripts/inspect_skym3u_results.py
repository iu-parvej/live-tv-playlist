import json
from collections import Counter

with open('temp/skym3u_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

reasons = Counter([x['reason'] for x in data['failed']])
for r, c in reasons.most_common():
    print(f"{r}: {c}")

print("\nSample failed channels:")
for x in data['failed'][:15]:
    print(f"  {x['name']} ({x['group']}): {x['reason']}")
