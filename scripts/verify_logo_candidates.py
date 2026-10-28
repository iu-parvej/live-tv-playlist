import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

candidates = {
    "beIN Sports Xtra": [
        "https://upload.wikimedia.org/wikipedia/commons/9/9d/BeIN_Sports_XTRA.png",
        "https://jiotvimages.cdn.jio.com/dare_images/images/BeIN_Sports_Xtra.png",
        "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/bein-sports-xtra-us.png",
        "https://static.wikia.nocookie.net/logopedia/images/b/b5/XTRA_2.png"
    ],
    "DAZN": [
        "https://upload.wikimedia.org/wikipedia/commons/7/71/DAZN_Logo.png",
        "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/dazn-1-es.png",
        "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/dazn-1-it.png"
    ],
    "ESPN 2": [
        "https://upload.wikimedia.org/wikipedia/commons/2/2f/ESPN2_logo.png",
        "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/espn-2-us.png",
        "https://jiotvimages.cdn.jio.com/dare_images/images/ESPN2.png"
    ],
    "BTV": [
        "https://i.ibb.co.com/Q3F9JyKH/btv.png",
        "https://upload.wikimedia.org/wikipedia/commons/0/07/Bangladesh_Television_logo.png",
        "https://www.btvlive.gov.bd/images/btv-logo.png"
    ],
    "Makkah": [
        "https://upload.wikimedia.org/wikipedia/commons/3/3b/Quran_TV_Saudi.png",
        "https://i.pinimg.com/originals/de/fc/23/defc2375723ec0e5d75ad1c7595e7dce.jpg",
        "https://i.imgur.com/A2fJysM.png"
    ],
    "Madinah": [
        "https://upload.wikimedia.org/wikipedia/commons/b/b3/Sunnah_TV_Saudi.png",
        "https://i.imgur.com/A2fJysM.png",
        "https://i.ibb.co/cygNtwH/bahrain-quaran.png"
    ],
    "History": [
        "https://upload.wikimedia.org/wikipedia/commons/f/f5/History_Logo.svg",
        "https://jiotvimages.cdn.jio.com/dare_images/images/History_TV18.png"
    ],
    "DSPORTS": [
        "https://jiotvimages.cdn.jio.com/dare_images/images/Eurosport.png",
        "https://upload.wikimedia.org/wikipedia/commons/3/38/DSport_logo.png"
    ],
    "2TV Sport": [
        "https://upload.wikimedia.org/wikipedia/commons/2/23/First_Channel_%28Georgia%29_logo.png",
        "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/georgia/1tv-ge.png"
    ]
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for ch, u_list in candidates.items():
    found = False
    for u in u_list:
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    print(f"VERIFIED: {ch} -> {u} ({len(resp.read())} bytes)")
                    found = True
                    break
        except Exception:
            continue
    if not found:
        print(f"NOT FOUND: {ch}")
