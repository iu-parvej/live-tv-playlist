"""
auto_daily_sync.py
Automated daily synchronization & self-healing pipeline for Live TV Playlists.

Workflow:
1. Audits current 'playlist_curated.m3u':
   - Tests every channel stream live on WiFi/BDIX.
   - Categorizes each as HEALTHY or BROKEN.
2. Downloads fresh manifests from ALL configured sources:
   - 3 dynamic SkyM3U playlists (prfj, oaiu, 3pks) with auto-XOR decryption.
   - All GitHub BDIX and sports playlists in config/sources.json.
   - Extra streams in config/extra_streams.json.
3. Finds and verifies replacement streams for any broken channels.
4. Generates all 5 playlists with:
   - Icon-free clean category names (Televizo / IPTV Pro ready).
   - Official GitHub-hosted logos.
   - Numbered failover channels (1, 2, 3).
5. Automatically commits and pushes changes to GitHub.
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.parser import PlaylistParser, decrypt_skym3u_url
from core.checker import StreamChecker
from core.normalizer import ChannelNormalizer
from core.generator import PlaylistGenerator
from core.publisher import GitHubPublisher

async def audit_curated_playlist(
    curated_path: str = "playlist_curated.m3u",
    concurrency: int = 50,
    timeout_sec: float = 3.5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Tests all streams currently in playlist_curated.m3u in parallel."""
    if not os.path.exists(curated_path):
        return [], []

    entries = []
    with open(curated_path, 'r', encoding='utf-8') as f:
        curr = {}
        for line in f:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                curr = {}
                m_logo = re.search(r'tvg-logo="([^"]+)"', line)
                m_grp = re.search(r'group-title="([^"]+)"', line)
                m_id = re.search(r'tvg-id="([^"]+)"', line)
                title = line.split(',')[-1].strip()
                curr['name'] = title
                curr['display_name'] = title
                curr['raw_name'] = title
                curr['logo'] = m_logo.group(1) if m_logo else ''
                curr['group'] = m_grp.group(1) if m_grp else ''
                curr['tvg_id'] = m_id.group(1) if m_id else ''
            elif line.startswith('http://') or line.startswith('https://'):
                if curr:
                    curr['url'] = line
                    entries.append(curr)
                    curr = {}

    print(f"[*] Auditing {len(entries)} channels currently in Curated VIP playlist...")
    checker = StreamChecker(concurrency=concurrency, total_timeout=timeout_sec)
    active_results = await checker.check_all(entries)

    healthy_urls = set(s['url'].lower() for s in active_results)
    healthy = []
    broken = []

    for item in entries:
        if item['url'].lower() in healthy_urls:
            # Match latency
            for act in active_results:
                if act['url'].lower() == item['url'].lower():
                    item['latency_ms'] = act.get('latency_ms', 100)
                    item['is_bdix'] = act.get('is_bdix', False)
                    break
            healthy.append(item)
        else:
            broken.append(item)

    return healthy, broken

