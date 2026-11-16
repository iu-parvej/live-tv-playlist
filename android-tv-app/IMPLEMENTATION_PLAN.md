# Premium Android TV M3U Player — Architecture & Implementation Plan

**Fixed Working Directory:** `C:\Users\Parvej Hossain\Documents\Website Work\Development Project\M3U Player App for TV`  
**Reference Repositories Analyzed:** `_reference_repos/` (`OwnTV`, `M3UAndroid`, `OpenTV`, `Quiblo`, `StreamVault-IPTV`, `m3u-lite`, `IPTV-Player`)  
**Target Playlist Ecosystem:** `live-tv-playlist` (GitHub-hosted `.m3u` URLs including `playlist_curated.m3u`, `playlist.m3u`, `playlist_bdix.m3u`, `playlist_sports.m3u`, `playlist_multiserver.m3u`)

---

## 1. Fastest & Most Reliable Tech Stack

To achieve **instant cold start**, **60/120fps D-pad scrolling**, **zero-lag channel zapping**, and **smooth playback on 1.5–2 GB RAM Android TV boxes** (such as Xiaomi Mi Box 3 / Mi Box S / Mi TV Stick):

| Layer | Technology Choice | Why It Is Fastest & Best |
| :--- | :--- | :--- |
| **Language & Runtime** | **Kotlin 2.x** (Native Android ART) | Compiles directly to native bytecode—no JavaScript bridge (React Native) and no extra C++/Skia engine startup cost (Flutter). |
| **UI Toolkit** | **Jetpack Compose for TV** (`androidx.tv:tv-material` + Compose Foundation) | Hardware-accelerated UI with native Android spatial D-pad focus engine, lazy grid virtualization, and zero XML inflation overhead. |
| **Video Engine** | **AndroidX Media3 (`ExoPlayer`)** + `media3-datasource-okhttp` (+ optional `libmpv` fallback) | Direct zero-copy `SurfaceView` (`PlayerSurface`) hardware decoding, shared HTTP socket pool, and single reusable player instance across channel switches. |
| **Networking** | **OkHttp 5** (`fastFallback` / Happy Eyeballs) | Parallel IPv4/IPv6 connection setup, HTTP `ETag`/`If-None-Match` conditional checks for GitHub raw links, and connection reuse across playlists, logos, and HLS segments. |
| **Local Storage** | **Room (SQLite)** + **DataStore Preferences** | Fast indexed SQL queries for categories/favorites/search; atomic merge-sync preserves favorites even when GitHub playlists update. |
| **Logo Caching** | **Coil 3 (`coil-compose` + `coil-network-okhttp`)** | Aggressive memory + disk caching of channel logos so large TV grids scroll without stutter or repeated network fetches. |
| **Startup Optimization** | **Baseline Profiles (`profileinstaller`)** | Pre-compiles hot Compose & Media3 paths into ART at APK install time (essential for sideloaded TV APKs that bypass Play Store cloud profiles). |
| **Licensing Note** | Clean new Kotlin codebase (inspired by MIT/Apache patterns) | Keeps full ownership of your app for private, Play Store, or commercial distribution without copyleft restrictions. |

---

## 2. Core User Flow & Feature Plan

### A. App Entry & Smart GitHub Playlist Sync
1. **Instant Launch (<1s to UI):**
   - App opens immediately with a clean branded splash/header while reading the cached Room database so channels appear instantly.
   - Simultaneously checks the active GitHub raw `.m3u` URL using conditional HTTP headers (`ETag` / `Last-Modified`).
   - If unchanged (`304 Not Modified`), zero parsing work happens.
   - If updated (`200 OK`), a **streaming line-by-line M3U parser** parses `#EXTINF` attributes (`group-title`, `tvg-id`, `tvg-name`, `tvg-logo`, `#EXTVLCOPT` headers) and performs an **atomic merge** into Room:
     - Updates channel names, logos, categories, and stream URLs.
     - **Preserves** user `Favorites`, `Last Watched Channel`, and `Recent History` using a stable channel ID (`tvg-id` + normalized name / FNV-1a URL hash).
