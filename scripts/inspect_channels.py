import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

channels = []
with open('output/playlist.m3u', 'r', encoding='utf-8') as f:
    curr_inf = {}
    for line in f:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            curr_inf = {}
            m_grp = re.search(r'group-title="([^"]+)"', line)
            m_logo = re.search(r'tvg-logo="([^"]+)"', line)
            m_id = re.search(r'tvg-id="([^"]+)"', line)
            name = line.split(',')[-1].strip()
            curr_inf['name'] = name
            curr_inf['group'] = m_grp.group(1) if m_grp else ""
            curr_inf['logo'] = m_logo.group(1) if m_logo else ""
            curr_inf['tvg_id'] = m_id.group(1) if m_id else ""
        elif line.startswith('http://') or line.startswith('https://'):
            if curr_inf:
                curr_inf['url'] = line
                channels.append(curr_inf)
                curr_inf = {}

print(f"Total active channels loaded: {len(channels)}")

# Let's inspect BD channels
bd_keywords = ['somoy', 'jamuna', 'dbc', 'ekattor', 'channel 24', 'independent', 'news 24', 'btv', 'channel i', 'ntv', 'rtv', 'banglavision', 'maasranga', 'deepto', 'nagorik', 't sports', 'gazi', 'gtv', 'bijoy', 'desh tv', 'boishakhi', 'ananda', 'bangla tv', 'gaan bangla', 'duronto']
found_bd = []
for c in channels:
    for kw in bd_keywords:
        if kw in c['name'].lower():
            found_bd.append(c)
            break

print(f"\n--- Found BD Channels: {len(found_bd)} ---")
for c in found_bd[:25]:
    print(f"  [{c['group']}] {c['name']} -> {c['url'][:60]}")

# Let's inspect Sports channels
sports = [c for c in channels if any(k in c['name'].lower() for k in ['sports', 'cricket', 'football', 'willow', 'bein', 'sky sport', 'sony ten', 'star sport', 't sports', 'a sports', 'ptv sport'])]
print(f"\n--- Found Sports Channels: {len(sports)} ---")
for c in sports[:25]:
    print(f"  [{c['group']}] {c['name']} -> {c['url'][:60]}")

# Let's inspect Kolkata / Bengali channels
kolkata = [c for c in channels if any(k in c['name'].lower() for k in ['zee bangla', 'jalsha', 'colors bangla', 'sony aath', 'aakash aath', 'ruposhi', 'dhoom'])]
print(f"\n--- Found Kolkata / Indian Bangla Channels: {len(kolkata)} ---")
for c in kolkata:
    print(f"  [{c['group']}] {c['name']} -> {c['url'][:60]}")

# Let's inspect Documentary channels
doc = [c for c in channels if any(k in c['name'].lower() for k in ['discovery', 'nat geo', 'national geographic', 'animal planet', 'history', 'tlc', 'wild'])]
print(f"\n--- Found Documentary Channels: {len(doc)} ---")
for c in doc[:25]:
    print(f"  [{c['group']}] {c['name']} -> {c['url'][:60]}")
