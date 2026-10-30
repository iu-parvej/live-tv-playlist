import re
import urllib.request
import time
from collections import Counter

channels = []
curr = {}

with open('temp/skym3u_prfj.m3u', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            curr = {}
            m_grp = re.search(r'group-title="([^"]*)"', line)
            name = line.split(',')[-1].strip()
            curr['name'] = name
            curr['group'] = m_grp.group(1) if m_grp else 'Ungrouped'
        elif line.startswith('http://') or line.startswith('https://'):
            if curr:
                curr['url'] = line
                channels.append(curr)
                curr = {}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Test a sample of 20 failed channels from Sports, Movies, Entertainment
sports = [c for c in channels if c['group'] == 'Sports'][:10]
movies = [c for c in channels if c['group'] == 'Movies'][:5]
docs = [c for c in channels if c['group'] == 'Documentary'][:5]

test_sample = sports + movies + docs
print(f"Testing {len(test_sample)} sample channels...")

for ch in test_sample:
    url = ch['url']
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read(256)
            print(f"  OK {resp.status}: {ch['name']} ({ch['group']}) - Content-Type: {resp.headers.get('Content-Type')}")
    except Exception as e:
        print(f"  FAIL: {ch['name']} ({ch['group']}) -> {e}")