2. **Pre-Seeded + Custom Playlists:**
   - Out-of-the-box presets pointing to your GitHub repo (`Curated VIP`, `Primary Fastest`, `BDIX Only`, `Sports Live`, `Multi-Server`), plus ability to paste/edit any custom `.m3u` / `.m3u8` URL.

### B. Premium Homepage Layout (Inspired by Your Reference Grid, Upgraded for TV)
Keeping the clean, effortless structure of your reference screenshot, redesigned as a **10-foot dark cinematic TV UI**:
1. **Top Navigation Bar:**
   - **Left:** App logo + Active Playlist name (e.g., `VIP Live TV`) + subtle sync status pill (`Updated just now` / `Updating...`).
   - **Right:** Focusable action icons: **Search**, **Sync/Refresh Now**, **Switch Playlist**, **Settings**, and **Live Clock**.
2. **Category Tabs Bar (Right Below Header):**
   - `Favorites` | `All Channels` | Dynamic categories from `group-title` (e.g., `BD Sports`, `BD News`, `BD Entertainment`, `Indian & Kolkata`, `All Sports`, `Documentary`, `Kids & Music`, `Islamic`).
   - Clear **Selected vs Focused** visual states: active tab has a glowing accent underline; focused tab highlights brightly as you move along the bar with Left/Right D-pad.
3. **Large Premium Channel Grid:**
   - **4 or 5 large tiles per row** (configurable in Settings).
   - Each card displays:
     - **Large centered Channel Logo** on a subtle neutral/glass card surface (with automatic clean monogram fallback if a logo fails to load).
     - **Bold, high-contrast Channel Name** below the logo (1–2 lines max, legible from across the living room).
     - **Subtle status badges:** Favorite star indicator, and optional server count pill (`3 Servers` when multiple streams share a channel).
   - **Premium TV Focus Effect:** Focused card smoothly scales (`1.06x`), gains a crisp `2.5dp` glowing accent border + soft drop shadow, and subtly brightens its surface.

### C. Full-Screen Auto-Play & Live Zapping
- **Single-Click Auto Fullscreen:** Pressing `OK / DPAD_CENTER` on any channel card immediately opens the full-screen player using a **single persistent `ExoPlayer` instance** (reusing decoders for near-instant channel switching).
- **Minimal Translucent OSD (Auto-hides after 4s):**
  - Channel number + Logo + Channel Name + Category + Live resolution/codec badge (e.g., `1080p • HLS`) + Current time.
- **Multi-Server / Backup Stream Handling:**
  - Since playlists like `playlist_curated.m3u` and `playlist_multiserver.m3u` list backup links (`Gazi TV HD 1`, `Gazi TV HD 2`, etc.), if Stream 1 fails or buffers endlessly, the player can offer **1-click "Next Server"** (or optional auto-failover to Server 2!).

### D. Comprehensive Android TV & Xiaomi Mi Box Remote Support
Engineered with `androidx.tv` focus routing + `Modifier.onPreviewKeyEvent` (`KeyEvent.ACTION_DOWN` / `ACTION_UP` with long-press detection) to support **Xiaomi Mi Box (Gen 1, 2, 3, Mi Box S 1st/2nd Gen, Mi TV Stick)**, **Google TV / Chromecast**, **Fire TV**, and **universal IR/Bluetooth TV remotes**:

