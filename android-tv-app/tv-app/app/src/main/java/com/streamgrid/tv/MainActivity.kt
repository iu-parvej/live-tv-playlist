package com.streamgrid.tv

import android.os.Bundle
import android.view.KeyEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.streamgrid.tv.ui.AppScreen
import com.streamgrid.tv.ui.MainViewModel
import com.streamgrid.tv.ui.home.HomeScreen
import com.streamgrid.tv.ui.player.PlayerScreen
import com.streamgrid.tv.ui.remote.TvRemoteKeys
import com.streamgrid.tv.ui.settings.SettingsScreen
import com.streamgrid.tv.ui.theme.LocalTvPalette
import com.streamgrid.tv.ui.theme.StreamGridTvTheme
import com.streamgrid.tv.ui.theme.TvShapes

class MainActivity : ComponentActivity() {

    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableImmersiveTvMode()

        setContent {
            val settings by viewModel.settings.collectAsStateWithLifecycle()

            StreamGridTvTheme(themeMode = settings.themeMode) {
                val screen by viewModel.currentScreen.collectAsStateWithLifecycle()
                val categories by viewModel.categories.collectAsStateWithLifecycle()
                val selectedCategory by viewModel.selectedCategory.collectAsStateWithLifecycle()
                val visibleChannels by viewModel.visibleChannels.collectAsStateWithLifecycle()
                val allChannels by viewModel.allChannels.collectAsStateWithLifecycle()
                val syncStatus by viewModel.syncStatus.collectAsStateWithLifecycle()
                val searchQuery by viewModel.searchQuery.collectAsStateWithLifecycle()
                val focusedChannelId by viewModel.focusedChannelId.collectAsStateWithLifecycle()
                val playbackState by viewModel.playbackState.collectAsStateWithLifecycle()

                var showExitDialog by remember { mutableStateOf(false) }

                BackHandler(enabled = screen == AppScreen.HOME && !showExitDialog) {
                    showExitDialog = true
                }

                BackHandler(enabled = screen == AppScreen.PLAYER) {
                    viewModel.exitPlayer()
                }

                BackHandler(enabled = screen == AppScreen.SETTINGS) {
                    viewModel.closeSettings()
                }

                Box(modifier = Modifier.fillMaxSize()) {
                    when (screen) {
                        AppScreen.HOME -> {
                            HomeScreen(
                                settings = settings,
                                categories = categories,
                                selectedCategory = selectedCategory,
                                channels = visibleChannels,
                                syncStatus = syncStatus,
                                searchQuery = searchQuery,
                                focusedChannelId = focusedChannelId,
                                onSelectCategory = viewModel::selectCategory,
                                onSearchQueryChange = viewModel::updateSearchQuery,
                                onChannelClick = viewModel::playChannel,
                                onToggleFavorite = viewModel::toggleFavorite,
                                onRefreshClick = { viewModel.refreshPlaylist(force = true) },
                                onResumeLastClick = viewModel::resumeLastOrFirstChannel,
                                onSettingsClick = viewModel::openSettings,
                            )
                        }

                        AppScreen.PLAYER -> {
                            PlayerScreen(
                                player = viewModel.playerController.getOrCreatePlayer(),
                                playbackState = playbackState,
                                channels = visibleChannels.ifEmpty { allChannels },
                                aspectRatioMode = settings.aspectRatioMode,
                                onSelectChannel = viewModel::playChannel,
                                onNextChannel = viewModel::nextChannel,
                                onPrevChannel = viewModel::previousChannel,
                                onPlayChannelNumber = viewModel::playChannelByNumber,
                                onSwitchServer = viewModel::switchServer,
                                onRetry = viewModel::retryPlayback,
                                onTogglePlayPause = viewModel::togglePlayPause,
                                onToggleFavorite = viewModel::toggleFavorite,
                                onChangeAspectRatio = viewModel::setAspectRatioMode,
                                onExitPlayer = viewModel::exitPlayer,
                            )
                        }

                        AppScreen.SETTINGS -> {
                            SettingsScreen(
                                settings = settings,
                                onSelectPreset = viewModel::selectPreset,
                                onAddCustomPlaylist = viewModel::addCustomPlaylist,
                                onRefreshNow = { viewModel.refreshPlaylist(force = true) },
                                onAutoUpdateChange = viewModel::setAutoUpdateOnStart,
                                onBufferPresetChange = viewModel::setBufferPreset,
                                onAutoFailoverChange = viewModel::setAutoFailover,
                                onGroupMultiServerChange = viewModel::setGroupMultiServer,
                                onThemeModeChange = viewModel::setThemeMode,
                                onAspectRatioChange = viewModel::setAspectRatioMode,
                                onGridColumnsChange = viewModel::setGridColumns,
                                onClearCache = viewModel::clearLogoCache,
                                onBack = viewModel::closeSettings,
                            )
                        }
                    }

                    if (showExitDialog) {
                        ExitConfirmationOverlay(
                            onConfirmExit = { finish() },
                            onDismiss = { showExitDialog = false },
                        )
                    }
                }
            }
        }
    }

    private fun enableImmersiveTvMode() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val controller = WindowInsetsControllerCompat(window, window.decorView)
        controller.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        controller.hide(WindowInsetsCompat.Type.systemBars())
    }
}

@Composable
private fun ExitConfirmationOverlay(
    onConfirmExit: () -> Unit,
    onDismiss: () -> Unit,
) {
    val palette = LocalTvPalette.current
    val stayFocus = remember { FocusRequester() }
    LaunchedEffect(Unit) {
        runCatching { stayFocus.requestFocus() }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(palette.overlayScrim),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier
                .width(400.dp)
                .clip(TvShapes.Panel)
                .background(palette.surfaceCard)
                .border(1.dp, palette.borderSubtle, TvShapes.Panel)
                .padding(28.dp),
        ) {
            Text(
                text = "Exit Live TV?",
                color = palette.textPrimary,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Press Stay to keep watching.",
                color = palette.textSecondary,
                fontSize = 14.sp,
            )
            Spacer(modifier = Modifier.height(22.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                DialogPillButton(
                    label = "Stay",
                    modifier = Modifier.focusRequester(stayFocus),
                    onClick = onDismiss,
                )
                DialogPillButton(
                    label = "Exit App",
                    onClick = onConfirmExit,
                )
            }
        }
    }
}

@Composable
private fun DialogPillButton(
    label: String,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    Box(
        modifier = modifier
            .clip(TvShapes.Pill)
            .background(if (focused) palette.accent else palette.surfaceElevated)
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) palette.focusRingOverlay else palette.borderSubtle,
                shape = TvShapes.Pill,
            )
            .onPreviewKeyEvent { key ->
                if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                    TvRemoteKeys.isConfirmKey(key.nativeKeyEvent.keyCode)
                ) {
                    onClick()
                    true
                } else {
                    false
                }
            }
            .onFocusChanged { focused = it.isFocused }
            .focusable()
            .clickable(onClick = onClick)
            .padding(horizontal = 24.dp, vertical = 10.dp),
    ) {
        Text(
            text = label,
            color = if (focused) palette.onAccent else palette.textPrimary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}
