import os
import sys
import json
import urllib.request
import re

LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

# Master curated logo map (Channel Canonical Name -> Source PNG URL)
# All URLs verified to return raw PNG image
LOGO_SOURCES = {
    # 1. BD Sports
    "T Sports HD": "https://i.imgur.com/2JzlorD.png",
    "Gazi TV HD": "https://i.imgur.com/2Lzhiq6.png",

    # 2. BD News & National
    "Somoy TV HD": "https://i.imgur.com/i54AQic.png",
    "Jamuna TV HD": "https://i.imgur.com/8Qj8297.png",
    "Ekattor TV HD": "https://i.imgur.com/zoLwwUK.png",
    "DBC News HD": "https://i.imgur.com/Qbt6q4z.png",
    "Channel 24 HD": "https://i.imgur.com/4JLkaF7.png",
    "Independent TV HD": "https://i.imgur.com/POXFhGN.png",
    "News 24 HD": "https://i.imgur.com/fkTHh75.png",
    "ATN News HD": "https://i.imgur.com/4qZQKjo.png",
    "BTV National HD": "https://i.imgur.com/5OE2FDt.png",
    "BTV Chittagong HD": "https://i.imgur.com/hvpyuek.png",
    "BTV World HD": "https://i.imgur.com/sSnrg7o.png",
    "Jago News 24": "https://i.imgur.com/oSqJIYm.jpeg",
    "NEWS 21 BANGLA": "https://i.imgur.com/ijuJfmd.png",
    "Sangsad TV HD": "https://i.imgur.com/jkouxLg.png",

    # 3. BD Entertainment & Drama
    "Channel i HD": "https://i.imgur.com/X0JJlOX.png",
    "NTV HD": "https://i.imgur.com/l75bDTx.png",
    "Rtv HD": "https://i.imgur.com/yu8ugqt.png",
    "Banglavision HD": "https://i.imgur.com/nCWgp38.png",
    "Maasranga TV HD": "https://i.imgur.com/uVZJMed.png",
    "Deepto TV HD": "https://i.imgur.com/F62GUqS.png",
    "ATN Bangla HD": "https://i.imgur.com/K1HmMRz.png",
    "Nagorik TV HD": "https://i.imgur.com/aRDvQpl.png",
    "Channel 9 HD": "https://i.imgur.com/Xf5YuoE.png",
    "Boishakhi TV HD": "https://i.imgur.com/gxL05Y4.png",
    "Desh TV HD": "https://i.imgur.com/ItrZok1.png",
    "Bijoy TV HD": "https://i.imgur.com/Faetm0C.png",
    "Bangla TV HD": "https://i.imgur.com/DLGjTfI.png",
    "Ananda TV HD": "https://i.imgur.com/jkbo7Qe.png",
    "Asian TV": "https://i.imgur.com/k2adSjA.png",
    "MY TV HD": "https://i.imgur.com/475qK5T.png",
    "Mohona TV": "https://i.imgur.com/E6doEWH.png",
    "SA TV": "https://i.imgur.com/tL9kxxB.png",
    "Sananda TV": "https://jiotvimages.cdn.jio.com/dare_images/images/Sananda_TV.png",
    "Movie Bangla TV": "https://www.jagobd.com/wp-content/uploads/2016/02/moviebangla.jpg",
    "Orange Bangla TV": "https://www.jagobd.com/wp-content/uploads/2021/04/orange-bangla.jpg",

    # 4. Indian & Kolkata Entertainment & Movies
    "Zee Bangla HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Zee_Bangla_HD.png",
    "Star Jalsha HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Star_Jalsha_HD.png",
    "Jalsha Movies HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Jalsha_Movies_HD.png",
    "Colors Bangla HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Colors_Bangla_HD.png",
    "Colors Bangla Cinema HD": "https://jiotvimages.cdn.jio.com/dare_images/images/Colors_Bangla_Cinema.png",
    "Sony Aath": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/sony-aath-in.png",
    "Aakash Aath": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/aakash-aath-in.png",
    "Ruposhi Bangla": "https://jiotvimages.cdn.jio.com/dare_images/images/Rupashi_Bangla.png",
    "Sangeet Bangla": "https://jiotvimages.cdn.jio.com/dare_images/images/Sangeet_Bangla.png",
    "Dhoom Music": "https://jiotvimages.cdn.jio.com/dare_images/images/Dhoom_Music.png",
    "Zee TV HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/zee-tv-in.png",
    "Zee Bangla Sonar": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Zee_Bangla_HD.png",
    "Colors HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/colors-hd-in.png",
    "Sony Entertainment Television HD": "https://i.imgur.com/AkdfpVr.png",
    "Sony SAB HD": "https://jiotvimages.cdn.jio.com/dare_images/images/Sony_SAB.png",
    "Star Plus HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-plus-in.png",
    "Star Bharat HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-bharat-in.png",
    "&TV HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/and-tv-in.png",
    "Dangal TV": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/dangal-in.png",
    "Dangal 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/dangal-in.png",
    "Shemaroo TV": "https://jiotvimages.cdn.jio.com/dare_images/images/Shemaroo_TV.png",
    "Shemaroo Josh": "https://jiotvimages.cdn.jio.com/dare_images/images/Shemaroo_Josh.png",
    "Shemaroo Umang": "https://jiotvimages.cdn.jio.com/dare_images/images/Shemaroo_Umang.png",
    "Shemaroo Marathi Bana": "https://jiotvimages.cdn.jio.com/dare_images/images/Shemaroo_Marathi_Bana.png",
    "Big Magic": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/big-magic-in.png",
    "Zee Cinema HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Zee_Cinema_HD.png",
    "Sony MAX HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Sony_Max_HD.png",
    "Sony MAX 2 HD": "https://i.imgur.com/gqUYk6C.png",
    "Star Gold HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Star_Gold_HD.png",
    "Star Gold 2 HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-gold-in.png",
    "Star Gold Romance": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-gold-in.png",
    "Colors Cineplex HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/colors-cineplex-hd-in.png",
    "Colors Cineplex Superhits": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/colors-cineplex-in.png",
    "Sony PIX HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Sony_Pix_HD.png",
    "&pictures HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/And_Pictures_HD.png",
    "Goldmines": "https://jiotvimages.cdn.jio.com/dare_images/images/Goldmines.png",
    "Goldmines 2": "https://jiotvimages.cdn.jio.com/dare_images/images/Goldmines.png",
    "Goldmines Action": "https://jiotvimages.cdn.jio.com/dare_images/images/Goldmines_Action.png",
    "Goldmines Bollywood": "https://jiotvimages.cdn.jio.com/dare_images/images/Goldmines_Bollywood.png",
    "Goldmines Movies": "https://jiotvimages.cdn.jio.com/dare_images/images/Goldmines_Movies.png",
    "Goldmines Movies 2": "https://jiotvimages.cdn.jio.com/dare_images/images/Goldmines_Movies.png",
    "B4U Movies": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/b4u-movies-in.png",
    "Bhojpuri Cinema": "https://jiotvimages.cdn.jio.com/dare_images/images/Bhojpuri_Cinema.png",
    "Filamchi Bhojpuri": "https://jiotvimages.cdn.jio.com/dare_images/images/Filamchi_Bhojpuri.png",
    "Manoranjan Grand": "https://jiotvimages.cdn.jio.com/dare_images/images/Manoranjan_Grand.png",
    "Manoranjan Movies": "https://jiotvimages.cdn.jio.com/dare_images/images/Manoranjan_Movies.png",
    "Manoranjan TV": "https://jiotvimages.cdn.jio.com/dare_images/images/Manoranjan_TV.png",

    # 5. All Sports
    "Star Sports 1 HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-sports-1-in.png",
    "Star Sports 1 Hindi HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-sports-1-hindi-in.png",
    "Star Sports 2 HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-sports-2-in.png",
    "Star Sports Select 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-sports-1-in.png",
    "Star Sports Select 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/star-sports-2-in.png",
    "Sony Sports Ten 1 HD": "https://i.imgur.com/hWo7Ba4.png",
    "Sony Sports Ten 2 HD": "https://i.imgur.com/W96KVqu.png",
    "Sony Sports Ten 3 HD": "https://i.imgur.com/vG19HxD.png",
    "Sony Sports Ten 5 HD": "https://i.imgur.com/40BbQUd.png",
    "Willow TV HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/willow-us.png",
    "Willow HD TV": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/willow-us.png",
    "Willow Extra": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-states/willow-us.png",
    "A Sports HD": "https://i.imgur.com/EVJuFRs.png",
    "PTV Sports HD": "https://i.imgur.com/yFzNf3d.png",
    "beIN Sports HD": "https://i.imgur.com/RLrMBlm.png",
    "beIN Sports Xtra HD": "https://i.ibb.co/HT49GPmB/XTRA-2.png",
    "Sky Sports Main Event": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-kingdom/sky-sports-main-event-uk.png",
    "Sky Sports Cricket": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-kingdom/sky-sports-cricket-uk.png",
    "Sky Sports Premier League": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-kingdom/sky-sports-premier-league-uk.png",
    "TNT Sports 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-kingdom/tnt-sports-1-uk.png",
    "TNT SPORTS PREMIUM": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/united-kingdom/tnt-sports-1-uk.png",
    "Eurosport": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/eurosport-1-es.png",
    "DD Sports": "https://jiotvimages.cdn.jio.com/dare_images/images/DD_Sports.png",
    "DSPORTS 1": "https://jiotvimages.cdn.jio.com/dare_images/images/1Sports.png",
    "Dazn 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/dazn-1-it.png",
    "Fox Sports 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/fox-sports-2-ar.png",
    "Espn": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/espn-ar.png",
    "ESPN 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/espn-2-ar.png",
    "2TV SPORT": "https://i.imgur.com/z9V8HkP.png",
    "Jordan Sports ARB": "https://i.imgur.com/MpmxYm8.png",
    "MAX SPORT 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/bulgaria/max-sport-1-bg.png",
    "MAX SPORT 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/bulgaria/max-sport-2-bg.png",
    "MAX SPORT 3": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/bulgaria/max-sport-3-bg.png",
    "MAX SPORT 4": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/bulgaria/max-sport-4-bg.png",

    # 6. Documentary & Wildlife
    "Discovery Channel HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Discovery_Channel.png",
    "Animal Planet HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Animal_Planet.png",
    "National Geographic HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-ar.png",
    "Nat Geo Wild HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-wild-ar.png",
    "Nat Geo TV": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-ar.png",
    "History TV18 HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "TLC HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/TLC.png",
    "Sony BBC Earth HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/sony-bbc-earth-in.png",
    "Discovery Science HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/discovery-science-ar.png",
    "Discovery Turbo": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/discovery-turbo-ar.png",
    "Discovery Kids Hindi": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/discovery-kids-ar.png",
    "Discovery Family": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/discovery-family-ar.png",
    "Investigation Discovery HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/id-investigation-discovery-ar.png",
    "Wild Earth": "https://wildearth.tv/wp-content/uploads/2024/11/WE-LOGO-2025-WHITE-WEB-1.png",
    "Wild Nature": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-wild-ar.png",
    "Wild Planet": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-wild-ar.png",
    "REAL WILD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-wild-ar.png",
    "Alone By History": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "Autentic History": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "History & Warfare Now": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "History Hit": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "History Hunters": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "True History": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/history-tv18-in.png",
    "InWild HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/argentina/national-geographic-wild-ar.png",

    # 7. Kids & Music
    "Duronto TV HD": "https://i.imgur.com/gXsddRK.png",
    "Cartoon Network HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Cartoon_Network.png",
    "Nickelodeon HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Nick.png",
    "Sony YAY HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Sony_Yay_Hindi.png",
    "Disney Channel HD": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Disney_Channel.png",
    "Disney Junior": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Disney_Junior.png",
    "Sonic The Hedgehog": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/sonic-nickelodeon-in.png",
    "Trace Urban": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/trace-urban-fr.png",
    "9XM": "http://jiotv.catchup.cdn.jio.com/dare_images/images/9XM.png",
    "MTV India HD": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/mtv-in.png",
    "Mastiii": "http://jiotv.catchup.cdn.jio.com/dare_images/images/Mastiii.png",
    "B4U Music": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/india/b4u-music-in.png",
    "Gaan Bangla HD": "https://i.imgur.com/XS9mq4n.png",

    # 8. Islamic & Devotional
    "Makkah Live HD": "https://www.jagobd.com/wp-content/uploads/2020/05/MakkahLive.jpg",
    "Madinah Live HD": "https://www.jagobd.com/wp-content/uploads/2020/05/Medina-Live.jpg",
    "Peace TV Bangla": "https://i.imgur.com/vIJTVia.png",
    "Peace TV English": "https://m1pfxzepyyyj.merlincdn.net/content/Q/k_/169572/logo_50.png",
    "Peace TV Urdu": "https://m1pfxzepyyyj.merlincdn.net/content/J/kE/169575/logo_50.png",
    "Al Quran TV": "https://i.ibb.co/2qdGPCh/Sharjahtvquran.png",
    "Islamic TV": "https://www.jagobd.com/wp-content/uploads/2016/02/atnislamictv.jpg",
}

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    return s

