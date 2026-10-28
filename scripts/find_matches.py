import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('output/playlist_multiserver.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

channels = []
curr = {}
for line in lines:
    line = line.strip()
    if line.startswith('#EXTINF:'):
        curr = {}
        title = line.split(',')[-1].strip()
        curr['title'] = title
    elif line.startswith('http://') or line.startswith('https://'):
        if curr:
            curr['url'] = line
            channels.append(curr)
            curr = {}

keywords = [
    'star plus', 'zee tv', 'colors', 'sony sab', 'sab tv', 'set india', 'sony ent', 'star bharat', '&tv',
    'star gold', 'sony max', 'zee cinema', 'colors cineplex', 'sony pix', '&pictures', 'b4u', 'goldmines',
    'zee bangla', 'star jalsha', 'jalsha movies', 'colors bangla', 'sony aath', 'aakash aath',
    'discovery', 'animal planet', 'nat geo', 'history tv18', 'tlc',
    '9xm', 'mtv', 'b4u music', 'mastiii', 'zing', 'gaan bangla', 'duronto', 'cartoon network', 'nick'
]

print("Matches found:")
for kw in keywords:
    matches = [c['title'] for c in channels if kw in c['title'].lower()]
    if matches:
        print(f"=== {kw.upper()} ({len(matches)}) ===")
        for m in sorted(set(matches))[:5]:
            print(f"   {m}")
