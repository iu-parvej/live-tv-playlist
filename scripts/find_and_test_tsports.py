import urllib.request
import re
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('config/sources.json', 'r', encoding='utf-8') as f:
    sources = json.load(f)['sources']

print('Searching all sources for any T Sports links...')
all_found = []
for s in sources:
    try:
        req = urllib.request.Request(s['url'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            lines = text.splitlines()
            for idx, l in enumerate(lines):
                if l.startswith('#EXTINF:'):
                    # Check strictly for T Sports (and not TNT or BT)
                    lower = l.lower()
                    if ('t sports' in lower or 'tsport' in lower or 't-sport' in lower) and not any(x in lower for x in ['tnt', 'bt sport', 'ct sport']):
                        for j in range(idx+1, min(idx+4, len(lines))):
                            if lines[j].startswith('http'):
                                all_found.append({
                                    'source': s['name'],
                                    'extinf': l,
                                    'url': lines[j].strip()
                                })
                                break
    except Exception as e:
        print(f"Error reading {s['name']}: {e}")

print(f"Total occurrences found across all sources: {len(all_found)}")
unique = {}
for item in all_found:
    u = item['url'].split('?@')[0].strip()
    if u not in unique:
        unique[u] = item

print(f"Total unique T Sports candidate URLs: {len(unique)}")
for u, item in unique.items():
    print(f"[{item['source']}] {item['extinf'][:50]}... -> {u}")

print("\nNow testing all unique candidate URLs...")
results = []
for u, item in unique.items():
    t0 = time.perf_counter()
    status = 'FAILED'
    lat = 9999
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            lat = int((time.perf_counter() - t0) * 1000)
            data = resp.read(256)
            text_snippet = data.decode('utf-8', errors='ignore')
            if resp.status == 200 and ('#EXT' in text_snippet or len(data) > 30) and 'error code: 523' not in text_snippet and '<!doctype html' not in text_snippet.lower():
                status = 'WORKING'
            else:
                status = f"HTTP {resp.status} (invalid content/523)"
    except Exception as e:
        status = f"ERR: {type(e).__name__}"
    print(f"{status:25s} | {lat:5d}ms | {u}")
    if status == 'WORKING':
        results.append({'url': u, 'latency': lat, 'item': item})

print(f"\nTotal Working T Sports URLs: {len(results)}")
for r in results:
    print(f"-> {r['latency']}ms: {r['url']}")