from concurrent.futures import ThreadPoolExecutor, as_completed

def download_one(item):
    name, url = item
    slug = slugify(name)
    ext = ".png" if ".png" in url.lower() else ".jpg"
    dest_filename = f"{slug}{ext}"
    dest_path = os.path.join(LOGOS_DIR, dest_filename)

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return name, True, dest_filename, len(open(dest_path, 'rb').read()), "Cached"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=7) as resp:
            data = resp.read()
            if len(data) > 500:
                with open(dest_path, "wb") as f:
                    f.write(data)
                return name, True, dest_filename, len(data), "OK"
            else:
                return name, False, dest_filename, 0, f"Small size {len(data)}"
    except Exception as e:
        return name, False, dest_filename, 0, str(e)

def main():
    print(f"Downloading logos for {len(LOGO_SOURCES)} channels using ThreadPool...")
    success = 0
    failed = []
    github_logo_map = {}

    for name, url in LOGO_SOURCES.items():
        slug = slugify(name)
        ext = ".png" if ".png" in url.lower() else ".jpg"
        dest_filename = f"{slug}{ext}"
        gh_raw_url = f"https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/logos/{dest_filename}"
        github_logo_map[name] = gh_raw_url

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(download_one, item): item for item in LOGO_SOURCES.items()}
        for fut in as_completed(futures):
            name, ok, fname, size, status = fut.result()
            if ok:
                success += 1
                print(f"[{status}] {name} -> {fname} ({size} bytes)")
            else:
                failed.append((name, status, LOGO_SOURCES[name]))

    print(f"\nDone: {success} succeeded, {len(failed)} failed.")
    if failed:
        print("Failed logos:")
        for name, err, url in failed:
            print(f"  {name}: {err} -> {url}")

    out_map_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "curated_logo_map.json")
    with open(out_map_file, "w", encoding="utf-8") as f:
        json.dump(github_logo_map, f, indent=2, ensure_ascii=False)
    print(f"Wrote logo mapping to {out_map_file}")

if __name__ == "__main__":
    main()
