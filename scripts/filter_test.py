import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the working streams from the latest check
with open('output/playlist_multiserver.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in multiserver: {len(lines)}")
# Find all unique channel names and sample them
channels = []
curr = {}
for line in lines:
    line = line.strip()
    if line.startswith('#EXTINF:'):
        curr = {}
        m_logo = re.search(r'tvg-logo="([^"]+)"', line)
        m_grp = re.search(r'group-title="([^"]+)"', line)
        title = line.split(',')[-1].strip()
        curr['title'] = title
        curr['logo'] = m_logo.group(1) if m_logo else ""
        curr['group'] = m_grp.group(1) if m_grp else ""
    elif line.startswith('http://') or line.startswith('https://'):
        if curr:
            curr['url'] = line
            channels.append(curr)
            curr = {}

print(f"Total active streams parsed: {len(channels)}")

# Let's see all channel names containing 'sports' or 'cricket'
sports_found = [c['title'] for c in channels if any(k in c['title'].lower() for k in ['sport', 'cricket', 'football', 'willow', 'bein', 'sky', 'tnt', 'supersport', 'asports', 'a sports', 'ptv'])]
print(f"Sports found ({len(sports_found)}):")
for s in sorted(set(sports_found))[:30]:
    print("  ", s)
