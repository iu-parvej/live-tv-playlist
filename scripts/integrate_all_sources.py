import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalizer import ChannelNormalizer
from core.generator import PlaylistGenerator
from core.publisher import GitHubPublisher

with open('output/status.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

# 1. Load existing multiserver streams
existing_streams = []
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
                existing_streams.append(curr)
                curr = {}

print(f"Existing streams loaded: {len(existing_streams)}")

seen_urls = set(s['url'].strip().lower() for s in existing_streams)
added_count = 0

# Helper to add stream list
def add_new_streams(file_path: str, source_label: str):
    global added_count
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    print(f"Loaded {len(items)} items from {source_label} ({file_path})")
    for item in items:
        url = (item.get('real_url') or item.get('url') or '').strip()
        if not url:
            continue
        u_norm = url.lower()
        if u_norm in seen_urls:
            continue
        seen_urls.add(u_norm)
        existing_streams.append({
            "display_name": item["name"],
            "raw_name": item["name"],
            "logo": item.get("logo", ""),
            "group": item.get("group", ""),
            "tvg_id": "",
            "url": url,
            "latency_ms": item.get("latency_ms", 999),
            "is_bdix": item.get("is_bdix", False)
        })
        added_count += 1

# 2. Add streams from prfj, oaiu, and 3pks
add_new_streams('temp/working_decrypted.json', 'SkyM3U prfj')
add_new_streams('temp/working_oaiu.json', 'SkyM3U oaiu (AynaOTT)')
add_new_streams('temp/working_3pks.json', 'SkyM3U 3pks (Indian/Global)')

print(f"Total streams after merge: {len(existing_streams)} (+{added_count} new)")

# 3. Ensure T-SPORTS-FULL-HD has 50ms BDIX priority
for s in existing_streams:
    if "T-SPORTS-FULL-HD" in s['url']:
        s['latency_ms'] = 50
        s['is_bdix'] = True
        s['display_name'] = "T Sports HD"
        s['raw_name'] = "T Sports HD"

# 4. Group and rank
normalizer = ChannelNormalizer()
channels = normalizer.group_and_rank(existing_streams)
curated = normalizer.group_and_rank_curated(existing_streams)

print(f"Total Consolidated Channels: {len(channels)}")
print(f"VIP Curated Distinct Channel Groups: {len(curated)}")

# Check sample BD channels and their streams count
for c in curated:
    if any(k in c['name'].lower() for k in ['somoy', 'jamuna', 'atn bangla', 'ntv', 't sports', 'discovery', 'cartoon']):
        print(f"  ★ {c['name']} ({c['category']}) -> {len(c['streams'])} streams | Logo: {c['logo']}")

# 5. Generate Playlists
gen = PlaylistGenerator()
gen.generate_all(channels, stats, curated_channels=curated)

# 6. Copy output to root
pub = GitHubPublisher()
pub.sync_output_to_root()

print("Playlists generated and synchronized to root successfully!")
