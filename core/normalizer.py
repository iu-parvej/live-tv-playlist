"""
core/normalizer.py
Normalizes channel names, maps official logos and categories,
deduplicates identical channels, and orders streams by response latency (lowest ping first).
Includes strict curated VIP filter for Bangladeshi, Indian Entertainment, All Sports, Docs, Music & Kids.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Normalizer")

CLEAN_PATTERNS = [
    r'^\s*\[bdix\]\s*', r'^\s*bdix\s*[-:|]\s*', r'^\s*bd\s*[-:|]\s*',
    r'^\s*hd\s*[-:|]\s*', r'^\s*fhd\s*[-:|]\s*', r'^\s*news\s*[-:|]\s*',
    r'^\s*ent\s*[-:|]\s*', r'^\s*sports?\s*[-:|]\s*', r'^\s*pan\s*[-:|]\s*',
    r'^\s*cr\s*\|\s*', r'^\s*mov\s*\|\s*', r'^\s*mu\s*\|\s*', r'^\s*mixer\s*\|\s*',
    r'^\s*bhoj\s*\|\s*', r'^\s*in\s*\|\s*', r'^\s*en\s*\|\s*',
    r'^\s*--?live\(?', r'\)?---?$',
    r'^\s*\d+[\.\-_:]\s*',
    r'\s*\[geo-bloc?k?e?d?\]',
    r'\s*\((?:server\s*\d+\s*[-:]\s*)?\d+ms.*?\)',
    r'\s*\((?:1080p|720p|576p|480p|hd|fhd|4k|sd|ads only)\)',
    r'\s*\[(?:1080p|720p|576p|480p|hd|fhd|4k|sd)\]',
    r'\s*\|\s*(?:bdix|1080p|720p|hd|fhd|sd|4k)'
]

EMOJI_PATTERN = r'[\u2700-\u27BF]|[\uE000-\uF8FF]|[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]'

# Strict RegEx Filters for Curated VIP Playlist
RE_INDIAN_NEWS = [
    r'\baaj\s*tak\b', r'\babp\b', r'\bindia\s*tv\b', r'\brepublic\b', r'\bndtv\b',
    r'\bzee\s*(?:news|24|hindustan|bharat)\b', r'\bnews\s*18\b', r'\btv9\b',
    r'\bdd\s*news\b', r'\bwion\b', r'\bsansad\b', r'\bnews\s*nation\b', r'\bindia\s*today\b',
    r'\btimes\s*now\b', r'\bmirror\s*now\b', r'\bcnbc\s*awaz\b', r'\bkhabar\b', r'\bsamachar\b',
    r'\bpratham\s*khabar\b', r'\bkalash\s*news\b', r'\bchhattisgarh\b', r'\bmp\s*&\b'
]

RE_BD_SPORTS = [
    r'\bt[\s\-_]?sports\b',
    r'\b(?:gazi\s*tv|gtv)\b(?!\s*home|\s*garden|\s*cgtv)'
]

RE_BD_NEWS = [
    r'\bsomoy\b', r'\bjamuna\b', r'\bdbc\s*news\b', r'\b(?:ekattor|71\s*tv)\b',
    r'\bchannel\s*24\b', r'\bindependent\s*tv\b', r'\batn\s*news\b',
    r'\bbtv(?:\s*national|\s*world|\s*chattogram|\s*chittagong|\s*ctg|\s*hd)?\b',
    r'\bsangsad\b', r'\bjago\s*news\b', r'\bnews\s*21\s*bangla\b',
    r'\bnews\s*24(?:\s*hd|\s*bd|\s*television)\b'
]

RE_FOREIGN_NEWS_EXCLUDE = [
    r'\blac\b', r'\brai\b', r'\brtve\b', r'\bcity\s*news\b', r'\bitaly\b',
    r'\bfrance\b', r'\bspain\b', r'\bcanada\b', r'\bntv\s*telugu\b', r'\bashwaveega\b',
    r'\b22scope\b', r'\b4tv\b', r'\b6tv\b', r'\b99tv\b', r'\baagaaz\b', r'\baaj\s*i\s*habar\b',
    r'\bchhattisgarh\b', r'\bmp\s*&\b', r'\bbalkan\b', r'\b%8\b'
]

RE_BD_ENT = [
    r'\bchannel\s*i\b', r'\bntv(?:\s*hd|\s*bd)?\b', r'\brtv(?:\s*hd|\s*bd)?\b',
    r'\bbangla\s*vision\b', r'\bmaasranga\b', r'\bdeepto\b', r'\batn\s*bangla\b',
    r'\bnagorik\b', r'\bchannel\s*9\b', r'\bboishakhi\b', r'\bdesh\s*tv\b',
    r'\bbijoy\s*tv\b', r'\bbangla\s*tv\b', r'\bananda\s*tv\b', r'\bmohona\b',
    r'\bsa\s*tv\b', r'\bmy\s*tv(?:\s*hd|\s*bd)?\b', r'\basian\s*tv\b', r'\bsananda\s*tv\b',
    r'\bmovie\s*bangla\b'
]

RE_FOREIGN_ENT_EXCLUDE = [
    r'\bnoord\b', r'\boost\b', r'\brijnmond\b', r'\butrecht\b', r'\btoscana\b',
    r'\bnasa\b', r'\baristanis\b', r'\bfeh[eé]rv[aá]r\b', r'\bidman\b', r'\bintv\b',
    r'\bradiosa\b', r'\bsantvani\b', r'\bvissa\b', r'\beurope\b', r'\bze\b', r'\btelugu\b'
]

RE_KOLKATA_AND_INDIAN_ENT = [
    # Kolkata / Bangla
    r'\bzee\s*bangla\b', r'\bstar\s*jalsha\b', r'\bjalsha\s*movies\b', r'\bcolors\s*bangla\b',
    r'\bsony\s*aath\b', r'\baakash\s*aath\b', r'\bruposhi\s*bangla\b', r'\bdhoom\s*music\b',
    r'\bsangeet\s*bangla\b',
    # Hindi Entertainment
    r'\bstar\s*plus\b', r'\bsony\s*sab\b', r'\bsab\s*tv\b', r'\bzee\s*tv\b', r'\bcolors\s*hd\b',
    r'\bcolors\s*tv\b', r'\bsony\s*entertainment\b', r'\bset\s*india\b', r'\bstar\s*bharat\b',
    r'\b&tv\b', r'\bdangal\b', r'\bshemaroo\b', r'\bbig\s*magic\b', r'\bishara\b',
    # Movies (Hindi, South Dubbed, Regional)
    r'\bstar\s*gold\b', r'\bsony\s*max\b', r'\bzee\s*cinema\b', r'\bcolors\s*cineplex\b',
    r'\bsony\s*pix\b', r'\bzee\s*bollywood\b', r'\b&pictures\b', r'\bgoldmines\b',
    r'\bb4u\s*movies\b', r'\bbhojpuri\s*cinema\b', r'\bfilamchi\b', r'\bmanoranjan\b',
    r'\bdhinchaak\b', r'\bcinema\s*tv\b', r'\bbflix\b', r'\bmovie\s*plus\b', r'\bshubh\s*cinema\b'
]

RE_ALL_SPORTS = [
    r'\bstar\s*sports\b', r'\bsony\s*sports\b', r'\bsony\s*ten\b', r'\bten\s*[1235]\b',
    r'\bsony\s*six\b', r'\bwillow\b', r'\ba\s*sports\b', r'\bptv\s*sports\b', r'\bastro\s*cricket\b',
    r'\bbein\s*sports?\b', r'\bsky\s*sports?\b', r'\btnt\s*sports?\b', r'\bsupersport\b',
    r'\beurosport\b', r'\bfox\s*sports?\b', r'\bespn\b', r'\bdazn\b', r'\bdd\s*sports\b',
    r'\bdsports\b', r'\bcricket\b', r'\bfootball\b', r'\b2tv\s*sport\b', r'\bbahrain\s*sports\b',
    r'\bjordan\s*sports\b', r'\bmax\s*sport\b', r'\bpremier\s*sports\b', r'\bpremier\s*league\b',
    r'\bkabaddi\b'
]

RE_DOCS = [
    r'\bdiscovery\b(?!\s*kids)', r'\banimal\s*planet\b', r'\bnational\s*geographic\b', r'\bnat\s*geo\b',
    r'\bhistory\s*tv18\b', r'\bhistory\b', r'\btlc\b', r'\binvestigation\s*discovery\b',
    r'\bdiscovery\s*science\b', r'\bdiscovery\s*turbo\b', r'\bsony\s*bbc\s*earth\b',
    r'\breal\s*wild\b', r'\bwild\s*earth\b', r'\bwild\s*planet\b', r'\bwild\s*nature\b',
    r'\bautentic\s*history\b', r'\blove\s*nature\b', r'\binwild\b', r'\bdocubay\b'
]

RE_KIDS_AND_MUSIC = [
    r'\bduronto\b', r'\bcartoon\s*network\b', r'\bnickelodeon\b', r'\bnick\b', r'\bpogo\b',
    r'\bdisney\b', r'\bsony\s*yay\b', r'\bhungama\b', r'\bsonic\b', r'\bdiscovery\s*kids\b',
    r'\bgaan\s*bangla\b', r'\b9xm\b', r'\bmtv\b', r'\bb4u\s*music\b', r'\bmastiii\b',
    r'\bzing\b', r'\btrace\s*urban\b', r'\bdeluxe\s*music\b', r'\bclub\s*mtv\b',
    r'\bmtunes\b', r'\bsangeet\s*bangla\b', r'\bjungle\s*book\b', r'\bgreen\s*gold\b', r'\b9x\s*jalwa\b'
]

RE_ISLAMIC = [
    r'\bpeace\s*tv\b', r'\bmakkah\b', r'\bmadinah\b', r'\bquran\b', r'\bsunnah\b', r'\bislamic\b'
]

class ChannelNormalizer:
    def __init__(self, mapping_path: str = "config/channel_mapping.json", logo_db_path: str = "config/logo_database.json", logos_dir: str = "logos"):
        self.mapping_path = mapping_path
        self.logo_db_path = logo_db_path
        self.logos_dir = logos_dir
        self.canonical_channels = []
        self.categories = []
        self.logo_exact = {}
        self.logo_patterns = []
        self.local_logos = set()
        self.load_local_logos()
        self.load_mapping()
        self.load_logo_db()

    def load_local_logos(self):
        try:
            if os.path.isdir(self.logos_dir):
                self.local_logos = set(os.listdir(self.logos_dir))
        except Exception as e:
            logger.warning(f"Could not load local logos: {e}")

    def load_mapping(self):
        try:
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.categories = data.get("categories", [])
                self.canonical_channels = data.get("channels", [])
        except Exception as e:
            logger.warning(f"Could not load channel mapping: {e}")

    def load_logo_db(self):
        try:
            with open(self.logo_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.logo_exact = data.get("exact_matches", {})
                self.logo_patterns = data.get("keyword_patterns", [])
        except Exception as e:
            logger.warning(f"Could not load logo database: {e}")

    def resolve_logo(self, name: str, current_logo: str) -> str:
        # 1. First priority: Local verified GitHub raw logo (100% reliable, no 429/404)
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        for ext in ['png', 'jpg']:
            if f"{slug}.{ext}" in self.local_logos:
                return f"https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/logos/{slug}.{ext}"

        # 1a. Strip trailing channel index (_1, _2, _3...)
        slug_no_num = re.sub(r'_\d+$', '', slug)
        for ext in ['png', 'jpg']:
            if f"{slug_no_num}.{ext}" in self.local_logos:
                return f"https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/logos/{slug_no_num}.{ext}"

        # 1b. Strip resolution / type suffixes (_hd, _fhd, _sd, _4k, _tv)
        slug_base = re.sub(r'_(?:hd|fhd|sd|4k|tv)$', '', slug_no_num)
        for ext in ['png', 'jpg']:
            if f"{slug_base}.{ext}" in self.local_logos:
                return f"https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/logos/{slug_base}.{ext}"

        # 2. Check if current_logo is valid (reject placeholders, svg, and rate-limiting wikimedia)
        is_invalid = (
            not current_logo or
            current_logo == "https://i.imgur.com/WpMA9kC.png" or
            "placeholder" in current_logo.lower() or
            current_logo.endswith(".m3u8") or
            current_logo.endswith(".svg") or
            "upload.wikimedia.org" in current_logo.lower()
        )
        if not is_invalid:
            return current_logo

        # 3. Check exact matches in logo db
        for k, url in self.logo_exact.items():
            if k.lower() == name.lower() and not url.endswith('.svg') and "upload.wikimedia.org" not in url:
                return url

        # 4. Check keyword patterns
        nl = name.lower()
        for pat in self.logo_patterns:
            if pat["keyword"].lower() in nl:
                url = pat["logo"]
                if not url.endswith('.svg') and "upload.wikimedia.org" not in url:
                    return url

        return current_logo or "https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/logos/gazi_tv_hd.png"

    def clean_name(self, raw_name: str) -> str:
        name = raw_name
        for p in CLEAN_PATTERNS:
            name = re.sub(p, "", name, flags=re.IGNORECASE)
        name = re.sub(EMOJI_PATTERN, "", name)

        name = re.sub(r"\s+", " ", name).strip()
        nl = name.lower()

        # Strict Canonical Name Unification for Curated TV Experience
        # 1. BD Sports & News
        if re.search(r'\b(?:gazi\s*tv|gtv)\b', nl) and not re.search(r'garden|cgtv', nl):
            return "Gazi TV HD"
        if re.search(r'\bt[\s\-_]?sports\b', nl):
            return "T Sports HD"
        if re.search(r'\bsomoy\b', nl):
            return "Somoy TV HD"
        if re.search(r'\bjamuna\b', nl):
            return "Jamuna TV HD"
        if re.search(r'\b(?:ekattor|71\s*tv)\b', nl):
            return "Ekattor TV HD"
        if re.search(r'\bdbc\s*news\b', nl):
            return "DBC News HD"
        if re.search(r'\bchannel\s*24\b', nl):
            return "Channel 24 HD"
        if re.search(r'\bindependent\s*tv\b', nl):
            return "Independent TV HD"
        if re.search(r'\bnews\s*24\b', nl):
            return "News 24 HD"
        if re.search(r'\batn\s*news\b', nl):
            return "ATN News HD"
        if re.search(r'\bbtv\s*(?:chattogram|chittagong|ctg)\b', nl):
            return "BTV Chittagong HD"
        if re.search(r'\bbtv\s*world\b', nl):
            return "BTV World HD"
        if re.search(r'\bbtv\b', nl) and "world" not in nl:
            return "BTV National HD"

        # 2. BD Entertainment
        if re.search(r'\bchannel\s*i\b', nl):
            return "Channel i HD"
        if re.search(r'\bntv\b', nl) and "telugu" not in nl:
            return "NTV HD"
        if re.search(r'\brtv\b', nl):
            return "Rtv HD"
        if re.search(r'\bbangla\s*vision\b', nl):
            return "Banglavision HD"
        if re.search(r'\bmaasranga\b', nl):
            return "Maasranga TV HD"
        if re.search(r'\bdeepto\b', nl):
            return "Deepto TV HD"
        if re.search(r'\batn\s*bangla\b', nl):
            return "ATN Bangla HD"
        if re.search(r'\bnagorik\b', nl):
            return "Nagorik TV HD"
        if re.search(r'\bchannel\s*9\b', nl):
            return "Channel 9 HD"
        if re.search(r'\bboishakhi\b', nl):
            return "Boishakhi TV HD"
        if re.search(r'\bdesh\s*tv\b', nl):
            return "Desh TV HD"
        if re.search(r'\bbijoy\s*tv\b', nl):
            return "Bijoy TV HD"
        if re.search(r'\bbangla\s*tv\b', nl):
            return "Bangla TV HD"
        if re.search(r'\bananda\s*tv\b', nl):
            return "Ananda TV HD"
        if re.search(r'\basian\s*tv\b', nl):
            return "Asian TV"
        if re.search(r'\bmy\s*tv\b', nl):
            return "MY TV HD"
        if re.search(r'\bmohona\b', nl):
            return "Mohona TV"
        if re.search(r'\bsa\s*tv\b', nl):
            return "SA TV"
        if re.search(r'\bsananda\b', nl):
            return "Sananda TV"
        if re.search(r'\bmovie\s*bangla\b', nl):
            return "Movie Bangla TV"

        # 3. Kolkata & Indian Entertainment & Movies
        if re.search(r'\bzee\s*bangla\s*sonar\b', nl):
            return "Zee Bangla Sonar"
        if re.search(r'\bzee\s*bangla\b', nl):
            return "Zee Bangla HD"
        if re.search(r'\bstar\s*jalsha\b', nl):
            return "Star Jalsha HD"
        if re.search(r'\bjalsha\s*movies\b', nl):
            return "Jalsha Movies HD"
        if re.search(r'\bcolors\s*bangla\s*cinema\b', nl):
            return "Colors Bangla Cinema HD"
        if re.search(r'\bcolors\s*bangla\b', nl):
            return "Colors Bangla HD"
        if re.search(r'\bsony\s*aath\b', nl):
            return "Sony Aath"
        if re.search(r'\baakash\s*aath\b', nl):
            return "Aakash Aath"
        if re.search(r'\bruposhi\s*bangla\b', nl):
            return "Ruposhi Bangla"
        if re.search(r'\bsangeet\s*bangla\b', nl):
            return "Sangeet Bangla"
        if re.search(r'\bdhoom\s*music\b', nl):
            return "Dhoom Music"
        if re.search(r'\bzee\s*tv\b', nl):
            return "Zee TV HD"
        if re.search(r'\bcolors\b', nl) and "cineplex" not in nl and "bangla" not in nl:
            return "Colors HD"
        if re.search(r'\b(?:sony\s*entertainment|set\s*india)\b', nl):
            return "Sony Entertainment Television HD"
        if re.search(r'\b(?:sony\s*sab|sab\s*tv)\b', nl):
            return "Sony SAB HD"
        if re.search(r'\bstar\s*plus\b', nl):
            return "Star Plus HD"
        if re.search(r'\bstar\s*bharat\b', nl):
            return "Star Bharat HD"
        if re.search(r'\b&tv\b', nl):
            return "&TV HD"
        if re.search(r'\bdangal\s*2\b', nl):
            return "Dangal 2"
        if re.search(r'\bdangal\b', nl):
            return "Dangal TV"
        if re.search(r'\bshemaroo\s*tv\b', nl):
            return "Shemaroo TV"
        if re.search(r'\bshemaroo\s*josh\b', nl):
            return "Shemaroo Josh"
        if re.search(r'\bshemaroo\s*umang\b', nl):
            return "Shemaroo Umang"
        if re.search(r'\bshemaroo\s*marathi\b', nl):
            return "Shemaroo Marathi Bana"
        if re.search(r'\bbig\s*magic\b', nl):
            return "Big Magic"
        if re.search(r'\bzee\s*cinema\b', nl):
            return "Zee Cinema HD"
        if re.search(r'\bsony\s*max\s*2\b', nl):
            return "Sony MAX 2 HD"
        if re.search(r'\bsony\s*max\b', nl):
            return "Sony MAX HD"
        if re.search(r'\bstar\s*gold\s*romance\b', nl):
            return "Star Gold Romance"
        if re.search(r'\bstar\s*gold\s*2\b', nl):
            return "Star Gold 2 HD"
        if re.search(r'\bstar\s*gold\b', nl):
            return "Star Gold HD"
        if re.search(r'\bcolors\s*cineplex\s*superhits\b', nl):
            return "Colors Cineplex Superhits"
        if re.search(r'\bcolors\s*cineplex\b', nl):
            return "Colors Cineplex HD"
        if re.search(r'\bsony\s*pix\b', nl):
            return "Sony PIX HD"
        if re.search(r'\b&pictures\b', nl):
            return "&pictures HD"
        if re.search(r'\bgoldmines\s*bollywood\b', nl):
            return "Goldmines Bollywood"
        if re.search(r'\bgoldmines\s*action\b', nl):
            return "Goldmines Action"
        if re.search(r'\bgoldmines\s*movies\b', nl):
            return "Goldmines Movies"
        if re.search(r'\bgoldmines\b', nl):
            return "Goldmines"
        if re.search(r'\bb4u\s*movies\b', nl):
            return "B4U Movies"
        if re.search(r'\bbhojpuri\s*cinema\b', nl):
            return "Bhojpuri Cinema"
        if re.search(r'\bfilamchi\b', nl):
            return "Filamchi Bhojpuri"
        if re.search(r'\bmanoranjan\s*grand\b', nl):
            return "Manoranjan Grand"
        if re.search(r'\bmanoranjan\s*movies\b', nl):
            return "Manoranjan Movies"
        if re.search(r'\bmanoranjan\b', nl):
            return "Manoranjan TV"

        # 4. Sports
        if re.search(r'\bstar\s*sports\s*1\s*hindi\b', nl):
            return "Star Sports 1 Hindi HD"
        if re.search(r'\bstar\s*sports\s*1\b', nl) and "select" not in nl:
            return "Star Sports 1 HD"
        if re.search(r'\bstar\s*sports\s*2\b', nl) and "select" not in nl:
            return "Star Sports 2 HD"
        if re.search(r'\bstar\s*sports\s*select\s*1\b', nl):
            return "Star Sports Select 1"
        if re.search(r'\bstar\s*sports\s*select\s*2\b', nl):
            return "Star Sports Select 2"
        if re.search(r'\b(?:sony\s*sports\s*ten\s*1|sony\s*ten\s*1|ten\s*1)\b', nl):
            return "Sony Sports Ten 1 HD"
        if re.search(r'\b(?:sony\s*sports\s*ten\s*2|sony\s*ten\s*2|ten\s*2)\b', nl):
            return "Sony Sports Ten 2 HD"
        if re.search(r'\b(?:sony\s*sports\s*ten\s*3|sony\s*ten\s*3|ten\s*3)\b', nl):
            return "Sony Sports Ten 3 HD"
        if re.search(r'\b(?:sony\s*sports\s*ten\s*5|sony\s*ten\s*5|ten\s*5|sony\s*six)\b', nl):
            return "Sony Sports Ten 5 HD"
        if re.search(r'\bwillow\b', nl):
            return "Willow TV HD"
        if re.search(r'\ba\s*sports\b', nl):
            return "A Sports HD"
        if re.search(r'\bptv\s*sports\b', nl):
            return "PTV Sports HD"
        if re.search(r'\bbein\s*sports?\s*xtra\b', nl) or "157" in nl:
            return "beIN Sports Xtra HD"
        if re.search(r'\bbein\s*sports?\b', nl):
            return "beIN Sports HD"
        if re.search(r'\bdd\s*sports\b', nl):
            return "DD Sports"
        if re.search(r'\bdsports\b', nl) or "1sports" in nl:
            return "DSPORTS 1"
        if re.search(r'\bsky\s*sports\s*main\b', nl):
            return "Sky Sports Main Event"
        if re.search(r'\bsky\s*sports\s*cricket\b', nl):
            return "Sky Sports Cricket"
        if re.search(r'\bsky\s*sports\s*premier\b', nl):
            return "Sky Sports Premier League"
        if re.search(r'\btnt\s*sports\b', nl):
            return "TNT Sports 1"
        if re.search(r'\beurosport\b', nl):
            return "Eurosport"
        if re.search(r'\bkabaddi\b', nl):
            return "Kabaddi 24x7"

        # 5. Docs & Wildlife
        if re.search(r'\binvestigation\s*discovery\b', nl):
            return "Investigation Discovery HD"
        if re.search(r'\bdiscovery\s*channel\b', nl) or (re.search(r'\bdiscovery\b', nl) and not any(w in nl for w in ["kids", "ids", "science", "turbo", "family", "investigation"])):
            return "Discovery Channel HD"
        if re.search(r'\bdiscovery\s*(?:ids|kids)\b', nl):
            return "Discovery Kids"
        if re.search(r'\bdiscovery\s*science\b', nl):
            return "Discovery Science HD"
        if re.search(r'\bdiscovery\s*turbo\b', nl):
            return "Discovery Turbo"
        if re.search(r'\banimal\s*planet\b', nl):
            return "Animal Planet HD"
        if re.search(r'\bnational\s*geographic\b|\bnat\s*geo\b', nl) and "wild" not in nl:
            return "National Geographic HD"
        if re.search(r'\bnat\s*geo\s*wild\b', nl):
            return "Nat Geo Wild HD"
        if re.search(r'\bhistory\s*tv18\b', nl):
            return "History TV18 HD"
        if re.search(r'\btlc\b', nl):
            return "TLC HD"
        if re.search(r'\bsony\s*bbc\s*earth\b', nl):
            return "Sony BBC Earth HD"
        if re.search(r'\binvestigation\s*discovery\b', nl):
            return "Investigation Discovery HD"
        if re.search(r'\binwild\b', nl):
            return "InWild HD"
        if re.search(r'\bdocubay\b', nl):
            return "DocuBay TV"

        # 6. Kids & Music
        if re.search(r'\bduronto\b', nl):
            return "Duronto TV HD"
        if re.search(r'\bcartoon\s*network\b', nl):
            return "Cartoon Network HD"
        if re.search(r'\bjungle\s*book\b', nl):
            return "The Jungle Book"
        if re.search(r'\bgreen\s*gold\b', nl):
            return "Green Gold TV"
        if re.search(r'\b9x\s*jalwa\b', nl):
            return "9X Jalwa"
        if re.search(r'\bnickelodeon\b|\bnick\b', nl) and "sonic" not in nl:
            return "Nickelodeon HD"
        if re.search(r'\bsony\s*yay\b', nl):
            return "Sony YAY HD"
        if re.search(r'\bdisney\s*(?:jr|junior)\b', nl):
            return "Disney Junior"
        if re.search(r'\bdisney\s*channel\b|\bdisney\b', nl):
            return "Disney Channel HD"
        if re.search(r'\bsonic\b', nl):
            return "Sonic The Hedgehog"
        if re.search(r'\btrace\s*urban\b', nl):
            return "Trace Urban"
        if re.search(r'\b9xm\b', nl):
            return "9XM"
        if re.search(r'\bmtv\b', nl) and "club" not in nl:
            return "MTV India HD"
        if re.search(r'\bmastiii\b', nl):
            return "Mastiii"
        if re.search(r'\bb4u\s*music\b', nl):
            return "B4U Music"
        if re.search(r'\bgaan\s*bangla\b', nl):
            return "Gaan Bangla HD"

        # 7. Islamic
        if re.search(r'\b(?:makkah|maah)\s*live\b', nl):
            return "Makkah Live HD"
        if re.search(r'\bmadinah\s*live\b', nl):
            return "Madinah Live HD"
        if re.search(r'\bpeace\s*tv\s*bangla\b', nl):
            return "Peace TV Bangla"
        if re.search(r'\bpeace\s*tv\s*english\b', nl):
            return "Peace TV English"
        if re.search(r'\bpeace\s*tv\s*urdu\b', nl):
            return "Peace TV Urdu"
        if re.search(r'\b(?:al\s*quran|bahrain\s*quran|quran\s*radiotv|quran)\b', nl) and "radio" not in nl:
            return "Al Quran TV"

        return name

    def find_canonical(self, cleaned_name: str) -> Optional[Dict[str, Any]]:
        norm_input = re.sub(r"[^a-zA-Z0-9\u0980-\u09FF]", "", cleaned_name.lower())
        for ch in self.canonical_channels:
            c_norm = re.sub(r"[^a-zA-Z0-9\u0980-\u09FF]", "", ch["name"].lower())
            if norm_input == c_norm:
                return ch
            for alias in ch.get("aliases", []):
                a_norm = re.sub(r"[^a-zA-Z0-9\u0980-\u09FF]", "", alias.lower())
                if norm_input == a_norm:
                    return ch
        return None

    def infer_category(self, name: str, original_group: str) -> str:
        nl = name.lower()
        gl = original_group.lower()

        if any(w in nl or w in gl for w in ["cricket", "football", "sports", "sport", "fifa", "ipl", "t sports"]):
            return "⚽ Sports | Live & Cricket"
        elif any(w in nl or w in gl for w in ["news", "khabar", "samachar", "somoy", "ekattor", "jamuna", "dbc"]):
            if any(w in nl or w in gl for w in ["india", "hindi", "aaj tak", "republic", "ndtv", "zee news"]):
                return "🇮🇳 India | News"
            return "🇧🇩 BD | News"
        elif any(w in nl or w in gl for w in ["movie", "movies", "cinema", "film", "max", "pix"]):
            return "🎬 Movies | Hindi & International"
        elif any(w in nl or w in gl for w in ["natok", "drama", "zee bangla", "star jalsha", "jalsha"]):
            return "🇮🇳 India | Bengali (Kolkata)"
        elif any(w in nl or w in gl for w in ["cartoon", "kids", "pogo", "nick", "duronto", "disney"]):
            return "👶 Kids & Animation"
        elif any(w in nl or w in gl for w in ["discovery", "animal planet", "nat geo", "history", "wild"]):
            return "🌍 Documentary & Wildlife"
        elif any(w in nl or w in gl for w in ["islam", "quran", "sunnah", "makkah", "madinah", "peace tv", "religious"]):
            return "🕌 Religious & Islamic"
        elif any(w in nl or w in gl for w in ["music", "gaan", "sangeet", "beats"]):
            return "🎵 Music & Lifestyle"
        elif any(w in nl or w in gl for w in ["bangla", "bd", "dhaka"]):
            return "🇧🇩 BD | Entertainment"
        elif any(w in nl or w in gl for w in ["india", "hindi", "star", "zee", "colors", "sony"]):
            return "🇮🇳 India | Entertainment & Hindi"

        return original_group or "General"

    def classify_curated(self, title: str, group: str) -> Optional[str]:
        tl = title.lower()

        # 1. Exclude Indian News
        for p in RE_INDIAN_NEWS:
            if re.search(p, tl):
                return None

        # 2. BD Sports
        for p in RE_BD_SPORTS:
            if re.search(p, tl):
                if "tnt" in tl:
                    break
                return "1. BD Sports 🇧🇩"

        # 3. BD News (Strictly verified BD news - placed right after BD Sports)
        for p in RE_BD_NEWS:
            if re.search(p, tl):
                if any(re.search(e, tl) for e in RE_FOREIGN_NEWS_EXCLUDE):
                    continue
                return "2. BD News & National 🇧🇩"

        # 4. BD Entertainment & Drama (Strictly verified BD entertainment)
        for p in RE_BD_ENT:
            if re.search(p, tl):
                if any(re.search(e, tl) for e in RE_FOREIGN_ENT_EXCLUDE):
                    continue
                return "3. BD Entertainment & Drama 🇧🇩"

        # 5. Kolkata & Indian Entertainment & Movies
        for p in RE_KOLKATA_AND_INDIAN_ENT:
            if re.search(p, tl):
                return "4. Indian & Kolkata Entertainment & Movies 🎬"

        # 6. All Sports (Cricket, Football, Global Sports)
        for p in RE_ALL_SPORTS:
            if re.search(p, tl):
                return "5. All Sports (Cricket, Football & HD) ⚽"

        # 7. Documentary & Wildlife
        for p in RE_DOCS:
            if re.search(p, tl):
                return "6. Documentary & Wildlife 🌍"

        # 8. Music & Kids (Cartoons & Songs)
        for p in RE_KIDS_AND_MUSIC:
            if re.search(p, tl):
                if "hmtv" in tl:
                    continue
                return "7. Music & Kids (Cartoons & Songs) 🎵"

        # 9. Islamic & Devotional
        for p in RE_ISLAMIC:
            if re.search(p, tl):
                return "8. Islamic & Devotional 🕌"

        return None

    def group_and_rank(self, active_streams: List[Dict[str, Any]], max_servers: int = 4) -> List[Dict[str, Any]]:
        channel_buckets: Dict[str, Dict[str, Any]] = {}

        for item in active_streams:
            raw_title = item.get("display_name") or item.get("raw_name") or "Live Stream"
            cleaned = self.clean_name(raw_title)
            canonical = self.find_canonical(cleaned)

            if canonical:
                ch_name = canonical["name"]
                ch_category = canonical["category"]
                ch_logo = canonical.get("logo") or item.get("logo") or ""
                ch_tvg_id = canonical.get("tvg_id") or item.get("tvg_id") or ""
            else:
                ch_name = cleaned or "Live Channel"
                ch_category = self.infer_category(ch_name, item.get("group", ""))
                ch_logo = item.get("logo", "")
                ch_tvg_id = item.get("tvg_id", "")

            key = (ch_name.lower(), ch_category)
            if key not in channel_buckets:
                channel_buckets[key] = {
                    "name": ch_name,
                    "category": ch_category,
                    "logo": ch_logo,
                    "tvg_id": ch_tvg_id,
                    "streams": []
                }

            if not channel_buckets[key]["logo"] and item.get("logo"):
                channel_buckets[key]["logo"] = item["logo"]

            channel_buckets[key]["streams"].append(item)

        results = []
        for bucket in channel_buckets.values():
            bucket["logo"] = self.resolve_logo(bucket["name"], bucket["logo"])
            bucket["streams"].sort(key=lambda x: x.get("latency_ms", 9999))
            bucket["streams"] = bucket["streams"][:max_servers]
            results.append(bucket)

        def sort_key(ch):
            cat = ch["category"]
            cat_order = self.categories.index(cat) if cat in self.categories else 99
            return (cat_order, ch["name"].lower())

        results.sort(key=sort_key)
        logger.info(f"Consolidated {len(active_streams)} streams into {len(results)} distinct channels.")
        return results

    def group_and_rank_curated(self, active_streams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Builds the VIP Curated Channel list strictly following the user's categories:
        1. BD Sports 🇧🇩
        2. BD News & National 🇧🇩
        3. BD Entertainment & Drama 🇧🇩
        4. Indian & Kolkata Entertainment & Movies 🎬
        5. All Sports (Cricket, Football & HD) ⚽
        6. Documentary & Wildlife 🌍
        7. Music & Kids (Cartoons & Songs) 🎵
        8. Islamic & Devotional 🕌
        """
        curated_buckets: Dict[str, Dict[str, Any]] = {}

        for item in active_streams:
            raw_title = item.get("display_name") or item.get("raw_name") or ""
            group = item.get("group", "")
            cat = self.classify_curated(raw_title, group)
            if not cat:
                continue

            cleaned = self.clean_name(raw_title)
            canonical = self.find_canonical(cleaned)

            if canonical:
                ch_name = canonical["name"]
                ch_logo = canonical.get("logo") or item.get("logo") or ""
                ch_tvg_id = canonical.get("tvg_id") or item.get("tvg_id") or ""
            else:
                ch_name = cleaned or "Live Channel"
                ch_logo = item.get("logo", "")
                ch_tvg_id = item.get("tvg_id", "")

            # Adjust channel name if needed
            key = (ch_name.lower(), cat)
            if key not in curated_buckets:
                curated_buckets[key] = {
                    "name": ch_name,
                    "category": cat,
                    "logo": ch_logo,
                    "tvg_id": ch_tvg_id,
                    "streams": []
                }

            if not curated_buckets[key]["logo"] and item.get("logo"):
                curated_buckets[key]["logo"] = item["logo"]

            curated_buckets[key]["streams"].append(item)

        results = []
        for bucket in curated_buckets.values():
            # Resolve logo to ensure no placeholder or missing logo remains
            bucket["logo"] = self.resolve_logo(bucket["name"], bucket["logo"])
            
            # Deduplicate streams by URL
            seen_u = set()
            uniq_streams = []
            for s in bucket["streams"]:
                u = s.get("url", "").strip()
                if u and u.lower() not in seen_u:
                    seen_u.add(u.lower())
                    uniq_streams.append(s)

            # Sort streams by latency ascending (fastest first)
            uniq_streams.sort(key=lambda x: x.get("latency_ms", 9999))

            # Keep up to 4 streams for sports channels, up to 3 for BD channels, 2 for others
            if "sports" in bucket["category"].lower() or "t sports" in bucket["name"].lower():
                bucket["streams"] = uniq_streams[:4]
            elif "bd " in bucket["category"].lower():
                bucket["streams"] = uniq_streams[:3]
            else:
                bucket["streams"] = uniq_streams[:2]
            results.append(bucket)

        # Sort strictly by category numbering: 1., 2., 3., 4., 5., 6., 7., 8.
        results.sort(key=lambda ch: (ch["category"], ch["name"].lower()))
        logger.info(f"Curated {len(results)} pristine channels across 8 VIP categories.")
        return results
