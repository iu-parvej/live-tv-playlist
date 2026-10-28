import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

import json
import re
from core.normalizer import ChannelNormalizer
from core.generator import PlaylistGenerator
from core.publisher import GitHubPublisher

with open('output/status.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

streams = []
with open('output/playlist_multiserver.m3u', 'r', encoding='utf-8') as f:
    curr = {}
    for line in f:
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

normalizer = ChannelNormalizer()
channels = normalizer.group_and_rank(streams)
curated = normalizer.group_and_rank_curated(streams)

print(f"Total Full Channels: {len(channels)}")
print(f"VIP Curated Channels: {len(curated)}")

gen = PlaylistGenerator()
gen.generate_all(channels, stats, curated_channels=curated)

pub = GitHubPublisher()
urls = pub.commit_and_push(stats)
print("Successfully generated and pushed to GitHub!")
print("Curated VIP Playlist URL:", urls['curated'])
