import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    # DSport / Eurosport
    ("DSPORTS", "https://i.postimg.cc/8cYLb3kY/Star-Sports-1-HD.jpg"), # fallback
    ("DSPORTS 1", "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/eurosport-in.png"),
    ("DSPORTS 2", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_EUROSPORT/images/LOGO_HD/image.png"),
    # 2TV Sport
    ("2TV Sport 1", "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/georgia/1tv-sport-ge.png"),
    ("2TV Sport 2", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Georgian_Public_Broadcaster_logo.svg/300px-Georgian_Public_Broadcaster_logo.svg.png"),
    ("2TV Sport 3", "https://i.imgur.com/A2fJysM.png"),
    # QURAN
    ("QURAN 1", "https://i.ibb.co/cygNtwH/bahrain-quaran.png"),
    ("QURAN 2", "https://i.ibb.co/2qdGPCh/Sharjahtvquran.png")
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for name, u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as r:
            print(f"OK ({r.status}): {name} -> {u} ({len(r.read())} bytes)")
    except Exception as e:
        print(f"FAILED: {name} -> {e}")
