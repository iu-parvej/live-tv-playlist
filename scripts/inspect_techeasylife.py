import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://tvpro.techeasylife.com/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Downloaded {len(html)} bytes from {url}")
        
        # Look for playlist links or scripts
        scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
        print("\nScripts found:")
        for s in scripts:
            print(" ", s)
            
        links = re.findall(r'https?://[^\s"\'<>]+', html)
        relevant = [l for l in links if any(k in l.lower() for k in ['m3u', 'tsport', 'github', 'raw', 'playlist'])]
        print("\nRelevant links found:")
        for l in set(relevant):
            print(" ", l)
except Exception as e:
    print(f"Error: {e}")
