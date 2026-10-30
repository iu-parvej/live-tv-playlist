import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('config/sources.json', 'r', encoding='utf-8') as f:
    sources = json.load(f)['sources']

ayna_links = []
for s in sources:
    try:
        req = urllib.request.Request(s['url'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            lines = [l.strip() for l in r.read().decode('utf-8', errors='ignore').splitlines() if l.strip()]
            curr = {}
            for l in lines:
                if l.startswith('#EXTINF:'):
                    curr = {'source': s['name'], 'title': l.split(',')[-1].strip(), 'raw': l}
                elif l.startswith('http'):
                    if curr:
                        curr['url'] = l
                        if 'aynaott.com' in l:
                            ayna_links.append(curr)
                        curr = {}
    except Exception as e:
        pass

print(f"Total AynaOTT links across all sources: {len(ayna_links)}")
sports_ayna = [a for a in ayna_links if any(k in a['title'].lower() for k in ['sport', 'tsport', 't sport', 't-sport', 'gazi', 'gtv'])]
print(f"Sports AynaOTT links: {len(sports_ayna)}")
seen = set()
for a in sports_ayna:
    u = a['url'].split('?')[0]
    if u not in seen:
        seen.add(u)
        print(f"[{a['source']}] {a['title']} -> {a['url']}")
