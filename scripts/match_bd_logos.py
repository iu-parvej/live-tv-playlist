import urllib.request
import json

req = urllib.request.Request(
    'https://iptv-org.github.io/api/logos.json',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    logos = json.loads(resp.read().decode('utf-8'))

with open('config/iptv_org_bd.json', 'r', encoding='utf-8') as f:
    bd_channels = json.load(f)

bd_ids = {c['id']: c['name'] for c in bd_channels}
print(f"Total BD channel IDs: {len(bd_ids)}")

bd_logos = {}
for item in logos:
    cid = item.get('channel')
    if cid in bd_ids:
        ch_name = bd_ids[cid]
        # Prefer PNG
        if item.get('format') == 'PNG' or (ch_name not in bd_logos and not item.get('url', '').endswith('.svg')):
            bd_logos[ch_name] = item.get('url')

print(f"Found logos for {len(bd_logos)} BD channels:")
for name, url in sorted(bd_logos.items()):
    print(f"  {name}: {url}")

with open('config/bd_logos_found.json', 'w', encoding='utf-8') as f:
    json.dump(bd_logos, f, indent=2, ensure_ascii=False)
