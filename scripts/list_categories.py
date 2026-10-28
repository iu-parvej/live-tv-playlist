import re
from collections import Counter
import sys

sys.stdout.reconfigure(encoding='utf-8')

cats = Counter()
with open('playlist.m3u', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('#EXTINF:'):
            m = re.search(r'group-title="([^"]+)"', line)
            if m:
                cats[m.group(1)] += 1
            else:
                cats['Uncategorized'] += 1

print(f"Total Unique Categories: {len(cats)}")
print("=" * 45)
for cat, count in cats.most_common():
    print(f"{cat:<35} : {count:>4} channels")
