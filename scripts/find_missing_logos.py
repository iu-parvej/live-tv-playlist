import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

channels_missing_logo = []
channels_with_logo = []

with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            name = line.split(',')[-1].strip()
            # clean name of latency tags
            clean_name = re.sub(r'\(.*?\)', '', name).strip()
            
            m_logo = re.search(r'tvg-logo="([^"]+)"', line)
            logo = m_logo.group(1).strip() if m_logo else ""
            
            # Check if logo is missing, empty, or placeholder
            is_placeholder = (
                not logo or 
                logo == "https://i.imgur.com/WpMA9kC.png" or
                logo.endswith(".m3u8") or
                "placeholder" in logo.lower()
            )
            
            if is_placeholder:
                channels_missing_logo.append((name, clean_name, logo))
            else:
                channels_with_logo.append((name, clean_name, logo))

print(f"Total entries in curated playlist: {len(channels_with_logo) + len(channels_missing_logo)}")
print(f"Entries with good logo: {len(channels_with_logo)}")
print(f"Entries missing/placeholder logo: {len(channels_missing_logo)}")
print("=" * 60)
print("Channels missing logo:")
seen = set()
for full, clean, l in channels_missing_logo:
    if clean not in seen:
        seen.add(clean)
        print(f"  • {clean} (Current: '{l}')")
