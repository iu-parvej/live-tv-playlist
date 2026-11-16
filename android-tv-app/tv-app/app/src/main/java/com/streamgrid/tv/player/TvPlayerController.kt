package com.streamgrid.tv.player

import android.content.Context
import android.net.Uri
import android.os.SystemClock
import androidx.annotation.OptIn
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.VideoSize
import androidx.media3.common.util.UnstableApi
import androidx.media3.datasource.okhttp.OkHttpDataSource
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.DefaultRenderersFactory
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import com.streamgrid.tv.data.model.BufferPreset
import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.data.model.StreamServer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.cancel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

data class PlaybackUiState(
    val channel: Channel? = null,
    val serverIndex: Int = 0,
    val isBuffering: Boolean = false,
    val isPlaying: Boolean = false,
    val videoWidth: Int = 0,
    val videoHeight: Int = 0,
    val latencyMs: Long? = null,
    val serverLatenciesMs: Map<Int, Long> = emptyMap(),
    val statusNote: String? = null,
    val offlineError: String? = null,
) {
    val currentServer: StreamServer?
        get() = channel?.servers?.getOrNull(serverIndex)
}

/**
 * Zero-delay ExoPlayer controller optimized for instant sports/IPTV zapping:
 * 1. Starts playing Link 1 immediately at 0ms delay while probing backups in the background.
 * 2. Tries every available link one-by-one (fastest backups first) on error or stall.
 * 3. Monitors mid-stream freezes/buffering stalls continuously and recovers automatically.
 * 4. If all links for a channel fail, invokes [onAllLinksFailed] so the app skips to the next channel.
 */
