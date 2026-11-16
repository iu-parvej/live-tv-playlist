package com.streamgrid.tv.data.prefs

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.streamgrid.tv.data.model.AppThemeMode
import com.streamgrid.tv.data.model.AspectRatioMode
import com.streamgrid.tv.data.model.BufferPreset
import com.streamgrid.tv.data.model.DefaultPlaylists
import com.streamgrid.tv.data.model.PlaylistPreset
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "streamgrid_settings")

data class UserSettings(
    val activePlaylistName: String = DefaultPlaylists.presets.first().name,
    val activePlaylistUrl: String = DefaultPlaylists.presets.first().url,
    val customPlaylists: List<PlaylistPreset> = emptyList(),
    val autoUpdateOnStart: Boolean = true,
    val bufferPreset: BufferPreset = BufferPreset.FAST_ZAP,
    val autoFailoverServer: Boolean = true,
    val aspectRatioMode: AspectRatioMode = AspectRatioMode.FIT,
    val gridColumns: Int = 5,
    val groupMultiServer: Boolean = true,
    val themeMode: AppThemeMode = AppThemeMode.RETRO_LIGHT,
    val lastEtag: String? = null,
    val lastSyncTimeMillis: Long = 0L,
    val lastChannelId: String? = null,
)

class SettingsRepository(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true }

    private object Keys {
        val ACTIVE_NAME = stringPreferencesKey("active_playlist_name")
        val ACTIVE_URL = stringPreferencesKey("active_playlist_url")
        val CUSTOM_PLAYLISTS = stringPreferencesKey("custom_playlists_json")
        val AUTO_UPDATE = booleanPreferencesKey("auto_update_on_start")
        val BUFFER_PRESET = stringPreferencesKey("buffer_preset")
        val AUTO_FAILOVER = booleanPreferencesKey("auto_failover_server")
        val ASPECT_RATIO = stringPreferencesKey("aspect_ratio_mode")
        val GRID_COLUMNS = intPreferencesKey("grid_columns")
        val GROUP_MULTI_SERVER = booleanPreferencesKey("group_multi_server")
        val THEME_MODE = stringPreferencesKey("theme_mode")
        val LAST_ETAG = stringPreferencesKey("last_etag")
        val LAST_SYNC_MILLIS = longPreferencesKey("last_sync_millis")
        val LAST_CHANNEL_ID = stringPreferencesKey("last_channel_id")
    }

    val settingsFlow: Flow<UserSettings> = context.dataStore.data.map { prefs ->
        val defaultPreset = DefaultPlaylists.presets.first()
        val customList = prefs[Keys.CUSTOM_PLAYLISTS]?.let { raw ->
            runCatching { json.decodeFromString<List<PlaylistPreset>>(raw) }.getOrDefault(emptyList())
        } ?: emptyList()

        UserSettings(
            activePlaylistName = prefs[Keys.ACTIVE_NAME] ?: defaultPreset.name,
            activePlaylistUrl = prefs[Keys.ACTIVE_URL] ?: defaultPreset.url,
            customPlaylists = customList,
            autoUpdateOnStart = prefs[Keys.AUTO_UPDATE] ?: true,
            bufferPreset = prefs[Keys.BUFFER_PRESET]?.let { name ->
                runCatching { BufferPreset.valueOf(name) }.getOrNull()
            } ?: BufferPreset.FAST_ZAP,
            autoFailoverServer = prefs[Keys.AUTO_FAILOVER] ?: true,
            aspectRatioMode = prefs[Keys.ASPECT_RATIO]?.let { name ->
                runCatching { AspectRatioMode.valueOf(name) }.getOrNull()
            } ?: AspectRatioMode.FIT,
            gridColumns = (prefs[Keys.GRID_COLUMNS] ?: 5).coerceIn(4, 6),
            groupMultiServer = prefs[Keys.GROUP_MULTI_SERVER] ?: true,
            themeMode = prefs[Keys.THEME_MODE]?.let { name ->
                runCatching { AppThemeMode.valueOf(name) }.getOrNull()
            } ?: AppThemeMode.RETRO_LIGHT,
            lastEtag = prefs[Keys.LAST_ETAG],
            lastSyncTimeMillis = prefs[Keys.LAST_SYNC_MILLIS] ?: 0L,
            lastChannelId = prefs[Keys.LAST_CHANNEL_ID],
        )
    }

    suspend fun current(): UserSettings = settingsFlow.first()

    suspend fun selectPlaylist(name: String, url: String) {
        context.dataStore.edit { prefs ->
            prefs[Keys.ACTIVE_NAME] = name
            prefs[Keys.ACTIVE_URL] = url.trim()
            prefs.remove(Keys.LAST_ETAG)
            prefs[Keys.LAST_SYNC_MILLIS] = 0L
        }
    }

    suspend fun addCustomPlaylist(name: String, url: String) {
        val cleanUrl = url.trim()
        val cleanName = name.trim().ifBlank { "Custom Playlist" }
        context.dataStore.edit { prefs ->
            val currentList = prefs[Keys.CUSTOM_PLAYLISTS]?.let { raw ->
                runCatching { json.decodeFromString<List<PlaylistPreset>>(raw) }.getOrDefault(emptyList())
            } ?: emptyList()
            val updated = (currentList.filterNot { it.url == cleanUrl } + PlaylistPreset(
                id = "custom_${cleanUrl.hashCode()}",
                name = cleanName,
                url = cleanUrl,
                description = cleanUrl,
                isCustom = true,
            ))
            prefs[Keys.CUSTOM_PLAYLISTS] = json.encodeToString(updated)
            prefs[Keys.ACTIVE_NAME] = cleanName
            prefs[Keys.ACTIVE_URL] = cleanUrl
            prefs.remove(Keys.LAST_ETAG)
            prefs[Keys.LAST_SYNC_MILLIS] = 0L
        }
    }

    suspend fun setAutoUpdateOnStart(enabled: Boolean) {
        context.dataStore.edit { it[Keys.AUTO_UPDATE] = enabled }
    }

    suspend fun setBufferPreset(preset: BufferPreset) {
        context.dataStore.edit { it[Keys.BUFFER_PRESET] = preset.name }
    }

    suspend fun setAutoFailover(enabled: Boolean) {
        context.dataStore.edit { it[Keys.AUTO_FAILOVER] = enabled }
    }

    suspend fun setAspectRatioMode(mode: AspectRatioMode) {
        context.dataStore.edit { it[Keys.ASPECT_RATIO] = mode.name }
    }

    suspend fun setGridColumns(columns: Int) {
        context.dataStore.edit { it[Keys.GRID_COLUMNS] = columns.coerceIn(4, 6) }
    }

    suspend fun setGroupMultiServer(enabled: Boolean) {
        context.dataStore.edit {
            it[Keys.GROUP_MULTI_SERVER] = enabled
            it.remove(Keys.LAST_ETAG)
        }
    }

    suspend fun setThemeMode(mode: AppThemeMode) {
        context.dataStore.edit { it[Keys.THEME_MODE] = mode.name }
    }

    suspend fun updateSyncMeta(etag: String?, syncMillis: Long) {
        context.dataStore.edit { prefs ->
            if (etag != null) prefs[Keys.LAST_ETAG] = etag
            prefs[Keys.LAST_SYNC_MILLIS] = syncMillis
        }
    }

    suspend fun setLastChannelId(channelId: String) {
        context.dataStore.edit { it[Keys.LAST_CHANNEL_ID] = channelId }
    }
}
