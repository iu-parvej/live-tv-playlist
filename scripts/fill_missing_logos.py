import os
import subprocess
import json
import re

LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logos")

# Load logo map from download_all_logos
from download_all_logos import LOGO_SOURCES, slugify

missing = []
for name, url in LOGO_SOURCES.items():
    slug = slugify(name)
    ext = ".png" if ".png" in url.lower() else ".jpg"
    dest = os.path.join(LOGOS_DIR, f"{slug}{ext}")
    if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
        missing.append((name, url, dest))

print(f"Total logos in catalog: {len(LOGO_SOURCES)}")
print(f"Already downloaded: {len(LOGO_SOURCES) - len(missing)}")
print(f"Still missing: {len(missing)}")

for name, url, dest in missing:
    cmd = ["curl.exe", "-s", "-L", "--max-time", "10", url, "-o", dest]
    res = subprocess.run(cmd)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  [FIXED] {name} -> {os.path.basename(dest)} ({os.path.getsize(dest)} bytes)")
    else:
        print(f"  [STILL FAILED] {name} ({url})")
