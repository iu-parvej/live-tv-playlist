import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
from run_curated_check import classified

by_cat = defaultdict(list)
for s in classified:
    by_cat[s['curated_category']].append(s)

for cat in sorted(by_cat.keys()):
    print(f"\n==================== {cat} ({len(by_cat[cat])}) ====================")
    unique_names = set()
    for s in by_cat[cat]:
        # Clean title
        clean = re.sub(r'\(.*?\)', '', s['title']).strip()
        clean = re.sub(r'^(?:--Live\(|---Live\(|MIXER \| |CR \| |MOV \| |MU \| )', '', clean)
        clean = re.sub(r'\)$|\)---$', '', clean).strip()
        if clean not in unique_names:
            unique_names.add(clean)
            print(f"  • {clean:<35} [Ping: {s['latency']}ms] Logo: {'YES' if s['logo'] else 'NO'}")