| Context | Remote Button / Keycode | Action |
| :--- | :--- | :--- |
| **Homepage Grid** | `DPAD_UP / DOWN / LEFT / RIGHT` | Navigate smoothly across big channel tiles; pressing `UP` on top row moves to Category Tabs & Header Bar. |
| **Homepage Grid** | `DPAD_CENTER` / `ENTER` / `NUMPAD_ENTER` | Play channel immediately in Fullscreen. |
| **Homepage Grid** | Long-press `DPAD_CENTER` or `MENU` (`KEYCODE_MENU`) | Toggle Favorite / Open quick channel options. |
| **Homepage Grid** | `CHANNEL_UP` / `PAGE_UP` / `MEDIA_PLAY_PAUSE` | Resume last watched channel immediately. |
| **Homepage Grid** | `BACK` (`KEYCODE_BACK`) | Jump focus back to Top/Tabs (if scrolled down), or show clean "Exit App?" prompt (prevents accidental exits). |
| **Fullscreen Player** | `DPAD_UP` / `CHANNEL_UP` / `PAGE_UP` / `MEDIA_NEXT` | **Next Channel** (live zapping). |
| **Fullscreen Player** | `DPAD_DOWN` / `CHANNEL_DOWN` / `PAGE_DOWN` / `MEDIA_PREVIOUS` | **Previous Channel** (live zapping). |
| **Fullscreen Player** | `DPAD_LEFT` | Slide out **Quick Channel & Category Overlay** over live video so you can browse without stopping playback. |
| **Fullscreen Player** | `DPAD_RIGHT` / `MENU` / Long-press `DPAD_CENTER` | Open **Quick Player Menu** (Switch Backup Server, Aspect Ratio `Fit/Fill/16:9`, Toggle Favorite, Audio/Subtitle track). |
| **Fullscreen Player** | `DPAD_CENTER` / `MEDIA_PLAY_PAUSE` / `INFO` | Toggle OSD overlay (or Play/Pause if toggled). |
| **Fullscreen Player** | `0–9` (`KEYCODE_0`..`KEYCODE_9`) | Direct channel number entry (for remotes with number pads). |
| **Fullscreen Player** | `BACK` (`KEYCODE_BACK`) | Closes any open overlay first; second press exits Fullscreen back to Grid with focus kept on that channel. |

*Note on Xiaomi Mi Box Remotes:* Mi Box remotes are minimalist (D-pad, OK, Back, Home, Volume, Power, Voice/Apps—often without physical `CH+`/`CH-` rockers). Mapping `DPAD_UP` / `DPAD_DOWN` in fullscreen directly to Next/Previous channel + `DPAD_LEFT` to the overlay channel list ensures **100% effortless operation on every Mi Box generation**.

### E. Basic Settings Screen (TV-Friendly Modal / Screen)
Clean, uncluttered Settings layout navigable strictly via D-pad:
1. **Playlist Sources:**
   - Quick-select preset GitHub playlists (`Curated VIP`, `BDIX Only`, `Sports Live`, `Full Primary`, `Multi-Server`).
   - Custom M3U URL input (plus optional QR/local phone-typing helper or simple on-screen keyboard).
   - **Auto-Refresh on Startup** (`On` / `Off`) + **Manual Sync Now** button + Last synced timestamp.
2. **Playback & Performance:**
   - **Stream Buffer Mode:** `Fast Zap (Low Latency - Best for BDIX)` vs `Balanced` vs `High Stability (Unstable Public Streams)`.
   - **Auto-Switch Backup Server on Error:** (`On` / `Off`).
   - **Default Aspect Ratio:** `Fit` / `Fill (Crop)` / `16:9`.
   - **Playback Engine:** `Media3 ExoPlayer (Hardware)` (default, fastest) with optional `Software/Compatibility` fallback.
3. **Display & Storage:**
   - **Grid Density:** `Large (4 columns)` vs `Standard (5 columns)`.
   - **Keep Screen On During Playback** (`Always On`).
   - **Clear Logo & Playlist Cache**.

---

## 3. Visual Design System ("Premium Dark TV")

