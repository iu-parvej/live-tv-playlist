import binascii
import re
import json

KEY = b"mrd81T0da__e5ue_ayco92_2_0utK6Ak6bker_3h_2d33_7_o27SSPy4tnV9"

def decrypt_hex(hex_str: str) -> str:
    try:
        raw = binascii.unhexlify(hex_str)
        decrypted = bytes([raw[i] ^ KEY[i % len(KEY)] for i in range(len(raw))])
        return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"ERROR: {e}"

channels = []
curr = {}

with open('temp/skym3u_prfj.m3u', 'r', encoding='utf-8', errors='ignore') as f:
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
                # Extract hex from /live/5e822/<HEX>.m3u8
                m_hex = re.search(r'/live/[^/]+/([a-f0-9]+)\.m3u8', line)
                if m_hex:
                    curr['real_url'] = decrypt_hex(m_hex.group(1))
                else:
                    curr['real_url'] = line
                channels.append(curr)
                curr = {}

print(f"Decrypted {len(channels)} channels:")
servers = set()
for c in channels[:30]:
    print(f"  {c['name']:30} ({c['group']:15}) -> {c['real_url']}")

for c in channels:
    m_srv = re.search(r'https?://([^/]+)/', c['real_url'])
    if m_srv:
        servers.add(m_srv.group(1))

print(f"\nUnique stream host servers ({len(servers)}):")
for s in sorted(servers):
    print(" ", s)

with open('temp/skym3u_decrypted.json', 'w', encoding='utf-8') as f:
    json.dump(channels, f, indent=2, ensure_ascii=False)
