import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re

with open('output/playlist_multiserver.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

from core.normalizer import ChannelNormalizer

normalizer = ChannelNormalizer()

streams = []
curr = {}
for line in lines:
    line = line.strip()
    if line.startswith('#EXTINF:'):
        curr = {}
        m_logo = re.search(r'tvg-logo="([^"]+)"', line)
        m_grp = re.search(r'group-title="([^"]+)"', line)
        m_id = re.search(r'tvg-id="([^"]+)"', line)
        title = line.split(',')[-1].strip()
        curr['display_name'] = title
        curr['raw_name'] = title
        curr['logo'] = m_logo.group(1) if m_logo else ''
        curr['group'] = m_grp.group(1) if m_grp else ''
        curr['tvg_id'] = m_id.group(1) if m_id else ''
    elif line.startswith('http://') or line.startswith('https://'):
        if curr:
            curr['url'] = line
            m_lat = re.search(r'\(.*?(?:Server \d+ - )?(\d+)ms.*?\)', curr['display_name'])
            curr['latency_ms'] = int(m_lat.group(1)) if m_lat else 999
            curr['is_bdix'] = '[BDIX]' in curr['display_name']
            streams.append(curr)
            curr = {}

curated = normalizer.group_and_rank_curated(streams)
print(f"Total curated channels: {len(curated)}")

for ch in curated:
    print(f"[{ch['category']}] {ch['name']} ({len(ch['streams'])} streams)")
