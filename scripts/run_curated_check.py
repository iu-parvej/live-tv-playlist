import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

from test_curated_filter import (
    BD_SPORTS, BD_NEWS, BD_ENTERTAINMENT, INDIAN_NEWS_BLACKLIST,
    KOLKATA_AND_INDIAN_ENT_MOVIES, ALL_SPORTS, DOCUMENTARY, KIDS_AND_MUSIC, ISLAMIC
)

# Load streams
with open('output/playlist_multiserver.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

streams = []
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
            # Extract latency
            m_lat = re.search(r'\(.*?(?:Server \d+ - )?(\d+)ms.*?\)', curr['title'])
            curr['latency'] = int(m_lat.group(1)) if m_lat else 999
            streams.append(curr)
            curr = {}

def classify_stream(title, group):
    tl = title.lower()
    gl = group.lower()

    # 1. Check Indian news blacklist first
    for n in INDIAN_NEWS_BLACKLIST:
        if n in tl:
            return None  # Excluded

    # 2. Check BD Sports
    for s in BD_SPORTS:
        if s in tl:
            return "1. BD Sports 🇧🇩"

    # 3. Check Kolkata & Indian Entertainment & Movies
    for e in KOLKATA_AND_INDIAN_ENT_MOVIES:
        if e in tl:
            return "2. Indian & Kolkata Entertainment & Movies 🎬"

    # 4. Check All Sports
    for s in ALL_SPORTS:
        if s in tl:
            return "3. All Sports (Cricket, Football & HD) ⚽"

    # 5. Check Documentary
    for d in DOCUMENTARY:
        if d in tl:
            return "4. Documentary & Wildlife 🌍"

    # 6. Check BD News
    for n in BD_NEWS:
        if n in tl:
            return "5. BD News & National 🇧🇩"

    # 7. Check BD Entertainment
    for e in BD_ENTERTAINMENT:
        if e in tl:
            return "6. BD Entertainment & Drama 🇧🇩"

    # 8. Check Kids & Music
    for k in KIDS_AND_MUSIC:
        if k in tl:
            return "7. Music & Kids (Cartoons & Songs) 🎵"

    # 9. Check Islamic
    for i in ISLAMIC:
        if i in tl:
            return "8. Islamic & Devotional 🕌"

    return None

classified = []
for s in streams:
    cat = classify_stream(s['title'], s['group'])
    if cat:
        s['curated_category'] = cat
        classified.append(s)

print(f"Total streams matched curated criteria: {len(classified)}")
counts = Counter(s['curated_category'] for s in classified)
for cat in sorted(counts.keys()):
    print(f"  {cat}: {counts[cat]} streams")
