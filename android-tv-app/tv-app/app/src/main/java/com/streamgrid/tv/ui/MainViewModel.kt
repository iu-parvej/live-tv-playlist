package com.streamgrid.tv.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import coil.Coil
import com.streamgrid.tv.StreamGridApp
import com.streamgrid.tv.data.model.AppThemeMode
import com.streamgrid.tv.data.model.AspectRatioMode
import com.streamgrid.tv.data.model.BufferPreset
import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.data.model.PlaylistPreset
import com.streamgrid.tv.data.model.SyncStatus
import com.streamgrid.tv.data.prefs.UserSettings
import com.streamgrid.tv.player.PlaybackUiState
import com.streamgrid.tv.player.TvPlayerController
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

enum class AppScreen {
    HOME,
    PLAYER,
    SETTINGS,
}

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as StreamGridApp
    private val playlistRepo = app.playlistRepository
    private val settingsRepo = app.settingsRepository

    private var consecutiveAutoSkips = 0

    val playerController: TvPlayerController = TvPlayerController(
        context = application,
        okHttpClient = app.okHttpClient,
        onChannelPlaying = { consecutiveAutoSkips = 0 },
        onAllLinksFailed = { handleAllChannelLinksFailed() },
    )

    val settings: StateFlow<UserSettings> = settingsRepo.settingsFlow
        .stateIn(viewModelScope, SharingStarted.Eagerly, UserSettings())

    val allChannels: StateFlow<List<Channel>> = playlistRepo.channelsFlow
        .stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())

    val syncStatus: StateFlow<SyncStatus> = playlistRepo.syncStatus
    val playbackState: StateFlow<PlaybackUiState> = playerController.state

    private val _currentScreen = MutableStateFlow(AppScreen.HOME)
    val currentScreen: StateFlow<AppScreen> = _currentScreen.asStateFlow()

    private val _selectedCategory = MutableStateFlow(TAB_ALL)
    val selectedCategory: StateFlow<String> = _selectedCategory.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _focusedChannelId = MutableStateFlow<String?>(null)
    val focusedChannelId: StateFlow<String?> = _focusedChannelId.asStateFlow()

    val categories: StateFlow<List<String>> = allChannels
        .combine(_selectedCategory) { channels, _ ->
            val dynamic = channels.map { it.category }.distinct()
            listOf(TAB_FAVORITES, TAB_ALL) + dynamic
        }
        .stateIn(viewModelScope, SharingStarted.Eagerly, listOf(TAB_FAVORITES, TAB_ALL))

    val visibleChannels: StateFlow<List<Channel>> = combine(
        allChannels,
        _selectedCategory,
        _searchQuery,
    ) { channels, category, query ->
        val byCategory = when (category) {
            TAB_FAVORITES -> channels.filter { it.isFavorite }
            TAB_ALL -> channels
            else -> channels.filter { it.category == category }
        }
        val cleanQuery = query.trim()
        if (cleanQuery.isEmpty()) {
            byCategory
        } else {
            byCategory.filter {
                it.name.contains(cleanQuery, ignoreCase = true) ||
                    it.category.contains(cleanQuery, ignoreCase = true) ||
                    it.number.toString() == cleanQuery
            }
        }
    }.stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())

    init {
        viewModelScope.launch {
            settings.collect { s ->
                playerController.updateSettings(s.bufferPreset, s.autoFailoverServer)
            }
        }
        viewModelScope.launch {
            playlistRepo.syncIfNeeded(force = false)
        }
    }

    fun selectCategory(category: String) {
        _selectedCategory.value = category
    }

    fun updateSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun refreshPlaylist(force: Boolean = true) {
        viewModelScope.launch {
            playlistRepo.syncIfNeeded(force = force)
        }
    }

    fun playChannel(channel: Channel) {
        consecutiveAutoSkips = 0
        startChannelInternal(channel)
    }

    private fun startChannelInternal(channel: Channel) {
        _focusedChannelId.value = channel.id
        _currentScreen.value = AppScreen.PLAYER
        playerController.playChannel(channel, serverIndex = null)
        viewModelScope.launch {
            playlistRepo.markWatched(channel.id)
        }
    }

    private fun handleAllChannelLinksFailed() {
        val list = activeZapList()
        if (list.isEmpty()) {
            playerController.showOfflineMessage("No channels available")
            return
        }
        val maxSkips = minOf(12, list.size)
        if (consecutiveAutoSkips >= maxSkips) {
            consecutiveAutoSkips = 0
            playerController.showOfflineMessage("Unable to connect. Check Wi-Fi or retry.")
            return
        }
        consecutiveAutoSkips++
        val currentId = playbackState.value.channel?.id
        val idx = list.indexOfFirst { it.id == currentId }
        val next = if (idx < 0 || idx + 1 >= list.size) list.first() else list[idx + 1]
        startChannelInternal(next)
    }

    fun resumeLastOrFirstChannel() {
        val list = visibleChannels.value.ifEmpty { allChannels.value }
        if (list.isEmpty()) return
        val lastId = settings.value.lastChannelId
        val target = list.firstOrNull { it.id == lastId } ?: list.first()
        playChannel(target)
    }

    fun nextChannel() {
        val list = activeZapList()
        if (list.isEmpty()) return
        val currentId = playbackState.value.channel?.id
        val idx = list.indexOfFirst { it.id == currentId }
        val next = if (idx < 0 || idx + 1 >= list.size) list.first() else list[idx + 1]
        playChannel(next)
    }

    fun previousChannel() {
        val list = activeZapList()
        if (list.isEmpty()) return
        val currentId = playbackState.value.channel?.id
        val idx = list.indexOfFirst { it.id == currentId }
        val prev = if (idx <= 0) list.last() else list[idx - 1]
        playChannel(prev)
    }

    fun playChannelByNumber(number: Int) {
        val match = allChannels.value.firstOrNull { it.number == number } ?: return
        playChannel(match)
    }

    fun switchServer(serverIndex: Int) {
        playerController.switchServer(serverIndex)
    }

    fun retryPlayback() {
        playerController.retryCurrent()
    }

    fun togglePlayPause() {
        playerController.togglePlayPause()
    }

    fun exitPlayer() {
        playerController.stopPlayback()
        _currentScreen.value = AppScreen.HOME
    }

    fun openSettings() {
        _currentScreen.value = AppScreen.SETTINGS
    }

    fun closeSettings() {
        _currentScreen.value = AppScreen.HOME
    }

    fun toggleFavorite(channel: Channel) {
        viewModelScope.launch {
            playlistRepo.toggleFavorite(channel)
            // Keep playback state badge in sync immediately
            val current = playbackState.value.channel
            if (current != null && current.id == channel.id) {
                playerController.state.value.channel
            }
        }
    }

    fun selectPreset(preset: PlaylistPreset) {
        viewModelScope.launch {
            settingsRepo.selectPlaylist(preset.name, preset.url)
            _selectedCategory.value = TAB_ALL
            _searchQuery.value = ""
            playlistRepo.syncIfNeeded(force = true)
        }
    }

    fun addCustomPlaylist(name: String, url: String) {
        if (url.isBlank()) return
        viewModelScope.launch {
            settingsRepo.addCustomPlaylist(name, url)
            _selectedCategory.value = TAB_ALL
            _searchQuery.value = ""
            playlistRepo.syncIfNeeded(force = true)
        }
    }

    fun setAutoUpdateOnStart(enabled: Boolean) {
        viewModelScope.launch { settingsRepo.setAutoUpdateOnStart(enabled) }
    }

    fun setBufferPreset(preset: BufferPreset) {
        viewModelScope.launch { settingsRepo.setBufferPreset(preset) }
    }

    fun setAutoFailover(enabled: Boolean) {
        viewModelScope.launch { settingsRepo.setAutoFailover(enabled) }
    }

    fun setAspectRatioMode(mode: AspectRatioMode) {
        viewModelScope.launch { settingsRepo.setAspectRatioMode(mode) }
    }

    fun setGridColumns(columns: Int) {
        viewModelScope.launch { settingsRepo.setGridColumns(columns) }
    }

    fun setGroupMultiServer(enabled: Boolean) {
        viewModelScope.launch {
            settingsRepo.setGroupMultiServer(enabled)
            playlistRepo.syncIfNeeded(force = true)
        }
    }

    fun setThemeMode(mode: AppThemeMode) {
        viewModelScope.launch { settingsRepo.setThemeMode(mode) }
    }

    fun toggleThemeMode() {
        val next = if (settings.value.themeMode == AppThemeMode.RETRO_LIGHT) {
            AppThemeMode.MIDNIGHT_DARK
        } else {
            AppThemeMode.RETRO_LIGHT
        }
        setThemeMode(next)
    }

    @OptIn(coil.annotation.ExperimentalCoilApi::class)
    fun clearLogoCache() {
        viewModelScope.launch {
            val loader = Coil.imageLoader(getApplication())
            loader.memoryCache?.clear()
            loader.diskCache?.clear()
        }
    }

    private fun activeZapList(): List<Channel> {
        return visibleChannels.value.ifEmpty { allChannels.value }
    }

    override fun onCleared() {
        super.onCleared()
        playerController.release()
    }

    companion object {
        const val TAB_FAVORITES = "Favorites"
        const val TAB_ALL = "All Channels"
    }
}
