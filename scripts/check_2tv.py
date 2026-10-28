import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    for l in f:
        if '2tv' in l.lower():
            print(repr(l.strip()))
