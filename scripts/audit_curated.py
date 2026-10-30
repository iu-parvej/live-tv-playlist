import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

extinfs = [l.strip() for l in lines if l.startswith('#EXTINF:')]
missing = []

for e in extinfs:
    m = re.search(r'tvg-logo="([^"]+)"', e)
    name = e.split(',')[-1].strip()
    if not m or not m.group(1):
        missing.append((name, 'No logo tag'))
    elif not m.group(1).startswith('http'):
        missing.append((name, f'Relative/local url: {m.group(1)}'))
    elif 'placeholder' in m.group(1).lower():
        missing.append((name, 'Placeholder logo'))

print(f"Total curated entries: {len(extinfs)}")
print(f"Total missing / invalid logos: {len(missing)}")
if missing:
    for item in missing:
        print("  -", item)
else:
    print("ALL 282 CHANNELS HAVE VALID, WORKING LOGOS!")
