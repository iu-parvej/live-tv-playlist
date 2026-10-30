import re
from collections import Counter
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('output/playlist_curated.m3u', 'r', encoding='utf-8') as f:
    text = f.read()

categories = re.findall(r'group-title="([^"]+)"', text)
counts = Counter(categories)

print("="*50)
print("Curated Playlist Categories & Channel Counts:")
print("="*50)
for c in sorted(counts.keys()):
    print(f" {c}: {counts[c]} streams")
print("="*50)
print(f"Total entries in playlist_curated.m3u: {len(categories)}")

# Check logos
missing_logos = 0
for l in text.splitlines():
    if l.startswith('#EXTINF:'):
        m = re.search(r'tvg-logo="([^"]*)"', l)
        if not m or not m.group(1).strip() or m.group(1).strip() == 'https://i.imgur.com/WpMA9kC.png':
            missing_logos += 1
            print(f"Missing logo: {l}")

print(f"Missing or placeholder logos: {missing_logos}")
