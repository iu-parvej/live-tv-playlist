import re
from collections import Counter

channels = []
curr = {}

with open('temp/skym3u_prfj.m3u', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            curr = {}
            m_logo = re.search(r'tvg-logo="([^"]*)"', line)
            m_grp = re.search(r'group-title="([^"]*)"', line)
            m_id = re.search(r'tvg-id="([^"]*)"', line)
            name = line.split(',')[-1].strip()
            curr['name'] = name
            curr['logo'] = m_logo.group(1) if m_logo else ''
            curr['group'] = m_grp.group(1) if m_grp else 'Ungrouped'
            curr['tvg_id'] = m_id.group(1) if m_id else ''
            curr['extinf'] = line
        elif line.startswith('http://') or line.startswith('https://'):
            if curr:
                curr['url'] = line
                channels.append(curr)
                curr = {}

print(f"Total Channels Parsed: {len(channels)}")

groups = Counter([c['group'] for c in channels])
print("\n=== Category Breakdown ===")
for g, cnt in groups.most_common():
    print(f"  {g}: {cnt} channels")

print("\n=== Checking for T Sports & GTV ===")
tsports = [c for c in channels if 't sports' in c['name'].lower() or 'tsports' in c['name'].lower() or 'tsport' in c['url'].lower()]
print(f"Found {len(tsports)} T Sports channel(s):")
for ts in tsports:
    print(f"  Name: {ts['name']} | Group: {ts['group']} | URL: {ts['url']}")

gtv = [c for c in channels if 'gazi' in c['name'].lower() or 'gtv' in c['name'].lower()]
print(f"\nFound {len(gtv)} GTV channel(s):")
for g in gtv:
    print(f"  Name: {g['name']} | Group: {g['group']} | URL: {g['url']}")

print("\n=== Sample of First 20 Channels ===")
for c in channels[:20]:
    print(f"  [{c['group']}] {c['name']} -> {c['url'][:60]}...")
