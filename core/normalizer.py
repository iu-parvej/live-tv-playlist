"""
core/normalizer.py
Normalizes channel names, maps official logos and categories,
deduplicates identical channels, and orders streams by response latency (lowest ping first).
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
    r'\s*\((?:1080p|720p|576p|480p|hd|fhd|4k|sd)\)',
    r'\s*\[(?:1080p|720p|576p|480p|hd|fhd|4k|sd)\]',
    r'\s*\|\s*(?:bdix|1080p|720p|hd|fhd|sd|4k)',
    r'[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF]'
]

class ChannelNormalizer:
    def __init__(self, mapping_path: str = "config/channel_mapping.json"):
        self.mapping_path = mapping_path
        self.canonical_channels = []
        self.categories = []
        self.load_mapping()

    def load_mapping(self):
        try:
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.categories = data.get("categories", [])
                self.canonical_channels = data.get("channels", [])
        except Exception as e:
            logger.warning(f"Could not load channel mapping: {e}")

    def clean_name(self, raw_name: str) -> str:
        name = raw_name
        for p in CLEAN_PATTERNS:
            name = re.sub(p, "", name, flags=re.IGNORECASE)
        # Collapse multiple spaces
        return re.sub(r"\s+", " ", name).strip()

    def find_canonical(self, cleaned_name: str) -> Optional[Dict[str, Any]]:
        norm_input = re.sub(r"[^a-zA-Z0-9\u0980-\u09FF]", "", cleaned_name.lower())
        for ch in self.canonical_channels:
            # Check canonical name
            c_norm = re.sub(r"[^a-zA-Z0-9\u0980-\u09FF]", "", ch["name"].lower())
            if norm_input == c_norm:
                return ch
            # Check aliases
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

            # Bucket identifier
            key = (ch_name.lower(), ch_category)
            if key not in channel_buckets:
                channel_buckets[key] = {
                    "name": ch_name,
                    "category": ch_category,
                    "logo": ch_logo,
                    "tvg_id": ch_tvg_id,
                    "streams": []
                }

            # Update logo if current stream has a logo and bucket doesn't
            if not channel_buckets[key]["logo"] and item.get("logo"):
                channel_buckets[key]["logo"] = item["logo"]

            channel_buckets[key]["streams"].append(item)

        # Sort each channel's streams by latency ascending (fastest ping first)
        results = []
        for bucket in channel_buckets.values():
            bucket["streams"].sort(key=lambda x: x.get("latency_ms", 9999))
            # Keep up to max_servers
            bucket["streams"] = bucket["streams"][:max_servers]
            results.append(bucket)

        # Sort channels nicely by Category then Channel Name
        def sort_key(ch):
            cat = ch["category"]
            cat_order = self.categories.index(cat) if cat in self.categories else 99
            return (cat_order, ch["name"].lower())

        results.sort(key=sort_key)
        logger.info(f"Consolidated {len(active_streams)} streams into {len(results)} distinct channels.")
        return results
