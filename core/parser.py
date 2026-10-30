"""
core/parser.py
Fetches and parses M3U/M3U8 playlists from all configured sources.
Handles EXTINF directives, custom headers, and raw URL lists.
"""

import re
import urllib.request
import json
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Parser")

SKYM3U_KEY = b"mrd81T0da__e5ue_ayco92_2_0utK6Ak6bker_3h_2d33_7_o27SSPy4tnV9"

def decrypt_skym3u_url(url: str) -> Optional[str]:
    m = re.search(r'/live/[^/]+/([a-f0-9]{32,})\.m3u8', url)
    if not m:
        return None
    try:
        raw = bytes.fromhex(m.group(1))
        decrypted = bytes([raw[i] ^ SKYM3U_KEY[i % len(SKYM3U_KEY)] for i in range(len(raw))])
        dec_url = decrypted.decode('utf-8', errors='ignore')
        if dec_url.startswith('http://') or dec_url.startswith('https://'):
            return dec_url
    except Exception:
        pass
    return None

class PlaylistParser:
    def __init__(self, sources_path: str = "config/sources.json"):
        self.sources_path = sources_path

    def load_sources(self) -> List[Dict[str, Any]]:
        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [s for s in data.get("sources", []) if s.get("enabled", True)]
        except Exception as e:
            logger.error(f"Failed to read sources config: {e}")
            return []

    def fetch_url(self, url: str, timeout: int = 12) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""

    def parse_source(self, name: str, content: str) -> List[Dict[str, Any]]:
        items = []
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        
        curr_meta: Dict[str, Any] = {}
        curr_headers: Dict[str, str] = {}

        for line in lines:
            if line.startswith("#EXTINF:"):
                curr_meta = {"source": name}
                
                # Extract tvg-name, tvg-logo, group-title, tvg-id
                m_name = re.search(r'tvg-name=["\']([^"\']+)["\']', line)
                m_logo = re.search(r'tvg-logo=["\']([^"\']+)["\']', line)
                m_group = re.search(r'group-title=["\']([^"\']+)["\']', line)
                m_id = re.search(r'tvg-id=["\']([^"\']+)["\']', line)
                
                # Channel title after the last comma
                comma_parts = line.split(",")
                title = comma_parts[-1].strip() if len(comma_parts) > 1 else ""

                curr_meta["raw_name"] = m_name.group(1).strip() if m_name else title
                curr_meta["display_name"] = title or (m_name.group(1).strip() if m_name else "Unknown")
                curr_meta["logo"] = m_logo.group(1).strip() if m_logo else ""
                curr_meta["group"] = m_group.group(1).strip() if m_group else "General"
                curr_meta["tvg_id"] = m_id.group(1).strip() if m_id else ""
            
            elif line.startswith("#EXTVLCOPT:") or line.startswith("#KODIPROP:"):
                # Handle headers like http-user-agent, http-referrer
                if "user-agent=" in line.lower():
                    val = line.split("=", 1)[-1].strip()
                    curr_headers["User-Agent"] = val
                elif "referer=" in line.lower() or "referrer=" in line.lower():
                    val = line.split("=", 1)[-1].strip()
                    curr_headers["Referer"] = val
                    
            elif line.startswith("http://") or line.startswith("https://") or line.startswith("rtmp://"):
                url = line.strip()
                # If stream url has pipe-separated headers: url|User-Agent=...
                if "|" in url:
                    stream_url, header_str = url.split("|", 1)
                    url = stream_url.strip()
                    for pair in header_str.split("&"):
                        if "=" in pair:
                            hk, hv = pair.split("=", 1)
                            curr_headers[hk.strip()] = hv.strip()

                if not curr_meta:
                    # In case of raw URL files like Sports
                    curr_meta = {
                        "source": name,
                        "raw_name": "Sports Live",
                        "display_name": "Sports Live",
                        "logo": "",
                        "group": "Sports",
                        "tvg_id": ""
                    }
                
                direct_url = decrypt_skym3u_url(url)
                if direct_url:
                    direct_meta = dict(curr_meta)
                    direct_meta["url"] = direct_url
                    direct_meta["headers"] = dict(curr_headers)
                    items.append(direct_meta)

                curr_meta["url"] = url
                curr_meta["headers"] = dict(curr_headers)
                items.append(curr_meta)

                # Reset for next entry
                curr_meta = {}
                curr_headers = {}

        return items

    def fetch_all(self) -> List[Dict[str, Any]]:
        sources = self.load_sources()
        all_streams = []
        seen_urls = set()

        for src in sources:
            name = src["name"]
            url = src["url"]
            logger.info(f"Downloading source: {name} ...")
            content = self.fetch_url(url)
            if not content:
                continue

            parsed = self.parse_source(name, content)
            new_count = 0
            for item in parsed:
                u = item["url"]
                if u not in seen_urls:
                    seen_urls.add(u)
                    all_streams.append(item)
                    new_count += 1
            logger.info(f" -> {name}: Found {len(parsed)} streams ({new_count} new unique)")

        # Load extra curated candidate streams (e.g. T Sports, GTV, BDIX sports)
        import os
        extra_path = "config/extra_streams.json"
        if os.path.exists(extra_path):
            try:
                with open(extra_path, "r", encoding="utf-8") as f:
                    extra_items = json.load(f)
                    extra_added = 0
                    for item in extra_items:
                        u = item.get("url")
                        if u and u not in seen_urls:
                            seen_urls.add(u)
                            all_streams.append(item)
                            extra_added += 1
                    logger.info(f"Added {extra_added} extra targeted candidate streams from {extra_path}.")
            except Exception as e:
                logger.warning(f"Could not load extra streams: {e}")

        logger.info(f"Total aggregated unique streams ready for testing: {len(all_streams)}")
        return all_streams
