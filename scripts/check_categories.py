import re

with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

groups = set()
for l in lines:
    if l.startswith('#EXTINF:'):
        m = re.search(r'group-title="([^"]+)"', l)
        if m:
            groups.add(m.group(1))

print("Distinct categories in playlist_curated.m3u:")
for g in sorted(groups):
    print(f"  - '{g}'")
