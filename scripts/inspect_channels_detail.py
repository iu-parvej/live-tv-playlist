import json
import re

from analyze_two_playlists import channels_3pks, channels_oaiu

print(f"=== SAMPLE OF 3pks.m3u (Total 850) ===")
# Show sports, kids, docs, movies
sports = [c for c in channels_3pks if 'sport' in c['name'].lower() or 'sport' in c['group'].lower()]
print(f"Sports in 3pks: {len(sports)}")
for s in sports[:15]:
    print(f"  {s['name']:30} ({s['group']:15}) -> {s['decrypted_url'][:60]}")

bd_in = [c for c in channels_3pks if any(w in c['name'].lower() for w in ['bangla', 'somoy', 'jamuna', 'star', 'zee', 'colors', 'sony', 'btv', 'ntv', 'rtv'])]
print(f"\nBD / Indian Channels in 3pks: {len(bd_in)}")
for b in bd_in[:20]:
    print(f"  {b['name']:30} ({b['group']:15}) -> {b['decrypted_url'][:60]}")

print(f"\n=== SAMPLE OF oaiu.m3u (Total 135) ===")
for c in channels_oaiu[:25]:
    print(f"  {c['name']:30} -> {c['decrypted_url'][:60]}")
