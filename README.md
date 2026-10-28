# 📺 Live TV Playlist Fusion & BDIX Latency Optimizer

An intelligent, automated IPTV stream aggregation, verification, and latency optimization system. It merges public IPTV playlists, verifies stream playback and response times (ping) directly on your local WiFi/BDIX network, categorizes channels, ranks multiple streams by speed (lowest ping first), and automatically commits and pushes the updated playlists to GitHub for live auto-updating in **Android IPTV Pro**, **TiviMate**, **OTT Navigator**, or Smart TVs.

---

## ⚡ Why Local PC Verification is Crucial (The BDIX Advantage)

Free public IPTV playlists contain thousands of channels, but **only 20% to 35% work on any given internet connection**. More importantly:
* **BDIX Streams** (Bangladesh Internet Exchange) connect directly to local Bangladesh ISPs (AynaOTT, Jagobd, GP CDN, Digijadoo, ICC, Roar, Circle, SamOnline). They stream in full HD with **ultra-low latency (10ms - 45ms)** and **zero buffering**.
* **Cloud Blockers:** If stream verification is run on cloud servers (like GitHub Actions in the US or Europe), **100% of BDIX streams fail or get blocked** because BDIX routes only within Bangladesh.
* **The Solution:** Running this checker on your home PC verifies streams against your actual residential WiFi. It identifies all active BDIX and international streams, ranks the fastest links first, and pushes the clean result to GitHub so your Android phone and TV enjoy the ultimate streaming experience.

---

## 🚀 Key Features

1. **Multi-Source Aggregation:** Merges 15+ community playlists including TechEasyLife, Mrgify BDIX, Bugsfree BD/India, ShamimHossain, Shadmanislam, Rokon-IPTV, DrSujonPaul, and more.
2. **High-Speed Async Health & Ping Checker:** Powered by Python `aiohttp` with 60 concurrent workers to scan thousands of streams in under 2 minutes.
3. **Latency-Based Stream Sorting:** If a channel has 3 working links (e.g., Server 1: 18ms BDIX, Server 2: 45ms, Server 3: 210ms), the fastest stream is placed at the top.
4. **Smart Deduplication & Categorization:** Consolidates duplicate channel entries into clean canonical categories (BD News, BD Entertainment, Sports, Movies, India, Kids, Documentary, Islamic).
5. **Multiple Generated Playlists:**
   * `playlist.m3u`: Primary clean list (1 best, fastest stream per channel).
   * `playlist_multiserver.m3u`: Multi-server list with all working backup servers labeled with ping.
   * `playlist_bdix.m3u`: Ultra-fast BDIX channels only (<90ms latency).
   * `playlist_sports.m3u`: Dedicated Live Sports channels (Cricket, Football, HD Sports).
6. **Automated GitHub Cloud Hosting:** Commits and pushes changes to your GitHub repository automatically, giving you permanent raw links that never expire.
7. **Local Interactive Web Dashboard:** Features an embedded HLS.js video player (just like TechEasyLife) to preview and test any stream directly in your PC browser.
8. **1-Click Batch Runner & Daily Task Scheduler:** Run it manually with one click or let Windows Task Scheduler run it automatically every morning.

---

## 📱 How to Use in Android IPTV Pro / Televizo / TiviMate

1. Open **IPTV Pro** or **Televizo** on your Android smartphone, tablet, or Android TV.
2. Tap the **+** (Add) icon and select **Add URL** / **M3U Playlist**.
3. Paste the **Curated VIP Playlist** (Recommended):
   ```text
   https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_curated.m3u
   ```
4. Enter any playlist name (e.g., `VIP Live TV BD & Sports`).
5. In your IPTV player settings, turn on **"Auto-refresh playlist on start"** (or set refresh interval to 1 day).

---

### 📑 Playlists Directory & Links

| Playlist | Raw GitHub URL | Description & Categories |
| :--- | :--- | :--- |
| **Curated VIP** ⭐ *(Recommended)* | `https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_curated.m3u` | **Pristine Curation:** BD Sports, Kolkata & Indian Movies/Natok, All Sports, Docs, BD News/Natok, Music & Kids. *(Zero Indian News, Zero foreign filler)* |
| **Primary (Fastest)** | `https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist.m3u` | Full list: single fastest stream per channel (<12ms - 150ms BDIX first) |
| **Multi-Server** | `https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_multiserver.m3u` | Full channel list with backup streams labeled with ping & BDIX |
| **BDIX Only** | `https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_bdix.m3u` | Ultra-fast BDIX channels only (<90ms) |
| **Sports Live** | `https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_sports.m3u` | Dedicated sports only (Cricket, Football, HD) |

