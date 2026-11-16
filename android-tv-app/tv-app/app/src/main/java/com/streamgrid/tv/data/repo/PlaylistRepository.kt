package com.streamgrid.tv.data.repo

import com.streamgrid.tv.data.db.ChannelDao
import com.streamgrid.tv.data.db.toDomain
import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.data.model.SyncStatus
import com.streamgrid.tv.data.parser.M3uParser
import com.streamgrid.tv.data.prefs.SettingsRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request

class PlaylistRepository(
    private val channelDao: ChannelDao,
    private val settingsRepository: SettingsRepository,
    private val okHttpClient: OkHttpClient,
) {
    val channelsFlow: Flow<List<Channel>> =
        channelDao.observeAll().map { entities -> entities.map { it.toDomain() } }

    private val _syncStatus = MutableStateFlow<SyncStatus>(SyncStatus.Idle)
    val syncStatus: StateFlow<SyncStatus> = _syncStatus.asStateFlow()

    suspend fun syncIfNeeded(force: Boolean = false) {
        val settings = settingsRepository.current()
        val existingCount = channelDao.count()
        if (!force && !settings.autoUpdateOnStart && existingCount > 0) {
            _syncStatus.value = SyncStatus.Updated(existingCount, fromCache = true)
            return
        }

        _syncStatus.value = SyncStatus.Checking(
            if (existingCount == 0) "Loading playlist from GitHub..." else "Checking playlist updates...",
        )

        val result = withContext(Dispatchers.IO) {
            runCatching {
                val requestBuilder = Request.Builder()
                    .url(settings.activePlaylistUrl)
                    .header("User-Agent", "StreamGridTV/1.0")

                if (!force && !settings.lastEtag.isNullOrBlank() && existingCount > 0) {
                    requestBuilder.header("If-None-Match", settings.lastEtag)
                }

                okHttpClient.newCall(requestBuilder.build()).execute().use { response ->
                    if (response.code == 304 && existingCount > 0) {
                        settingsRepository.updateSyncMeta(settings.lastEtag, System.currentTimeMillis())
                        return@runCatching SyncStatus.Updated(existingCount, fromCache = true)
                    }
                    if (!response.isSuccessful) {
                        error("HTTP ${response.code}: ${response.message}")
                    }

                    val body = response.body ?: error("Empty playlist response")
                    val parsed = body.charStream().use { reader ->
                        M3uParser.parse(reader, groupMultiServer = settings.groupMultiServer)
                    }
                    if (parsed.isEmpty()) {
                        error("No channels found in playlist")
                    }

                    val now = System.currentTimeMillis()
                    channelDao.replaceCataloguePreservingUserFlags(parsed, syncStamp = now)
                    val newEtag = response.header("ETag")
                    settingsRepository.updateSyncMeta(newEtag, now)
                    SyncStatus.Updated(parsed.size, fromCache = false)
                }
            }
        }

        _syncStatus.value = result.getOrElse { err ->
            SyncStatus.Error(err.message ?: "Failed to update playlist")
        }
    }

    suspend fun toggleFavorite(channel: Channel) {
        channelDao.setFavorite(channel.id, !channel.isFavorite)
    }

    suspend fun markWatched(channelId: String) {
        channelDao.markWatched(channelId, System.currentTimeMillis())
        settingsRepository.setLastChannelId(channelId)
    }
}
