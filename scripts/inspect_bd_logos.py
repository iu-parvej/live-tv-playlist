import json

with open('config/channel_mapping.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total canonical channels: {len(data.get('channels', []))}")
for ch in data.get('channels', []):
    if any(k in ch.get('category', '') for k in ['BD', 'Sports', 'Kolkata', 'News', 'Movies', 'Kids']):
        print(f"[{ch.get('category')}] {ch['name']} -> {ch.get('logo')}")
