# Live TV — Native Android TV M3U Player

A fast, clean, **Retro-Light** (with **Midnight Dark** option) native Android TV & Xiaomi Mi Box M3U IPTV player built with **Kotlin + Jetpack Compose + Media3 (ExoPlayer) + Room + OkHttp + Coil**.

Pre-configured to auto-sync live playlists from [`iu-parvej/live-tv-playlist`](https://github.com/iu-parvej/live-tv-playlist).

---

## Download APK

* **Latest Release APK:** [`releases/LiveTV-v1.0.0.apk`](releases/LiveTV-v1.0.0.apk) (`3.06 MB`, minSdk 23 / Android 6.0+, supports Android TV, Xiaomi Mi Box all generations, Fire TV, and Android phones)

### Install via ADB
```bash
adb connect <TV_IP>:5555
adb install -r releases/LiveTV-v1.0.0.apk
```

---

## Features

* **Instant Startup & Conditional GitHub Sync:** Loads cached channels immediately from Room SQLite while checking GitHub raw `.m3u` updates via HTTP `ETag` (`304 Not Modified` when unchanged), preserving Favorites.
* **Zero-Delay Sports Playback & Multi-Link Auto-Recovery:**
  * Launches Link 1 immediately at `0ms` delay (`0.5s` playback buffer in Fast Zap mode) while probing backup links concurrently in the background.
  * Automatically cycles through every backup link on error or stall (`3.8s` startup watchdog).
  * Monitors active playback every 2 seconds for mid-stream freezes or buffering stalls (`6s`) and recovers automatically.
  * Automatically skips to the next channel if all links on a channel fail (no blocking error screens).
* **Minimal 10-Foot TV Interface:**
  * **Home:** Clean `Live TV` header, compact focus-safe Search pill, Settings icon, Category Tabs, and 3 full rows of flat, fast-scrolling channel cards.
  * **Fullscreen OSD:** Minimal bottom-left overlay (Channel Logo + Number + Name) for `2.5s`.
  * **Dual Themes:** **Retro Light** (Default) & **Midnight Dark** selectable in Settings.
* **Enterprise Two-Pane Settings:** Playlists & Sync (5 GitHub presets + Custom M3U URL), Playback & Recovery, Appearance & Grid.

---

## Remote Controls (Android TV & Xiaomi Mi Box)

| Screen | Button | Action |
| :--- | :--- | :--- |
| **Home Grid** | `DPAD` | Navigate channels, categories, Search, Settings |
| **Home Grid** | `OK` / `DPAD_CENTER` | Play channel immediately in fullscreen |
| **Home Grid** | Hold `OK` or `MENU` | Add / Remove Favorite |
| **Home Grid** | `CH+` / `Play-Pause` | Resume last watched channel |
| **Fullscreen** | `▲` / `CH+` / `PAGE_UP` | Next channel |
| **Fullscreen** | `▼` / `CH-` / `PAGE_DOWN` | Previous channel |
| **Fullscreen** | `◀` (`DPAD_LEFT`) | Slide-out Quick Channel Drawer |
| **Fullscreen** | `▶` / `MENU` / Hold `OK` | Stream Options (Links, Aspect Ratio, Favorite, Reload) |
| **Fullscreen** | `0–9` | Direct channel number jump |
| **Fullscreen** | `BACK` | Close drawer/menu, or return to Home Grid |

---

## Build from Source

```bash
cd tv-app
./gradlew testDebugUnitTest assembleRelease
```

Output APK: `tv-app/app/build/outputs/apk/release/app-release.apk`
