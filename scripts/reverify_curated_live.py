import asyncio
import aiohttp
import time
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Read existing curated playlist
channels = []
with open('output/playlist_curated.m3u', 'r', encoding='utf-8') as f:
    curr = {}
    for line in f:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            curr = {}
            m_logo = re.search(r'tvg-logo="([^"]+)"', line)
            m_grp = re.search(r'group-title="([^"]+)"', line)
            m_id = re.search(r'tvg-id="([^"]+)"', line)
            title = line.split(',')[-1].strip()
            curr['title'] = title
            curr['logo'] = m_logo.group(1) if m_logo else ''
            curr['group'] = m_grp.group(1) if m_grp else ''
            curr['tvg_id'] = m_id.group(1) if m_id else ''
        elif line.startswith('#EXTVLCOPT:'):
            if 'http-user-agent=' in line:
                curr['user_agent'] = line.split('=', 1)[-1].strip()
        elif line.startswith('http://') or line.startswith('https://'):
            if curr:
                curr['url'] = line
                channels.append(curr)
                curr = {}

print(f"Total curated streams to reverify: {len(channels)}")

async def check_channel(session, ch, sem):
    url = ch['url']
    headers = {
        'User-Agent': ch.get('user_agent') or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    timeout = aiohttp.ClientTimeout(total=4.0, connect=2.5)
    async with sem:
        t0 = time.perf_counter()
        try:
            async with session.get(url, headers=headers, timeout=timeout, ssl=False, allow_redirects=True) as resp:
                lat = int((time.perf_counter() - t0) * 1000)
                if resp.status in (200, 206):
                    chunk = await resp.content.read(512)
                    chunk_str = chunk.decode('utf-8', errors='ignore').lower()
                    if '<!doctype html' in chunk_str or '<html' in chunk_str or 'error code: 52' in chunk_str:
                        return False, lat, "HTML/Cloudflare Error", ch
                    if '#extm3u' in chunk_str or '#ext-x-' in chunk_str or len(chunk) > 32:
                        ch['live_latency'] = lat
                        return True, lat, "OK", ch
                return False, lat, f"HTTP {resp.status}", ch
        except Exception as e:
            return False, 9999, type(e).__name__, ch

async def main():
    sem = asyncio.Semaphore(40)
    async with aiohttp.ClientSession() as session:
        tasks = [check_channel(session, ch, sem) for ch in channels]
        results = await asyncio.gather(*tasks)
        
    working = [r for r in results if r[0]]
    failed = [r for r in results if not r[0]]
    
    print(f"\nReverification Results:")
    print(f"  Total Checked: {len(channels)}")
    print(f"  Working / Active: {len(working)} ({len(working)/len(channels)*100:.1f}%)")
    print(f"  Failed / Offline: {len(failed)}")
    
    if failed:
        print("\nFailed Streams:")
        for ok, lat, reason, ch in failed[:15]:
            print(f"  - [{reason}] {ch['title'][:40]} -> {ch['url'][:60]}")

if __name__ == "__main__":
    asyncio.run(main())