---

### 🎯 Curated VIP Playlist Category Structure

In the Curated VIP playlist, channels appear in this exact order:
1. `1. BD Sports 🇧🇩` (T Sports, GTV / Gazi TV)
2. `2. Indian & Kolkata Entertainment & Movies 🎬` (Zee Bangla, Star Jalsha, Jalsha Movies, Colors Bangla, Sony SAB, Star Plus, Zee Cinema, Sony MAX, Goldmines, Filamchi, Bhojpuri Cinema)
3. `3. All Sports (Cricket, Football & HD) ⚽` (Star Sports, Sony Sports Ten 1/2/3/5, Willow TV, A Sports, beIN Sports, Sky Sports, TNT, SuperSport)
4. `4. Documentary & Wildlife 🌍` (Discovery HD, Animal Planet HD, Nat Geo, History TV18, TLC, Real Wild)
5. `5. BD News & National 🇧🇩` (Somoy, Jamuna, DBC, Ekattor, Channel 24, Independent, BTV, ATN News)
6. `6. BD Entertainment & Drama 🇧🇩` (Channel i, NTV, Rtv, Banglavision, Maasranga, Deepto, ATN Bangla, Nagorik)
7. `7. Music & Kids (Cartoons & Songs) 🎵` (Duronto TV, Cartoon Network, Nick, Pogo, Gaan Bangla, 9XM, MTV, B4U Music, Mastiii)
8. `8. Islamic & Devotional 🕌` (Makkah Live HD, Madinah Live HD, Peace TV Bangla, Quran TV)

---

## 💻 How to Run on PC

### Option 1: 1-Click Refresh (Fastest)
Double-click `run_checker.bat`. It will:
1. Download all playlist sources.
2. Test every stream on your WiFi.
3. Generate the 4 optimized `.m3u` files.
4. Automatically commit and push to GitHub!

### Option 2: Web Dashboard & Video Player
Double-click `run_web.bat` or run:
```bash
python main.py --web
```
Open [http://localhost:8080](http://localhost:8080) in your browser to search channels, play any live stream, and trigger a refresh.

### Option 3: Command Line
```bash
# Full check and push to GitHub
python main.py

# Check locally without pushing to GitHub
python main.py --no-push

# Customize concurrency
python main.py --concurrency 80
```

---

## ⏰ Setting Up Automatic Daily Refresh

To have your PC automatically refresh the playlist every morning at 08:00 AM:
1. Right-click `setup_scheduler.bat` and select **Run as Administrator**.
2. Windows Task Scheduler will register a task named `LiveTV_Playlist_Daily_Refresh`.
3. Whenever your PC is on at 08:00 AM, it will automatically test streams and push updates to GitHub. Your Android IPTV Pro app will pick up the new streams on its next launch!

---

## ⚙️ Configuration & Customization

* **Add or Remove Sources:** Edit `config/sources.json`. Add any raw M3U / M3U8 link or GitHub raw URL.
* **Change Channel Logos / Aliases:** Edit `config/channel_mapping.json`.
* **Adjust Timeouts & Concurrency:** Edit `config/settings.json`.

---

## 📂 Project Structure

```text
D:\Website\Live TV Playlist\
├── config\
│   ├── sources.json          # Source playlist URLs
│   ├── channel_mapping.json   # Canonical channel names, aliases & logos
│   └── settings.json          # Concurrency, timeouts, GitHub config
├── core\
│   ├── parser.py             # M3U parser & URL extractor
│   ├── checker.py            # High-speed async health & ping tester
│   ├── normalizer.py         # Deduplication, categorization & ranking
│   ├── generator.py          # M3U playlist builder
│   └── publisher.py          # Git & GitHub auto-push
├── web\
│   ├── index.html            # Web dashboard & HLS.js player
│   └── server.py             # Local web server & API
├── output\
│   ├── playlist.m3u          # Primary fastest playlist
│   ├── playlist_multiserver.m3u # Multi-server backup playlist
│   ├── playlist_bdix.m3u     # BDIX only playlist (<90ms)
│   ├── playlist_sports.m3u   # Live sports playlist
│   └── status.json           # Real-time scan statistics
├── main.py                   # Main pipeline CLI
├── run_checker.bat           # 1-Click execution script
├── run_web.bat               # 1-Click web dashboard launcher
├── setup_scheduler.bat       # Daily automated scheduler
└── requirements.txt
```
