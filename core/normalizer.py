"""
core/normalizer.py
Normalizes channel names, maps official logos and categories,
deduplicates identical channels, and orders streams by response latency (lowest ping first).
Includes strict curated VIP filter for Bangladeshi, Indian Entertainment, All Sports, Docs, Music & Kids.
"""

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
    r'\s*\((?:server\s*\d+\s*[-:]\s*)?\d+ms.*?\)',
    r'\s*\((?:1080p|720p|576p|480p|hd|fhd|4k|sd|ads only)\)',
    r'\s*\[(?:1080p|720p|576p|480p|hd|fhd|4k|sd)\]',
    r'\s*\|\s*(?:bdix|1080p|720p|hd|fhd|sd|4k)',
    r'[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF]'
]

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
    r'\bbanglavision\b', r'\bmaasranga\b', r'\bdeepto\b', r'\batn\s*bangla\b',
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
    r'\bjordan\s*sports\b', r'\bmax\s*sport\b', r'\bpremier\s*sports\b', r'\bpremier\s*league\b'
]

RE_DOCS = [
    r'\bdiscovery\b', r'\banimal\s*planet\b', r'\bnational\s*geographic\b', r'\bnat\s*geo\b',
    r'\bhistory\s*tv18\b', r'\bhistory\b', r'\btlc\b', r'\binvestigation\s*discovery\b',
    r'\bdiscovery\s*science\b', r'\bdiscovery\s*turbo\b', r'\bsony\s*bbc\s*earth\b',
    r'\breal\s*wild\b', r'\bwild\s*earth\b', r'\bwild\s*planet\b', r'\bwild\s*nature\b',
    r'\bautentic\s*history\b', r'\blove\s*nature\b', r'\binwild\b'
]

RE_KIDS_AND_MUSIC = [
    r'\bduronto\b', r'\bcartoon\s*network\b', r'\bnickelodeon\b', r'\bnick\b', r'\bpogo\b',
    r'\bdisney\b', r'\bsony\s*yay\b', r'\bhungama\b', r'\bsonic\b',
    r'\bgaan\s*bangla\b', r'\b9xm\b', r'\bmtv\b', r'\bb4u\s*music\b', r'\bmastiii\b',
    r'\bzing\b', r'\btrace\s*urban\b', r'\bdeluxe\s*music\b', r'\bclub\s*mtv\b',
    r'\bmtunes\b', r'\bsangeet\s*bangla\b'
]

RE_ISLAMIC = [
    r'\bpeace\s*tv\b', r'\bmakkah\b', r'\bmadinah\b', r'\bquran\b', r'\bsunnah\b', r'\bislamic\b'
]

class ChannelNormalizer:
    def __init__(self, mapping_path: str = "config/channel_mapping.json", logo_db_path: str = "config/logo_database.json"):
        self.mapping_path = mapping_path
        self.logo_db_path = logo_db_path
        self.canonical_channels = []
        self.categories = []
        self.logo_exact = {}
        self.logo_patterns = []
        self.load_mapping()
        self.load_logo_db()

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
        # If current logo is valid and not a placeholder, keep it
        is_placeholder = (
            not current_logo or
            current_logo == "https://i.imgur.com/WpMA9kC.png" or
            "placeholder" in current_logo.lower() or
            current_logo.endswith(".m3u8")
        )
        if not is_placeholder:
            return current_logo

        # Check exact matches in logo db
        for k, url in self.logo_exact.items():
            if k.lower() == name.lower():
                return url

        # Check keyword patterns
        nl = name.lower()
        for pat in self.logo_patterns:
            if pat["keyword"].lower() in nl:
                return pat["logo"]

        return current_logo or "https://i.imgur.com/WpMA9kC.png"

    def clean_name(self, raw_name: str) -> str:
        name = raw_name
        for p in CLEAN_PATTERNS:
            name = re.sub(p, "", name, flags=re.IGNORECASE)
        # Fix specific typos
        if re.search(r'\bmaah\s*live\b', name, re.I):
            name = "Makkah Live HD"
        if re.search(r'\b157\.?\s*bein\b', name, re.I):
            name = "beIN Sports Xtra HD"
        if re.search(r'\b0\.\s*sonic\b', name, re.I):
            name = "Sonic The Hedgehog"
        if re.search(r'\b0\.\s*disney\s*jr\b', name, re.I):
            name = "Disney Junior"
        if re.search(r'\b0\.\s*disney\s*channel\b', name, re.I):
            name = "Disney Channel"
        if re.search(r'\b86\.?\s*sony\s*yay\b', name, re.I):
            name = "Sony YAY HD"
        return re.sub(r"\s+", " ", name).strip()

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

        # 3. BD News (Strictly verified BD news)
        for p in RE_BD_NEWS:
            if re.search(p, tl):
                if any(re.search(e, tl) for e in RE_FOREIGN_NEWS_EXCLUDE):
                    continue
                return "5. BD News & National 🇧🇩"

        # 4. BD Entertainment & Drama (Strictly verified BD entertainment)
        for p in RE_BD_ENT:
            if re.search(p, tl):
                if any(re.search(e, tl) for e in RE_FOREIGN_ENT_EXCLUDE):
                    continue
                return "6. BD Entertainment & Drama 🇧🇩"

        # 5. Kolkata & Indian Entertainment & Movies
        for p in RE_KOLKATA_AND_INDIAN_ENT:
            if re.search(p, tl):
                return "2. Indian & Kolkata Entertainment & Movies 🎬"

        # 6. All Sports (Cricket, Football, Global Sports)
        for p in RE_ALL_SPORTS:
            if re.search(p, tl):
                return "3. All Sports (Cricket, Football & HD) ⚽"

        # 7. Documentary & Wildlife
        for p in RE_DOCS:
            if re.search(p, tl):
                return "4. Documentary & Wildlife 🌍"

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
        2. Indian & Kolkata Entertainment & Movies 🎬
        3. All Sports (Cricket, Football & HD) ⚽
        4. Documentary & Wildlife 🌍
        5. BD News & National 🇧🇩
        6. BD Entertainment & Drama 🇧🇩
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
            # Sort streams by latency ascending (fastest first)
            bucket["streams"].sort(key=lambda x: x.get("latency_ms", 9999))
            # Take the best 2 streams (primary + backup)
            bucket["streams"] = bucket["streams"][:2]
            results.append(bucket)

        # Sort strictly by category numbering: 1., 2., 3., 4., 5., 6., 7., 8.
        results.sort(key=lambda ch: (ch["category"], ch["name"].lower()))
        logger.info(f"Curated {len(results)} pristine channels across 8 VIP categories.")
        return results
