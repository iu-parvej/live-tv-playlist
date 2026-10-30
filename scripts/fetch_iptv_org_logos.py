import urllib.request
import json

req = urllib.request.Request(
    'https://iptv-org.github.io/api/logos.json',
    headers={'User-Agent': 'Mozilla/5.0'}
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Total logos in iptv-org: {len(data)}")
        for x in data[:10]:
            print(x)
except Exception as e:
    print('Error:', e)
