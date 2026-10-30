import re
import json

with open('output/playlist_curated.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

channels = []
for line in lines:
    line = line.strip()
    if line.startswith('#EXTINF:'):
        name = line.split(',')[-1].strip()
        m_logo = re.search(r'tvg-logo="([^"]+)"', line)
        m_grp = re.search(r'group-title="([^"]+)"', line)
        logo = m_logo.group(1) if m_logo else ''
        grp = m_grp.group(1) if m_grp else ''
        channels.append((grp, name, logo))

print(f"Total entries in playlist_curated: {len(channels)}")
for grp, name, logo in channels:
    is_svg = logo.endswith('.svg')
    has_wikimedia = 'upload.wikimedia.org' in logo
    issue = ""
    if not logo or logo == "https://i.imgur.com/WpMA9kC.png":
        issue = "MISSING_LOGO"
    elif is_svg:
        issue = "SVG_LOGO"
    elif has_wikimedia:
        issue = "WIKIMEDIA"
    print(f"[{grp}] {name} -> {issue or 'OK'} | {logo[:80]}")
