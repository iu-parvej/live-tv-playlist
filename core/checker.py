"""
core/checker.py
Asynchronous, high-concurrency stream health and latency (ping) checker.
Evaluates stream playback readiness directly from local WiFi/BDIX network.
"""

import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Any, Tuple, Callable, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Checker")

BDIX_HOST_KEYWORDS = [
    "aynaott.com", "gpcdn.net", "jagobd.com", "digijadoo.net", "bioscopelive",
    "toffeebd", "103.", "bdiptv", "roar", "circle", "samonline", "dhakacolo",
    "icccommunication", "amberit", "carnival"
]

class StreamChecker:
    def __init__(
        self,
        concurrency: int = 60,
        connect_timeout: float = 2.5,
        total_timeout: float = 4.0,
        bdix_threshold_ms: int = 90,
        default_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ):
        self.concurrency = concurrency
        self.connect_timeout = connect_timeout
        self.total_timeout = total_timeout
        self.bdix_threshold_ms = bdix_threshold_ms
        self.default_user_agent = default_user_agent

    def is_likely_bdix(self, url: str, latency_ms: int) -> bool:
        if latency_ms <= self.bdix_threshold_ms:
            return True
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in BDIX_HOST_KEYWORDS)

    async def check_single_stream(
        self,
        session: aiohttp.ClientSession,
        item: Dict[str, Any],
        semaphore: asyncio.Semaphore,
        progress_cb: Optional[Callable[[bool, int, Dict[str, Any]], None]] = None
    ) -> Tuple[bool, int, str, Dict[str, Any]]:
        url = item["url"]
        item_headers = item.get("headers", {})

        headers = {
            "User-Agent": item_headers.get("User-Agent", self.default_user_agent),
            "Accept": "*/*",
            "Connection": "close"
        }
        if "Referer" in item_headers:
            headers["Referer"] = item_headers["Referer"]

        timeout = aiohttp.ClientTimeout(
            total=self.total_timeout,
            connect=self.connect_timeout
        )

        async with semaphore:
            t0 = time.perf_counter()
            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                    ssl=False
                ) as resp:
                    latency_ms = int((time.perf_counter() - t0) * 1000)

                    if resp.status in (200, 206):
                        # Read initial chunk to inspect stream headers
                        chunk = await resp.content.read(512)
                        chunk_str = chunk.decode("utf-8", errors="ignore").lower()
                        ct = resp.headers.get("Content-Type", "").lower()

                        # Rejection criteria: HTML ISP block / 404 landing pages
                        if "<!doctype html" in chunk_str or "<html" in chunk_str or "<body" in chunk_str:
                            res = (False, latency_ms, "ISP/Web Page Block", item)
                        elif (
                            "#extm3u" in chunk_str or
                            "#ext-x-" in chunk_str or
                            "<mpd" in chunk_str or
                            "application/x-mpegurl" in ct or
                            "application/vnd.apple.mpegurl" in ct or
                            "video/" in ct or
                            "octet-stream" in ct or
                            len(chunk) > 32
                        ):
                            # Verified stream
                            item["latency_ms"] = latency_ms
                            item["is_bdix"] = self.is_likely_bdix(url, latency_ms)
                            res = (True, latency_ms, f"OK ({latency_ms}ms)", item)
                        else:
                            res = (False, latency_ms, "Unrecognized Stream Content", item)
                    else:
                        res = (False, latency_ms, f"HTTP {resp.status}", item)

            except asyncio.TimeoutError:
                res = (False, 9999, "Timeout", item)
            except Exception as e:
                err_msg = str(e) or type(e).__name__
                res = (False, 9999, err_msg[:50], item)

            if progress_cb:
                progress_cb(res[0], res[1], item)

            return res

    async def check_all(
        self,
        streams: List[Dict[str, Any]],
        progress_cb: Optional[Callable[[int, int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Initiating async scan on {len(streams)} streams (Concurrency: {self.concurrency})...")
        semaphore = asyncio.Semaphore(self.concurrency)
        connector = aiohttp.TCPConnector(
            limit=self.concurrency + 10,
            ttl_dns_cache=300,
            ssl=False
        )

        completed_count = 0
        working_count = 0
        total = len(streams)

        def on_item_done(is_ok: bool, latency: int, item: Dict[str, Any]):
            nonlocal completed_count, working_count
            completed_count += 1
            if is_ok:
                working_count += 1
            if progress_cb and (completed_count % 50 == 0 or completed_count == total):
                progress_cb(completed_count, working_count, total)

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                self.check_single_stream(session, item, semaphore, on_item_done)
                for item in streams
            ]
            results = await asyncio.gather(*tasks)

        working_items = [r[3] for r in results if r[0]]
        logger.info(
            f"Scan Complete: {len(working_items)}/{total} streams verified active "
            f"({len(working_items) / max(total, 1) * 100:.1f}% success rate)."
        )
        return working_items
