import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
from strict_rules import (
    RE_BD_SPORTS, RE_BD_NEWS, RE_FOREIGN_NEWS_EXCLUDE,
    RE_BD_ENT, RE_FOREIGN_ENT_EXCLUDE,
    RE_INDIAN_NEWS, RE_KOLKATA_AND_INDIAN_ENT,
    RE_ALL_SPORTS, RE_DOCS, RE_KIDS_AND_MUSIC, RE_ISLAMIC
)

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
            m_lat = re.search(r'\(.*?(?:Server \d+ - )?(\d+)ms.*?\)', curr['title'])
            curr['latency'] = int(m_lat.group(1)) if m_lat else 999
            streams.append(curr)
            curr = {}

def classify(title, group):
    tl = title.lower()
    gl = group.lower()

    # 1. Exclude Indian News
    for p in RE_INDIAN_NEWS:
        if re.search(p, tl):
            return None

    # 2. BD Sports
    for p in RE_BD_SPORTS:
        if re.search(p, tl):
            return "1. BD Sports 🇧🇩"

    # 3. BD News
    for p in RE_BD_NEWS:
        if re.search(p, tl):
            # Check foreign exclude
            if any(re.search(e, tl) for e in RE_FOREIGN_NEWS_EXCLUDE):
                continue
            return "5. BD News & National 🇧🇩"

    # 4. BD Entertainment
    for p in RE_BD_ENT:
        if re.search(p, tl):
            if any(re.search(e, tl) for e in RE_FOREIGN_ENT_EXCLUDE):
                continue
            return "6. BD Entertainment & Drama 🇧🇩"

    # 5. Kolkata & Indian Entertainment & Movies
    for p in RE_KOLKATA_AND_INDIAN_ENT:
        if re.search(p, tl):
            return "2. Indian & Kolkata Entertainment & Movies 🎬"

    # 6. All Sports
    for p in RE_ALL_SPORTS:
        if re.search(p, tl):
            return "3. All Sports (Cricket, Football & HD) ⚽"

    # 7. Documentary
    for p in RE_DOCS:
        if re.search(p, tl):
            return "4. Documentary & Wildlife 🌍"

    # 8. Kids & Music
    for p in RE_KIDS_AND_MUSIC:
        if re.search(p, tl):
            return "7. Music & Kids (Cartoons & Songs) 🎵"

    # 9. Islamic
    for p in RE_ISLAMIC:
        if re.search(p, tl):
            return "8. Islamic & Devotional 🕌"

    return None

categorized = defaultdict(list)
for s in streams:
    cat = classify(s['title'], s['group'])
    if cat:
        categorized[cat].append(s)

print("\n--- RESULTS OF STRICT CLASSIFICATION ---")
for cat in sorted(categorized.keys()):
    items = categorized[cat]
    print(f"\n{cat} -> {len(items)} streams:")
    seen = set()
    for s in sorted(items, key=lambda x: x['latency']):
        # Clean title for display
        clean = re.sub(r'\(.*?\)', '', s['title']).strip()
        clean = re.sub(r'^(?:--Live\(|---Live\(|MIXER \| |CR \| |MOV \| |MU \| )', '', clean)
        clean = re.sub(r'\)$|\)---$', '', clean).strip()
        if clean not in seen:
            seen.add(clean)
            print(f"   [{s['latency']:4d}ms] {clean:<35}")
