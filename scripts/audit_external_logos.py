import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    text = f.read()

lines = [l for l in text.splitlines() if l.startswith('#EXTINF:')]
external = []
for l in lines:
    m = re.search(r'tvg-logo="([^"]+)"', l)
    name = l.split(',')[-1].strip()
    if m:
        logo = m.group(1)
        if 'raw.githubusercontent.com/iu-parvej/live-tv-playlist' not in logo:
            external.append((name, logo))

print(f"Total external logo occurrences: {len(external)}")
uniq_ext = sorted(list(set(external)))
print(f"Distinct channels with external logo: {len(uniq_ext)}")
for n, l in uniq_ext:
    print(f"  {n:<32} -> {l}")
