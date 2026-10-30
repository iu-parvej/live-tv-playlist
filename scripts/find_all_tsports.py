import json
import re
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('config/sources.json', 'r', encoding='utf-8') as f:
    sources = json.load(f)['sources']

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

all_tsports_candidates = []

for s in sources:
    name = s['name']
    url = s['url']
    print(f"Fetching {name}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            
            curr_inf = None
            for l in lines:
                if l.startswith('#EXTINF:'):
                    curr_inf = {'source': name, 'extinf': l}
                    comma = l.split(',')[-1].strip()
                    curr_inf['name'] = comma
                    m_logo = re.search(r'tvg-logo="([^"]+)"', l)
                    curr_inf['logo'] = m_logo.group(1) if m_logo else ""
                elif l.startswith('http://') or l.startswith('https://'):
                    url_stream = l
                    title = curr_inf['name'] if curr_inf else ""
                    # Check if T Sports
                    if curr_inf and any(k in curr_inf['name'].lower() for k in ['t sports', 't-sports', 'tsports']) or \
                       any(k in url_stream.lower() for k in ['tsport', 't-sport', 't_sport', 'tsports']):
                        all_tsports_candidates.append({
                            'source': name,
                            'title': curr_inf['name'] if curr_inf else 'T Sports',
                            'logo': curr_inf.get('logo', '') if curr_inf else '',
                            'url': url_stream
                        })
                    curr_inf = None
    except Exception as e:
        print(f"  Error fetching {name}: {e}")

print(f"\nTotal T Sports candidate links found: {len(all_tsports_candidates)}")
unique_urls = set()
deduped_candidates = []
for c in all_tsports_candidates:
    if c['url'] not in unique_urls:
        unique_urls.add(c['url'])
        deduped_candidates.append(c)

print(f"Unique candidate URLs: {len(deduped_candidates)}")
for idx, c in enumerate(deduped_candidates, 1):
    print(f"{idx:2d}. [{c['source']}] {c['title']} -> {c['url']}")
