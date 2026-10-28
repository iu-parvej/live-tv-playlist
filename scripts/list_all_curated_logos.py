import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    seen = set()
    for line in f:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            name = line.split(',')[-1].strip()
            clean_name = re.sub(r'\(.*?\)', '', name).strip()
            m_logo = re.search(r'tvg-logo="([^"]+)"', line)
            logo = m_logo.group(1).strip() if m_logo else ""
            if clean_name not in seen:
                seen.add(clean_name)
                print(f"{clean_name:<35} | Logo: {logo[:70]}")
