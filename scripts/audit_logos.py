import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('config/channel_mapping.json', 'r', encoding='utf-8') as f:
    channels = json.load(f)['channels']

print(f"Total canonical channels: {len(channels)}")
svg_count = 0
wiki_count = 0
for ch in channels:
    logo = ch.get('logo', '')
    name = ch.get('name', '')
    is_svg = '.svg' in logo.lower()
    is_wiki = 'wikimedia.org' in logo.lower() or 'fandom' in logo.lower()
    if is_svg:
        svg_count += 1
    if is_wiki:
        wiki_count += 1
    if is_svg or is_wiki:
        print(f"[{'SVG ' if is_svg else '    '}{'WIKI' if is_wiki else '    '}] {name:30s} -> {logo}")

print(f"\nTotal SVG logos: {svg_count}")
print(f"Total Wikimedia/Fandom logos: {wiki_count}")