@OptIn(UnstableApi::class)
class TvPlayerController(
    private val context: Context,
    private val okHttpClient: OkHttpClient,
    private var bufferPreset: BufferPreset = BufferPreset.FAST_ZAP,
    private var autoFailover: Boolean = true,
    private val onChannelPlaying: () -> Unit = {},
    private val onAllLinksFailed: () -> Unit = {},
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val _state = MutableStateFlow(PlaybackUiState())
    val state: StateFlow<PlaybackUiState> = _state.asStateFlow()

    private var player: ExoPlayer? = null
    private var currentPreset: BufferPreset = bufferPreset
    private val defaultUserAgent =
        "Mozilla/5.0 (Linux; Android 13; MiBox) AppleWebKit/537.36 StreamGridTV/1.0"
    private val okHttpDataSourceFactory = OkHttpDataSource.Factory(okHttpClient)
        .setUserAgent(defaultUserAgent)

    private val probeClient: OkHttpClient by lazy {
        okHttpClient.newBuilder()
            .connectTimeout(1800, TimeUnit.MILLISECONDS)
            .readTimeout(1800, TimeUnit.MILLISECONDS)
            .callTimeout(2200, TimeUnit.MILLISECONDS)
            .build()
    }

    private var backupProbeJob: Job? = null
    private var startupWatchdogJob: Job? = null
    private var midStreamHealthJob: Job? = null

    private var rankedOrder: List<Int> = emptyList()
    private val triedServerIndices = mutableSetOf<Int>()
    private var stablePlaybackSinceMs: Long = 0L

    fun getOrCreatePlayer(): ExoPlayer {
        val existing = player
        if (existing != null) return existing

        val loadControl = buildLoadControl(currentPreset)
        val renderersFactory = DefaultRenderersFactory(context).apply {
            setExtensionRendererMode(DefaultRenderersFactory.EXTENSION_RENDERER_MODE_PREFER)
            setEnableDecoderFallback(true)
        }

        return ExoPlayer.Builder(context, renderersFactory)
            .setLoadControl(loadControl)
            .setMediaSourceFactory(DefaultMediaSourceFactory(okHttpDataSourceFactory))
            .build()
            .apply {
                playWhenReady = true
                videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT
                addListener(playerListener)
            }
            .also { player = it }
    }

    fun updateSettings(preset: BufferPreset, failover: Boolean) {
        autoFailover = failover
        if (preset != currentPreset) {
            currentPreset = preset
            val activeChannel = _state.value.channel
            val activeServer = _state.value.serverIndex
            releasePlayerOnly()
            if (activeChannel != null) {
                playExactServer(activeChannel, activeServer, resetTried = true)
            }
        }
    }

    fun playChannel(channel: Channel, serverIndex: Int? = null) {
        backupProbeJob?.cancel()
        startupWatchdogJob?.cancel()
        midStreamHealthJob?.cancel()
        triedServerIndices.clear()
        stablePlaybackSinceMs = 0L

        val servers = channel.servers
        if (servers.isEmpty()) {
            onAllLinksFailed()
            return
        }

        val startIdx = (serverIndex ?: 0).coerceIn(0, servers.lastIndex)
        rankedOrder = servers.indices.toList()

        // Start playback immediately at 0ms delay on Link 1 (or requested index)
        playExactServer(channel, startIdx, resetTried = true)

        // Probe backup links in the background so failover picks the fastest healthy backup
        if (serverIndex == null && servers.size > 1) {
            backupProbeJob = scope.launch {
                val backupIndices = servers.indices.filter { it != startIdx }
                val probeResults = withContext(Dispatchers.IO) {
                    probeBackupServers(servers, backupIndices)
                }
                if (_state.value.channel?.id != channel.id) return@launch

                val latencies = probeResults.mapNotNull { (idx, ms) -> ms?.let { idx to it } }.toMap()
                val sortedBackups = probeResults
                    .sortedWith(
                        compareBy<Pair<Int, Long?>>(
                            { it.second == null },
                            { it.second ?: Long.MAX_VALUE },
                            { it.first },
                        ),
                    )
                    .map { it.first }

                rankedOrder = listOf(startIdx) + sortedBackups
                _state.value = _state.value.copy(serverLatenciesMs = latencies)
            }
        }
    }

    fun switchServer(serverIndex: Int) {
        val channel = _state.value.channel ?: return
        backupProbeJob?.cancel()
        startupWatchdogJob?.cancel()
        midStreamHealthJob?.cancel()
        playExactServer(
            channel = channel,
            serverIndex = serverIndex.coerceIn(0, channel.servers.lastIndex),
            resetTried = true,
            latencies = _state.value.serverLatenciesMs,
        )
    }

    fun retryCurrent() {
        val current = _state.value
        val ch = current.channel ?: return
        playChannel(ch, serverIndex = null)
    }

    fun showOfflineMessage(message: String) {
        _state.value = _state.value.copy(
            isBuffering = false,
            isPlaying = false,
            offlineError = message,
        )
    }

    fun togglePlayPause() {
        val exo = player ?: return
        if (exo.isPlaying) {
            exo.pause()
        } else {
            exo.play()
        }
    }

    fun stopPlayback() {
        backupProbeJob?.cancel()
        startupWatchdogJob?.cancel()
        midStreamHealthJob?.cancel()
        triedServerIndices.clear()
        player?.stop()
        player?.clearMediaItems()
        _state.value = PlaybackUiState()
    }

    fun release() {
        backupProbeJob?.cancel()
        startupWatchdogJob?.cancel()
        midStreamHealthJob?.cancel()
        scope.cancel()
        releasePlayerOnly()
        _state.value = PlaybackUiState()
    }

    private fun playExactServer(
        channel: Channel,
        serverIndex: Int,
        resetTried: Boolean,
        latencies: Map<Int, Long> = _state.value.serverLatenciesMs,
    ) {
        if (resetTried) {
            triedServerIndices.clear()
        }
        triedServerIndices.add(serverIndex)
        stablePlaybackSinceMs = 0L

        val server = channel.servers[serverIndex]
        _state.value = PlaybackUiState(
            channel = channel,
            serverIndex = serverIndex,
            isBuffering = true,
            isPlaying = false,
            latencyMs = latencies[serverIndex],
            serverLatenciesMs = latencies,
            offlineError = null,
        )

        val exo = getOrCreatePlayer()
        val mediaItem = buildMediaItem(server)
        exo.setMediaItem(mediaItem, true)
        exo.prepare()
        exo.playWhenReady = true
        armStartupWatchdog(channel.id, serverIndex)
        armMidStreamHealthMonitor(channel.id, serverIndex)
    }

    private fun handleStreamFailureOrStall() {
        val current = _state.value
        val ch = current.channel ?: return
        if (!autoFailover) {
            onAllLinksFailed()
            return
        }

        // If stream played smoothly for >= 15s before stalling, allow retrying all links fresh
        val playedSmoothlyLong = stablePlaybackSinceMs > 0L &&
            (SystemClock.elapsedRealtime() - stablePlaybackSinceMs) >= SMOOTH_PLAY_RESET_MS
        if (playedSmoothlyLong) {
            triedServerIndices.clear()
            // Keep current index marked only if multiple links exist so we try a backup first
            if (ch.servers.size > 1) {
                triedServerIndices.add(current.serverIndex)
            }
        }

        val order = rankedOrder.ifEmpty { ch.servers.indices.toList() }
        val nextIndex = order.firstOrNull { it !in triedServerIndices }
        if (nextIndex != null) {
            playExactServer(
                channel = ch,
                serverIndex = nextIndex,
                resetTried = false,
                latencies = current.serverLatenciesMs,
            )
        } else {
            // Every link on this channel failed -> move to next channel automatically
            onAllLinksFailed()
        }
    }

    private fun armStartupWatchdog(channelId: String, serverIndex: Int) {
        startupWatchdogJob?.cancel()
        startupWatchdogJob = scope.launch {
            delay(STARTUP_TIMEOUT_MS)
            val current = _state.value
            val exo = player
            val stuckAtStart = current.channel?.id == channelId &&
                current.serverIndex == serverIndex &&
                !current.isPlaying &&
                (exo == null || exo.playbackState != Player.STATE_READY)
            if (stuckAtStart) {
                handleStreamFailureOrStall()
            }
        }
    }

    /**
     * Continuously checks active playback every 2 seconds for:
     * 1. Mid-stream buffering stalls (> 5s stuck in STATE_BUFFERING)
     * 2. Frozen streams (playWhenReady == true, but position does not advance for 6s)
     */
    private fun armMidStreamHealthMonitor(channelId: String, serverIndex: Int) {
        midStreamHealthJob?.cancel()
        midStreamHealthJob = scope.launch {
            var lastPosition = -1L
            var frozenTicks = 0
            var bufferingTicks = 0

            while (true) {
                delay(HEALTH_TICK_MS)
                val exo = player ?: break
                val current = _state.value
                if (current.channel?.id != channelId || current.serverIndex != serverIndex) break
                if (current.offlineError != null) break
                if (!exo.playWhenReady) {
                    // User intentionally paused
                    frozenTicks = 0
                    bufferingTicks = 0
                    continue
                }

                when (exo.playbackState) {
                    Player.STATE_READY -> {
                        bufferingTicks = 0
                        val pos = exo.currentPosition
                        if (lastPosition >= 0L && pos <= lastPosition) {
                            frozenTicks++
                            if (frozenTicks >= MAX_FROZEN_TICKS) {
                                handleStreamFailureOrStall()
                                break
                            }
                        } else {
                            frozenTicks = 0
                        }
                        lastPosition = pos
                    }

                    Player.STATE_BUFFERING -> {
                        // Startup timeout handles initial buffering; monitor post-start rebuffering here
                        if (stablePlaybackSinceMs > 0L) {
                            bufferingTicks++
                            if (bufferingTicks >= MAX_REBUFFER_TICKS) {
                                handleStreamFailureOrStall()
                                break
                            }
                        }
                    }

                    Player.STATE_ENDED -> {
                        handleStreamFailureOrStall()
                        break
                    }

                    Player.STATE_IDLE -> Unit
                }
            }
        }
    }

    private suspend fun probeBackupServers(
        servers: List<StreamServer>,
        indices: List<Int>,
    ): List<Pair<Int, Long?>> = coroutineScope {
        indices.map { idx ->
            async {
                val ms = probeSingleServer(servers[idx])
                idx to ms
            }
        }.awaitAll()
    }

    private fun probeSingleServer(server: StreamServer): Long? {
        return runCatching {
            val start = SystemClock.elapsedRealtime()
            val reqBuilder = Request.Builder()
                .url(server.url)
                .get()
                .header("User-Agent", server.userAgent?.takeIf { it.isNotBlank() } ?: defaultUserAgent)
                .header("Range", "bytes=0-511")
            server.referrer?.takeIf { it.isNotBlank() }?.let { reqBuilder.header("Referer", it) }

            probeClient.newCall(reqBuilder.build()).execute().use { resp ->
                if (resp.isSuccessful || resp.code == 206 || resp.code in 300..399) {
                    (SystemClock.elapsedRealtime() - start).coerceAtLeast(1L)
                } else {
                    null
                }
            }
        }.getOrNull()
    }

    private fun releasePlayerOnly() {
        startupWatchdogJob?.cancel()
        midStreamHealthJob?.cancel()
        player?.removeListener(playerListener)
        player?.release()
        player = null
    }

    private fun buildMediaItem(server: StreamServer): MediaItem {
        val headers = HashMap<String, String>(2)
        headers["User-Agent"] = server.userAgent?.takeIf { it.isNotBlank() } ?: defaultUserAgent
        server.referrer?.takeIf { it.isNotBlank() }?.let { headers["Referer"] = it }
        okHttpDataSourceFactory.setDefaultRequestProperties(headers)
        return MediaItem.Builder()
            .setUri(Uri.parse(server.url))
            .setMediaId(server.url)
            .build()
    }

    private fun buildLoadControl(preset: BufferPreset): DefaultLoadControl {
        return DefaultLoadControl.Builder()
            .setBufferDurationsMs(
                preset.minBufferMs,
                preset.maxBufferMs,
                preset.bufferForPlaybackMs,
                preset.bufferForPlaybackAfterRebufferMs,
            )
            .setBackBuffer(0, false)
            .setPrioritizeTimeOverSizeThresholds(true)
            .build()
    }

    private val playerListener = object : Player.Listener {
        override fun onPlaybackStateChanged(playbackState: Int) {
            if (playbackState == Player.STATE_READY) {
                startupWatchdogJob?.cancel()
            }
            _state.value = _state.value.copy(
                isBuffering = playbackState == Player.STATE_BUFFERING,
                isPlaying = player?.isPlaying == true,
            )
        }

        override fun onIsPlayingChanged(isPlaying: Boolean) {
            if (isPlaying) {
                startupWatchdogJob?.cancel()
                if (stablePlaybackSinceMs == 0L) {
                    stablePlaybackSinceMs = SystemClock.elapsedRealtime()
                }
                onChannelPlaying()
            }
            _state.value = _state.value.copy(
                isPlaying = isPlaying,
                isBuffering = if (isPlaying) false else _state.value.isBuffering,
            )
        }

        override fun onVideoSizeChanged(videoSize: VideoSize) {
            if (videoSize.width > 0 && videoSize.height > 0) {
                _state.value = _state.value.copy(
                    videoWidth = videoSize.width,
                    videoHeight = videoSize.height,
                )
            }
        }

        override fun onPlayerError(error: PlaybackException) {
            startupWatchdogJob?.cancel()
            midStreamHealthJob?.cancel()
            handleStreamFailureOrStall()
        }
    }

    companion object {
        private const val STARTUP_TIMEOUT_MS = 3_800L
        private const val HEALTH_TICK_MS = 2_000L
        private const val MAX_FROZEN_TICKS = 3
        private const val MAX_REBUFFER_TICKS = 3
        private const val SMOOTH_PLAY_RESET_MS = 15_000L
    }
}
