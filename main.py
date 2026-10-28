"""
main.py
Main entrypoint for BDIX & Live TV Stream Fusion & Optimizer.
Usage:
    python main.py                  # Full check, generate playlists, push to GitHub
    python main.py --no-push        # Check & generate locally without GitHub push
    python main.py --web            # Start local interactive web dashboard
"""

import sys
import time
import argparse
import logging
from typing import Dict, Any

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from core.parser import PlaylistParser
from core.checker import StreamChecker
from core.normalizer import ChannelNormalizer
from core.generator import PlaylistGenerator
from core.publisher import GitHubPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Main")

def run_pipeline(auto_push: bool = True, concurrency: int = 60) -> Dict[str, Any]:
    t_start = time.time()
    print("=" * 65)
    print(" 🚀 BDIX & LIVE TV STREAM FUSION & LATENCY OPTIMIZER")
    print("=" * 65)

    # 1. Parse Sources
    parser = PlaylistParser()
    raw_streams = parser.fetch_all()
    if not raw_streams:
        logger.error("No streams found from any sources. Please check internet connection or sources.json.")
        return {}

    # 2. Check Streams
    checker = StreamChecker(concurrency=concurrency)
    
    def on_progress(done: int, working: int, total: int):
        pct = (done / max(total, 1)) * 100
        print(f"\r🔍 Testing: {done}/{total} ({pct:.1f}%) | Active Working: {working}", end="", flush=True)

    print("\nStarting stream verification on local WiFi / BDIX...")
    active_streams = asyncio_run(checker.check_all(raw_streams, progress_cb=on_progress))
    print("\n")

    if not active_streams:
        logger.warning("No active streams detected.")
        return {}

    # 3. Normalize & Deduplicate & Rank by Latency
    normalizer = ChannelNormalizer()
    channels = normalizer.group_and_rank(active_streams)

    # Calculate statistics
    avg_latency = int(sum(s.get("latency_ms", 0) for s in active_streams) / max(len(active_streams), 1))
    bdix_streams = [s for s in active_streams if s.get("is_bdix", False)]

    stats = {
        "total_sources_scanned": len(parser.load_sources()),
        "total_unique_streams_tested": len(raw_streams),
        "total_active_streams": len(active_streams),
        "total_bdix_streams": len(bdix_streams),
        "average_latency_ms": avg_latency,
        "success_rate_percent": round(len(active_streams) / max(len(raw_streams), 1) * 100, 1),
        "execution_time_sec": round(time.time() - t_start, 1)
    }

    # 4. Generate Output Playlists
    generator = PlaylistGenerator()
    generator.generate_all(channels, stats)

    # 5. Push to GitHub
    github_urls = None
    if auto_push:
        publisher = GitHubPublisher()
        github_urls = publisher.commit_and_push(stats)

    # Print Summary Report
    print("\n" + "=" * 65)
    print(" 📊 VERIFICATION & OPTIMIZATION REPORT")
    print("=" * 65)
    print(f"Total Sources Checked:      {stats['total_sources_scanned']}")
    print(f"Total Candidate Streams:    {stats['total_unique_streams_tested']:,}")
    print(f"Active Working Streams:     {stats['total_active_streams']:,} ({stats['success_rate_percent']}%)")
    print(f"Ultra-Fast BDIX Streams:    {stats['total_bdix_streams']:,}")
    print(f"Unique Curated Channels:    {len(channels)}")
    print(f"Average Response Latency:   {stats['average_latency_ms']} ms")
    print(f"Time Taken:                 {stats['execution_time_sec']} seconds")
    print("-" * 65)
    print("📁 Generated Local Playlists:")
    print("   • output/playlist.m3u              (Primary - 1 best stream per channel)")
    print("   • output/playlist_multiserver.m3u  (Multi-Server - Backup streams labeled)")
    print("   • output/playlist_bdix.m3u         (Ultra-Fast BDIX channels only)")
    print("   • output/playlist_sports.m3u       (Live Sports only)")

    if github_urls:
        print("\n🌐 Cloud URLs for Android IPTV Pro / TiviMate:")
        print(f"   ► Primary Playlist URL:\n     {github_urls['primary']}")
        print(f"   ► Multi-Server Playlist URL:\n     {github_urls['multiserver']}")
        print(f"   ► BDIX Playlist URL:\n     {github_urls['bdix']}")
        print(f"   ► Sports Playlist URL:\n     {github_urls['sports']}")
    print("=" * 65)

    return stats

def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live TV Stream Fusion & Optimizer")
    parser.add_argument("--no-push", action="store_true", help="Skip pushing to GitHub")
    parser.add_argument("--concurrency", type=int, default=60, help="Async concurrency limit")
    parser.add_argument("--web", action="store_true", help="Launch local web UI dashboard")
    args = parser.parse_args()

    if args.web:
        from web.server import start_web_server
        start_web_server()
    else:
        run_pipeline(auto_push=not args.no_push, concurrency=args.concurrency)
