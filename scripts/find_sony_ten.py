import json
import urllib.request

req = urllib.request.Request(
    'https://iptv-org.github.io/api/logos.json',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    logos = json.loads(resp.read().decode('utf-8'))

for item in logos:
    cid = item.get('channel', '')
    url = item.get('url', '')
    fmt = item.get('format', '')
    if ('ten' in cid.lower() or 'sony' in cid.lower()) and 'in' in cid.lower():
        if fmt == 'PNG' and not url.endswith('.svg') and 'wikimedia' not in url:
            print(f"{cid} -> {url}")
