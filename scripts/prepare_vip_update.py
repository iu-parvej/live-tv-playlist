import json
import re
import os
import requests

logos = set(os.listdir('logos'))
print(f"Total logos in logos/: {len(logos)}")

# Check logos in 3pks and oaiu for specific channels
for fname in ['temp/skym3u_3pks.m3u', 'temp/skym3u_oaiu.m3u']:
    with open(fname, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#EXTINF'):
                for k in ['9x jalwa', 'docubay', 'kabaddi', 'jungle book', 'green gold']:
                    if k in line.lower():
                        m = re.search(r'tvg-logo="([^"]+)"', line)
                        name = line.split(',')[-1].strip()
                        logo = m.group(1) if m else 'None'
                        print(f"{name} -> {logo}")
