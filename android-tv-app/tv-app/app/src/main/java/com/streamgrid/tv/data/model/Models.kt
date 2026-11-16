package com.streamgrid.tv.data.model

import kotlinx.serialization.Serializable

@Serializable
data class StreamServer(
    val label: String,
    val url: String,
    val userAgent: String? = null,
    val referrer: String? = null,
)

data class Channel(
    val id: String,
    val number: Int,
    val name: String,
    val category: String,
    val logoUrl: String?,
    val tvgId: String?,
    val servers: List<StreamServer>,
    val isFavorite: Boolean = false,
    val lastWatchedMillis: Long = 0L,
    val sortOrder: Int = 0,
)

@Serializable
data class PlaylistPreset(
    val id: String,
    val name: String,
    val url: String,
    val description: String,
    val isCustom: Boolean = false,
)

object DefaultPlaylists {
    val presets: List<PlaylistPreset> = listOf(
        PlaylistPreset(
            id = "curated_vip",
            name = "Curated VIP (BD & Sports)",
            url = "https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_curated.m3u",
            description = "BD Sports, News, Entertainment, Indian Movies, All Sports, Docs, Kids & Islamic",
        ),
        PlaylistPreset(
            id = "primary_fastest",
            name = "Primary (Fastest Stream)",
            url = "https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist.m3u",
            description = "Full channel list with single fastest stream per channel",
        ),
        PlaylistPreset(
            id = "bdix_only",
            name = "BDIX Ultra-Fast",
            url = "https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_bdix.m3u",
            description = "Low-latency local Bangladesh BDIX streams (<90ms)",
        ),
        PlaylistPreset(
            id = "sports_live",
            name = "Sports Live HD",
            url = "https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_sports.m3u",
            description = "Dedicated live Cricket, Football, and HD Sports channels",
        ),
        PlaylistPreset(
            id = "multiserver",
            name = "Full Multi-Server",
            url = "https://raw.githubusercontent.com/iu-parvej/live-tv-playlist/main/playlist_multiserver.m3u",
            description = "All channels with backup servers and ping labels",
        ),
    )
}

enum class BufferPreset(
    val title: String,
    val subtitle: String,
    val minBufferMs: Int,
    val maxBufferMs: Int,
    val bufferForPlaybackMs: Int,
    val bufferForPlaybackAfterRebufferMs: Int,
) {
    FAST_ZAP(
        title = "Fast Zap (Sports & BDIX)",
        subtitle = "Instant start (~0.5s buffer), built for live sports & BDIX",
        minBufferMs = 3_500,
        maxBufferMs = 15_000,
        bufferForPlaybackMs = 500,
        bufferForPlaybackAfterRebufferMs = 1_200,
    ),
    BALANCED(
        title = "Balanced",
        subtitle = "Smooth playback with moderate buffering (~2.5s buffer)",
        minBufferMs = 15_000,
        maxBufferMs = 45_000,
        bufferForPlaybackMs = 2_500,
        bufferForPlaybackAfterRebufferMs = 4_000,
    ),
    HIGH_STABILITY(
        title = "High Stability",
        subtitle = "Larger buffer (~5s) for slower or unstable public streams",
        minBufferMs = 25_000,
        maxBufferMs = 60_000,
        bufferForPlaybackMs = 5_000,
        bufferForPlaybackAfterRebufferMs = 7_500,
    ),
}

enum class AspectRatioMode(val title: String) {
    FIT("Fit Screen"),
    FILL("Fill / Zoom"),
    RATIO_16_9("16:9 Widescreen"),
    RATIO_4_3("4:3 Classic"),
}

enum class AppThemeMode(val title: String, val subtitle: String) {
    RETRO_LIGHT("Retro Light (Default)", "Warm cream studio console with broadcast vermilion accents"),
    MIDNIGHT_DARK("Midnight Dark", "Deep obsidian cinema canvas with electric cyan accents"),
}

sealed interface SyncStatus {
    data object Idle : SyncStatus
    data class Checking(val message: String = "Checking playlist updates...") : SyncStatus
    data class Updated(val channelCount: Int, val fromCache: Boolean = false) : SyncStatus
    data class Error(val message: String) : SyncStatus
}
