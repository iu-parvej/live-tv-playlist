"""
core/generator.py
Generates clean, standardized M3U / M3U8 playlist files:
- playlist.m3u: Primary fastest stream per channel
- playlist_curated.m3u: Curated VIP Playlist (BD Sports, Kolkata/Hindi, All Sports, Docs, BD News/Ent, Music & Kids)
- playlist_multiserver.m3u: All backup servers labeled with latency
- playlist_bdix.m3u: Pure BDIX & ultra-low latency streams
- playlist_sports.m3u: Dedicated sports channels
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Generator")

class PlaylistGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _format_extinf(self, ch_name: str, category: str, logo: str, tvg_id: str) -> str:
        attrs = [f'group-title="{category}"']
        if tvg_id:
            attrs.append(f'tvg-id="{tvg_id}"')
            attrs.append(f'tvg-name="{tvg_id}"')
        else:
            attrs.append(f'tvg-name="{ch_name}"')
        if logo:
            attrs.append(f'tvg-logo="{logo}"')
        return f'#EXTINF:-1 {" ".join(attrs)},{ch_name}'

    def generate_all(
        self,
        channels: List[Dict[str, Any]],
        stats: Dict[str, Any],
        curated_channels: Optional[List[Dict[str, Any]]] = None
    ):
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        # 1. Primary Playlist (Fastest stream per channel)
        primary_lines = [
            "#EXTM3U",
            f"# Last Updated: {now_str} (Local Time)",
            "# Optimized for Android IPTV Pro / Televizo / TiviMate",
            f"# Total Active Channels: {len(channels)}",
            ""
        ]

        # 2. Multi-Server Playlist (All working links labeled)
        multi_lines = [
            "#EXTM3U",
            f"# Last Updated: {now_str} (Local Time)",
            "# Multi-Server with Ping & BDIX Indicators",
            ""
        ]

        # 3. Pure BDIX Ultra-Fast Playlist (<90ms)
        bdix_lines = [
            "#EXTM3U",
            f"# Last Updated: {now_str} (Local Time)",
            "# BDIX Ultra Low Latency Channels (<90ms)",
            ""
        ]

        # 4. Pure Sports Playlist
        sports_lines = [
            "#EXTM3U",
            f"# Last Updated: {now_str} (Local Time)",
            "# Dedicated Sports Live Playlist",
            ""
        ]

        # 5. Curated VIP Playlist (The exact categories requested)
        curated_lines = [
            "#EXTM3U",
            f"# Last Updated: {now_str} (Local Time)",
            "# Curated VIP Playlist: BD Sports, Kolkata/Hindi Ent & Movies, All Sports, Docs, BD News/Drama, Kids & Music",
            f"# Total Curated Channels: {len(curated_channels or [])}",
            ""
        ]

        bdix_count = 0
        sports_count = 0
        multi_stream_count = 0

        for ch in channels:
            name = ch["name"]
            cat = ch["category"]
            logo = ch["logo"]
            tvg_id = ch["tvg_id"]
            streams = ch.get("streams", [])

            if not streams:
                continue

            # --- Primary Playlist: Best (fastest) stream ---
            best = streams[0]
            primary_lines.append(self._format_extinf(name, cat, logo, tvg_id))
            if "User-Agent" in best.get("headers", {}):
                primary_lines.append(f'#EXTVLCOPT:http-user-agent={best["headers"]["User-Agent"]}')
            primary_lines.append(best["url"])
            primary_lines.append("")

            # --- Multi-Server Playlist ---
            for idx, s in enumerate(streams, 1):
                lat = s.get("latency_ms", 0)
                is_bdix = s.get("is_bdix", False)
                bdix_tag = " [BDIX]" if is_bdix else ""
                
                if len(streams) > 1:
                    srv_name = f"{name} (Server {idx} - {lat}ms{bdix_tag})"
                else:
                    srv_name = f"{name} ({lat}ms{bdix_tag})"

                multi_lines.append(self._format_extinf(srv_name, cat, logo, tvg_id))
                if "User-Agent" in s.get("headers", {}):
                    multi_lines.append(f'#EXTVLCOPT:http-user-agent={s["headers"]["User-Agent"]}')
                multi_lines.append(s["url"])
                multi_lines.append("")
                multi_stream_count += 1

            # --- BDIX Playlist ---
            bdix_streams = [s for s in streams if s.get("is_bdix", False)]
            if bdix_streams:
                best_bdix = bdix_streams[0]
                lat = best_bdix.get("latency_ms", 0)
                bdix_lines.append(self._format_extinf(f"{name} ({lat}ms)", cat, logo, tvg_id))
                bdix_lines.append(best_bdix["url"])
                bdix_lines.append("")
                bdix_count += 1

            # --- Sports Playlist ---
            if "sport" in cat.lower() or "cricket" in cat.lower():
                sports_lines.append(self._format_extinf(name, cat, logo, tvg_id))
                sports_lines.append(best["url"])
                sports_lines.append("")
                sports_count += 1

        # --- Build Curated VIP Playlist ---
        # Curated VIP is designed for pristine living-room TV viewing:
        # 1 clean tile per channel using the fastest verified stream, with no technical clutter in titles.
        if curated_channels:
            for ch in curated_channels:
                name = ch["name"]
                cat = ch["category"]
                logo = ch["logo"]
                tvg_id = ch["tvg_id"]
                streams = ch.get("streams", [])
                if not streams:
                    continue

                best = streams[0]
                curated_lines.append(self._format_extinf(name, cat, logo, tvg_id))
                if "User-Agent" in best.get("headers", {}):
                    curated_lines.append(f'#EXTVLCOPT:http-user-agent={best["headers"]["User-Agent"]}')
                curated_lines.append(best["url"])
                curated_lines.append("")

        # Write files
        primary_path = os.path.join(self.output_dir, "playlist.m3u")
        curated_path = os.path.join(self.output_dir, "playlist_curated.m3u")
        multi_path = os.path.join(self.output_dir, "playlist_multiserver.m3u")
        bdix_path = os.path.join(self.output_dir, "playlist_bdix.m3u")
        sports_path = os.path.join(self.output_dir, "playlist_sports.m3u")

        with open(primary_path, "w", encoding="utf-8") as f:
            f.write("\n".join(primary_lines))

        with open(curated_path, "w", encoding="utf-8") as f:
            f.write("\n".join(curated_lines))

        with open(multi_path, "w", encoding="utf-8") as f:
            f.write("\n".join(multi_lines))

        with open(bdix_path, "w", encoding="utf-8") as f:
            f.write("\n".join(bdix_lines))

        with open(sports_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sports_lines))

        # Write stats summary
        stats["channels_count"] = len(channels)
        stats["curated_channels_count"] = len(curated_channels or [])
        stats["multi_stream_count"] = multi_stream_count
        stats["bdix_channels_count"] = bdix_count
        stats["sports_channels_count"] = sports_count
        stats["last_updated"] = now_str

        stats_path = os.path.join(self.output_dir, "status.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        logger.info(f"Playlists written to '{self.output_dir}/':")
        logger.info(f"  - playlist_curated.m3u ({len(curated_channels or [])} channels)")
        logger.info(f"  - playlist.m3u ({len(channels)} channels)")
        logger.info(f"  - playlist_multiserver.m3u ({multi_stream_count} streams)")
        logger.info(f"  - playlist_bdix.m3u ({bdix_count} channels)")
        logger.info(f"  - playlist_sports.m3u ({sports_count} channels)")
