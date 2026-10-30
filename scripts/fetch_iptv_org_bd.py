import urllib.request
import json

req = urllib.request.Request(
    'https://iptv-org.github.io/api/channels.json',
    headers={'User-Agent': 'Mozilla/5.0'}
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Total channels in iptv-org: {len(data)}")
        bd = [c for c in data if c.get('country') == 'BD']
        print(f"BD channels in iptv-org: {len(bd)}")
        with open('config/iptv_org_bd.json', 'w', encoding='utf-8') as f:
            json.dump(bd, f, indent=2, ensure_ascii=False)
        for c in bd:
            print(f"{c.get('name')}: {c.get('logo')}")
except Exception as e:
    print('Error:', e)
