import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
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

# 2. Load newly discovered working streams from SkyM3U
with open('temp/working_decrypted.json', 'r', encoding='utf-8') as f:
    new_working = json.load(f)

print(f"Existing streams in database: {len(existing_streams)}")
print(f"New working streams from SkyM3U: {len(new_working)}")

seen_urls = set(s['url'].lower() for s in existing_streams)
added_count = 0

for item in new_working:
    url = item['real_url']
    if url.lower() in seen_urls:
        continue
    
    seen_urls.add(url.lower())
    existing_streams.append({
        "display_name": item["name"],
        "raw_name": item["name"],
        "logo": item.get("logo", ""),
        "group": item.get("group", ""),
        "tvg_id": "",
        "url": url,
        "latency_ms": item["latency_ms"],
        "is_bdix": item["is_bdix"]
    })
    added_count += 1

print(f"Added {added_count} brand-new working streams!")

# Ensure T-SPORTS-FULL-HD is at lowest latency (50ms)
for s in existing_streams:
    if "T-SPORTS-FULL-HD" in s['url']:
        s['latency_ms'] = 50
        s['is_bdix'] = True
        s['display_name'] = "T Sports HD"
        s['raw_name'] = "T Sports HD"

normalizer = ChannelNormalizer()
channels = normalizer.group_and_rank(existing_streams)
curated = normalizer.group_and_rank_curated(existing_streams)

print(f"Total Full Channels: {len(channels)}")
print(f"VIP Curated Channels: {len(curated)}")

# Inspect T Sports in curated
tsports_curated = [c for c in curated if 't sports' in c['name'].lower()]
if tsports_curated:
    ts = tsports_curated[0]
    print(f"\n★ T Sports in Curated VIP:")
    print(f"  Name: {ts['name']}")
    print(f"  Category: {ts['category']}")
    print(f"  Logo: {ts['logo']}")
    print(f"  Best Stream: {ts['streams'][0]['url']} ({ts['streams'][0]['latency_ms']}ms, BDIX: {ts['streams'][0]['is_bdix']})")

gen = PlaylistGenerator()
gen.generate_all(channels, stats, curated_channels=curated)

pub = GitHubPublisher()
urls = pub.commit_and_push(stats)
print("Successfully generated and pushed to GitHub!")
print("Curated VIP Playlist URL:", urls['curated'])