* **Background Canvas:** Deep midnight radial/vertical gradient (`#090D16` → `#111827`) to eliminate harsh OLED/LED glare in dark living rooms.
* **Surface Cards:** Translucent charcoal-slate (`#1A2233` at 85% opacity) with `14dp` rounded corners and subtle `1dp` border (`#FFFFFF` at 8% opacity).
* **Focus State:** Crisp `2.5dp` cyan/electric-blue or amber-gold accent ring (`#38BDF8` / `#60A5FA`), `1.06x` smooth spring scale, elevated surface glow.
* **Logo Container:** Soft neutral/frosted inner pad inside each tile so both dark and white channel logos remain crisp and legible.
* **Typography:** High-contrast clean sans-serif (18–20sp channel titles, 22sp category tabs, tabular digits for clock/channel numbers).

---

## 4. Proposed Folder & Module Structure

Inside `C:\Users\Parvej Hossain\Documents\Website Work\Development Project\M3U Player App for TV\`:

```text
M3U Player App for TV/
├── _reference_repos/           # Cloned open-source IPTV repos for reference
├── IMPLEMENTATION_PLAN.md      # This architecture & execution plan
└── tv-app/                     # New native Android TV Gradle project
    ├── app/
    │   ├── src/main/
    │   │   ├── AndroidManifest.xml   # LEANBACK_LAUNCHER, TV banner, uses-feature leanback
    │   │   ├── java/.../
    │   │   │   ├── data/
    │   │   │   │   ├── parser/       # Streaming M3U parser (supports #EXTINF & #EXTVLCOPT)
    │   │   │   │   ├── db/           # Room DB (ChannelEntity, PlaylistEntity, DAOs)
    │   │   │   │   ├── prefs/        # DataStore user settings
    │   │   │   │   └── repo/         # Smart ETag sync & atomic catalogue merge
    │   │   │   ├── player/           # Single reusable ExoPlayer manager + OkHttp DataSource
    │   │   │   └── ui/
    │   │   │       ├── theme/        # Premium Dark TV colors, typography, focus modifiers
    │   │   │       ├── home/         # Header + Category Tabs + Large Channel Grid + Search
    │   │   │       ├── player/       # Fullscreen Player + OSD + Quick Channel Drawer
    │   │   │       ├── settings/     # Basic TV Settings Screen
    │   │       │       └── remote/       # Universal TV / Mi Box keycode interceptor
    └── baselineprofile/              # ART AOT compilation profile for instant cold start
```

---

## 5. Step-by-Step Build Phases

1. **Phase 1 — Project Setup & Manifest (`tv-app/`):**
   - Initialize Gradle project with **Kotlin 2.x, Compose for TV (`androidx.tv:tv-material`), Media3 (`ExoPlayer` + HLS + OkHttp), Room, Coil 3, DataStore, and ProfileInstaller**.
   - Configure `LEANBACK_LAUNCHER` + TV banner icon so the app appears natively on Xiaomi Mi Box / Android TV home screens.
2. **Phase 2 — Fast M3U Engine & Smart GitHub Sync:**
   - Implement streaming `M3uParser` (handles `group-title`, `tvg-logo`, `tvg-id`, `#EXTVLCOPT`, and URL fragment cleanup).
   - Build Room entities + atomic merge-refresh + conditional `ETag` GitHub sync + pre-seeded `live-tv-playlist` URLs.
3. **Phase 3 — Premium TV Homepage & Search:**
   - Build the top bar, `Favorites` / `All Channels` / category tabs with clear Focused vs Selected states, and the **large logo + channel name grid** with Coil disk caching and 10-foot focus animations.
4. **Phase 4 — Fullscreen Player & Universal TV Remote Engine:**
   - Build single-instance `ExoPlayer` screen with auto-fullscreen, OSD, `DPAD_UP/DOWN` & `CH+/CH-` live channel zapping, `DPAD_LEFT` quick channel drawer, `DPAD_RIGHT/MENU` backup-server & aspect-ratio menu, and error/auto-failover handling.
5. **Phase 5 — Settings, Performance Tuning & Device Testing:**
   - Add Settings screen, generate Baseline Profile, build release APK, and test via ADB / Android TV emulator / Xiaomi Mi Box.
