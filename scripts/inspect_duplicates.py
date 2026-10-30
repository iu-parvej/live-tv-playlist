import json
import re

with open('output/playlist_curated.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

channels = []
for line in lines:
    line = line.strip()
    if line.startswith('#EXTINF:'):
        name = line.split(',')[-1].strip()
        m_grp = re.search(r'group-title="([^"]+)"', line)
        grp = m_grp.group(1) if m_grp else 'Unknown'
        # Strip server and ms
        clean = re.sub(r'\s*\((?:Server\s*\d+\s*[-:]\s*)?\d+ms.*?\)', '', name).strip()
        clean = re.sub(r'^\s*\d+\.\s*', '', clean).strip()
        channels.append((grp, clean, name))

from collections import Counter
counts = Counter([c[1] for c in channels])

print("=== DUPLICATE CHANNEL COUNTS ===")
for ch, count in counts.most_common():
    if count > 1:
        print(f"  {ch}: {count} occurrences")

print(f"\nTotal channel entries: {len(channels)}")
print(f"Total unique channel names: {len(counts)}")