def run_daily_sync(auto_push: bool = True, concurrency: int = 60):
    t_start = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    print("=" * 70)
    print(f" 🔄 AUTO DAILY PLAYLIST SYNC & SELF-HEALING [{now_str}]")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1: Audit Current Curated Playlist
    # -------------------------------------------------------------
    print("\n[Step 1/5] Checking health of existing Curated VIP playlist...")
    healthy_curated, broken_curated = asyncio.run(audit_curated_playlist(concurrency=concurrency))
    print(f"  ✓ Healthy channels playing: {len(healthy_curated)}")
    print(f"  ✗ Broken / unresponsive:    {len(broken_curated)}")
    if broken_curated:
        print("  Broken channel sample:")
        for b in broken_curated[:5]:
            print(f"    - {b['name']} ({b['url'][:60]})")

    # -------------------------------------------------------------
    # Step 2: Fetch Fresh Streams from ALL Sources
    # -------------------------------------------------------------
    print("\n[Step 2/5] Downloading fresh manifests from ALL sources...")
    print("  (Includes SkyM3U prfj, oaiu, 3pks + All GitHub & BDIX playlists)")
    parser = PlaylistParser()
    raw_streams = parser.fetch_all()
    print(f"  Total raw candidate streams aggregated: {len(raw_streams):,}")

    # Also include existing multiserver streams as fallback pool
    existing_fallback = []
    multi_path = "output/playlist_multiserver.m3u"
    if os.path.exists(multi_path):
        with open(multi_path, 'r', encoding='utf-8') as f:
            curr = {}
            for line in f:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    curr = {}
                    m_logo = re.search(r'tvg-logo="([^"]+)"', line)
                    m_grp = re.search(r'group-title="([^"]+)"', line)
                    title = line.split(',')[-1].strip()
                    curr['display_name'] = title
                    curr['raw_name'] = title
                    curr['logo'] = m_logo.group(1) if m_logo else ''
                    curr['group'] = m_grp.group(1) if m_grp else ''
                elif line.startswith('http://') or line.startswith('https://'):
                    if curr:
                        curr['url'] = line
                        existing_fallback.append(curr)
                        curr = {}

    # Merge candidates deduplicating by URL
    seen_urls = set()
    combined_candidates = []
    for s in raw_streams + existing_fallback:
        u = s.get('url', '').strip()
        if u and u.lower() not in seen_urls:
            seen_urls.add(u.lower())
            combined_candidates.append(s)

    # -------------------------------------------------------------
    # Step 3: Test Streams Live on Local Connection
    # -------------------------------------------------------------
    print(f"\n[Step 3/5] Verifying {len(combined_candidates):,} unique candidate streams live...")
    checker = StreamChecker(concurrency=concurrency, total_timeout=4.0)

    def on_progress(done: int, working: int, total: int):
        pct = (done / max(total, 1)) * 100
        print(f"\r🔍 Testing: {done}/{total} ({pct:.1f}%) | Active Working: {working}", end="", flush=True)

    active_streams = asyncio.run(checker.check_all(combined_candidates, progress_cb=on_progress))
    print("\n")
    print(f"  ✓ Active working streams verified: {len(active_streams):,}")

    # Prioritize dedicated T-SPORTS-FULL-HD stream at 50ms BDIX
    for s in active_streams:
        if "T-SPORTS-FULL-HD" in s['url']:
            s['latency_ms'] = 50
            s['is_bdix'] = True
            s['display_name'] = "T Sports HD"
            s['raw_name'] = "T Sports HD"

    # -------------------------------------------------------------
    # Step 4: Normalize, Deduplicate, Number Backups & Order
    # -------------------------------------------------------------
    print("\n[Step 4/5] Normalizing categories, logos, and numbered backups...")
    normalizer = ChannelNormalizer()
    channels = normalizer.group_and_rank(active_streams)
    curated_channels = normalizer.group_and_rank_curated(active_streams)

    print(f"  ✓ Total Full Channel Groups:  {len(channels)}")
    print(f"  ✓ VIP Curated Channel Groups: {len(curated_channels)}")

    # Load existing status
    stats_path = "output/status.json"
    stats = {}
    if os.path.exists(stats_path):
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        except Exception:
            pass

    stats["total_sources_scanned"] = len(parser.load_sources())
    stats["total_unique_streams_tested"] = len(combined_candidates)
    stats["total_active_streams"] = len(active_streams)
    stats["execution_time_sec"] = round(time.time() - t_start, 1)

    # Generate playlists
    generator = PlaylistGenerator()
    generator.generate_all(channels, stats, curated_channels=curated_channels)

    # Sync output to root
    publisher = GitHubPublisher()
    publisher.sync_output_to_root()
    print("  ✓ Playlists written to disk and synchronized to root.")

    # -------------------------------------------------------------
    # Step 5: Git Commit & Auto-Push to GitHub
    # -------------------------------------------------------------
    if auto_push:
        print("\n[Step 5/5] Pushing latest verified updates to GitHub...")
        repaired_count = len(broken_curated)
        commit_msg = f"Auto-Sync: {len(active_streams)} streams active, {len(curated_channels)} VIP channels [{now_str}]"
        
        urls = publisher.commit_and_push(stats)
        print("  ✓ Successfully pushed to GitHub repository!")
        print(f"  ► Curated VIP Playlist: {urls.get('curated')}")
    else:
        print("\n[Step 5/5] Skipped GitHub push (--no-push active).")

    print("\n" + "=" * 70)
    print(f" 🎉 DAILY SYNC COMPLETED SUCCESSFULLY IN {round(time.time() - t_start, 1)} SECONDS!")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto Daily Sync & Self-Healing Pipeline")
    parser.add_argument("--no-push", action="store_true", help="Do not push changes to GitHub")
    parser.add_argument("--concurrency", type=int, default=60, help="Async concurrent workers")
    args = parser.parse_args()

    run_daily_sync(auto_push=not args.no_push, concurrency=args.concurrency)
