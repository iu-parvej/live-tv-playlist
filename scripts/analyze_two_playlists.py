import re
from collections import Counter
import binascii

KEY = b"mrd81T0da__e5ue_ayco92_2_0utK6Ak6bker_3h_2d33_7_o27SSPy4tnV9"

def decrypt_hex(hex_str: str) -> str:
    try:
        raw = binascii.unhexlify(hex_str)
        decrypted = bytes([raw[i] ^ KEY[i % len(KEY)] for i in range(len(raw))])
        return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"ERROR: {e}"

def analyze(tag, path):
    channels = []
    curr = {}
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                curr = {}
                m_grp = re.search(r'group-title="([^"]*)"', line)
                m_logo = re.search(r'tvg-logo="([^"]*)"', line)
                m_id = re.search(r'tvg-id="([^"]*)"', line)
                name = line.split(',')[-1].strip()
                curr['name'] = name
                curr['group'] = m_grp.group(1) if m_grp else 'Ungrouped'
                curr['logo'] = m_logo.group(1) if m_logo else ''
                curr['tvg_id'] = m_id.group(1) if m_id else ''
            elif line.startswith('http://') or line.startswith('https://'):
                if curr:
                    curr['url'] = line
                    m_hex = re.search(r'/live/[^/]+/([a-f0-9]+)\.m3u8', line)
                    if m_hex:
                        curr['decrypted_url'] = decrypt_hex(m_hex.group(1))
                    else:
                        curr['decrypted_url'] = line
                    channels.append(curr)
                    curr = {}

    print(f"\n==========================================")
    print(f" Playlist: {tag} ({path})")
    print(f" Total Channels: {len(channels)}")
    print(f"==========================================")

    groups = Counter([c['group'] for c in channels])
    print("--- Categories Breakdown ---")
    for g, cnt in groups.most_common():
        print(f"  {g:25}: {cnt} channels")

    # Check decryption sanity
    valid_dec = sum(1 for c in channels if c['decrypted_url'].startswith('http://') or c['decrypted_url'].startswith('https://'))
    print(f"\nDecryption Valid URLs: {valid_dec} / {len(channels)}")
    if valid_dec < len(channels) / 2:
        print(">>> WARNING: Key might be different! Sample decrypted:")
        for c in channels[:5]:
            print(f"  {c['name']} -> {c['decrypted_url']}")

    # Check for T Sports / GTV
    tsports = [c for c in channels if 't sports' in c['name'].lower() or 'tsports' in c['name'].lower()]
    print(f"\nT Sports Found: {len(tsports)}")
    for t in tsports:
        print(f"  Name: {t['name']:20} | Group: {t['group']:15} | Decrypted: {t['decrypted_url']}")

    gtv = [c for c in channels if 'gazi' in c['name'].lower() or 'gtv' in c['name'].lower()]
    print(f"\nGazi TV / GTV Found: {len(gtv)}")
    for g in gtv:
        print(f"  Name: {g['name']:20} | Group: {g['group']:15} | Decrypted: {g['decrypted_url']}")

    return channels

channels_3pks = analyze("3pks.m3u", "temp/skym3u_3pks.m3u")
channels_oaiu = analyze("oaiu.m3u", "temp/skym3u_oaiu.m3u")
