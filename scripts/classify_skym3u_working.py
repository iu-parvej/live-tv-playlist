import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re

with open('temp/working_decrypted.json', 'r', encoding='utf-8') as f:
    working = json.load(f)

from core.normalizer import ChannelNormalizer

norm = ChannelNormalizer()

categorized = {}
for ch in working:
    name = norm.clean_name(ch['name'])
    cat = norm.classify_curated(name, ch['group'])
    if not cat:
        cat = norm.classify_curated(ch['name'], ch['group'])
    if not cat:
        continue
    
    if cat not in categorized:
        categorized[cat] = []
    
    logo = norm.resolve_logo(name, ch.get('logo', ''))
    categorized[cat].append({
        "raw_name": ch['name'],
        "name": name,
        "group": ch['group'],
        "latency_ms": ch['latency_ms'],
        "is_bdix": ch['is_bdix'],
        "real_url": ch['real_url'],
        "logo": logo
    })

print(f"Total working channels: {len(working)}")
total_curated_matches = sum(len(v) for v in categorized.values())
print(f"Total matching VIP Curated categories: {total_curated_matches}")

for cat in sorted(categorized.keys()):
    items = categorized[cat]
    print(f"\n=== {cat} ({len(items)} channels) ===")
    for item in items:
        bdix = " [BDIX]" if item['is_bdix'] else ""
        print(f"  {item['name']} ({item['raw_name']}) - {item['latency_ms']}ms{bdix}")
