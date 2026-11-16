package com.streamgrid.tv.ui.player

import android.view.KeyEvent
import androidx.activity.compose.BackHandler
import androidx.annotation.OptIn
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.focusable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AspectRatio
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.Dns
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material.icons.rounded.StarBorder
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import com.streamgrid.tv.data.model.AspectRatioMode
import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.player.PlaybackUiState
import com.streamgrid.tv.ui.components.ChannelLogo
import com.streamgrid.tv.ui.remote.TvRemoteKeys
import com.streamgrid.tv.ui.remote.tvPlayerRemoteHandler
import com.streamgrid.tv.ui.theme.LocalTvPalette
import com.streamgrid.tv.ui.theme.TvShapes
import kotlinx.coroutines.delay

private enum class PlayerOverlay {
    NONE,
    CHANNEL_DRAWER,
    QUICK_MENU,
}

@OptIn(UnstableApi::class)
@Composable
fun PlayerScreen(
    player: ExoPlayer,
    playbackState: PlaybackUiState,
    channels: List<Channel>,
    aspectRatioMode: AspectRatioMode,
    onSelectChannel: (Channel) -> Unit,
    onNextChannel: () -> Unit,
    onPrevChannel: () -> Unit,
    onPlayChannelNumber: (Int) -> Unit,
    onSwitchServer: (Int) -> Unit,
    onRetry: () -> Unit,
    onTogglePlayPause: () -> Unit,
    onToggleFavorite: (Channel) -> Unit,
    onChangeAspectRatio: (AspectRatioMode) -> Unit,
    onExitPlayer: () -> Unit,
) {
    val palette = LocalTvPalette.current
    val activeChannel = playbackState.channel
    val liveFavorite = remember(activeChannel, channels) {
        channels.firstOrNull { it.id == activeChannel?.id }?.isFavorite ?: activeChannel?.isFavorite ?: false
    }

    var activeOverlay by remember { mutableStateOf(PlayerOverlay.NONE) }
    var showOsd by remember { mutableStateOf(true) }
    var osdTrigger by remember { mutableIntStateOf(0) }
    var typedNumber by remember { mutableStateOf("") }

    val playerFocusRequester = remember { FocusRequester() }

    // Brief bottom-left OSD auto-hides after 2.5 seconds
    LaunchedEffect(activeChannel?.id, osdTrigger, activeOverlay) {
        if (activeOverlay == PlayerOverlay.NONE && showOsd) {
            delay(2_500L)
            showOsd = false
        }
    }

    LaunchedEffect(activeChannel?.id) {
        showOsd = true
        osdTrigger++
    }

    LaunchedEffect(typedNumber) {
        if (typedNumber.isNotEmpty()) {
            delay(1_000L)
            typedNumber.toIntOrNull()?.let { onPlayChannelNumber(it) }
            typedNumber = ""
        }
    }

    LaunchedEffect(activeOverlay) {
        if (activeOverlay == PlayerOverlay.NONE) {
            runCatching { playerFocusRequester.requestFocus() }
        }
    }

    BackHandler(enabled = activeOverlay != PlayerOverlay.NONE) {
        activeOverlay = PlayerOverlay.NONE
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .tvPlayerRemoteHandler(
                overlayOpen = activeOverlay != PlayerOverlay.NONE,
                onNextChannel = {
                    showOsd = true
                    osdTrigger++
                    onNextChannel()
                },
                onPrevChannel = {
                    showOsd = true
                    osdTrigger++
                    onPrevChannel()
                },
                onOpenChannelDrawer = { activeOverlay = PlayerOverlay.CHANNEL_DRAWER },
                onOpenQuickMenu = { activeOverlay = PlayerOverlay.QUICK_MENU },
                onToggleOsd = {
                    showOsd = !showOsd
                    if (showOsd) osdTrigger++
                },
                onTogglePlayPause = onTogglePlayPause,
                onDigitPressed = { digit ->
                    if (typedNumber.length < 4) {
                        typedNumber += digit.toString()
                    }
                },
                onBack = {
                    if (activeOverlay != PlayerOverlay.NONE) {
                        activeOverlay = PlayerOverlay.NONE
                    } else {
                        onExitPlayer()
                    }
                },
            )
            .focusRequester(playerFocusRequester)
            .focusable()
            .pointerInput(activeOverlay) {
                detectTapGestures {
                    if (activeOverlay != PlayerOverlay.NONE) {
                        activeOverlay = PlayerOverlay.NONE
                    } else {
                        showOsd = !showOsd
                        if (showOsd) osdTrigger++
                    }
                }
            },
    ) {
        val videoModifier = when (aspectRatioMode) {
            AspectRatioMode.RATIO_16_9 -> Modifier
                .align(Alignment.Center)
                .fillMaxHeight()
                .aspectRatio(16f / 9f, matchHeightConstraintsFirst = true)
            AspectRatioMode.RATIO_4_3 -> Modifier
                .align(Alignment.Center)
                .fillMaxHeight()
                .aspectRatio(4f / 3f, matchHeightConstraintsFirst = true)
            else -> Modifier.fillMaxSize()
        }

        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    useController = false
                    keepScreenOn = true
                    isFocusable = false
                    isFocusableInTouchMode = false
                    this.player = player
                }
            },
            update = { view ->
                if (view.player !== player) {
                    view.player = player
                }
                view.resizeMode = when (aspectRatioMode) {
                    AspectRatioMode.FIT -> AspectRatioFrameLayout.RESIZE_MODE_FIT
                    AspectRatioMode.FILL -> AspectRatioFrameLayout.RESIZE_MODE_ZOOM
                    AspectRatioMode.RATIO_16_9, AspectRatioMode.RATIO_4_3 ->
                        AspectRatioFrameLayout.RESIZE_MODE_FILL
                }
            },
            modifier = videoModifier,
        )

        // Subtle center spinner while switching/buffering
        if (playbackState.isBuffering && playbackState.offlineError == null) {
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .size(54.dp)
                    .clip(CircleShape)
                    .background(Color(0x99000000)),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator(
                    color = palette.accent,
                    strokeWidth = 3.dp,
                    modifier = Modifier.size(28.dp),
                )
            }
        }

        // Only shown if 12 consecutive channels fail (e.g., total Wi-Fi loss)
        if (playbackState.offlineError != null && activeOverlay == PlayerOverlay.NONE) {
            Box(
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .padding(28.dp)
                    .clip(TvShapes.Card)
                    .background(Color(0xD9111318))
                    .border(1.dp, palette.accent, TvShapes.Card)
                    .clickable { onRetry() }
                    .padding(horizontal = 18.dp, vertical = 12.dp),
            ) {
                Text(
                    text = playbackState.offlineError,
                    color = Color.White,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold,
                )
            }
        }

        // Direct numeric channel entry HUD
        if (typedNumber.isNotEmpty()) {
            Box(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(28.dp)
                    .clip(TvShapes.Card)
                    .background(Color(0xDD111318))
                    .border(2.dp, palette.accent, TvShapes.Card)
                    .padding(horizontal = 20.dp, vertical = 10.dp),
            ) {
                Text(
                    text = "CH $typedNumber",
                    color = palette.accent,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        }

        // Minimal Bottom-Left Corner OSD ONLY (Logo + Channel Number + Channel Name)
        AnimatedVisibility(
            visible = showOsd && activeOverlay == PlayerOverlay.NONE && activeChannel != null,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(start = 28.dp, bottom = 24.dp),
        ) {
            if (activeChannel != null) {
                MinimalChannelOsd(channel = activeChannel)
            }
        }

        // Left Slide-Out Quick Channel Switcher Drawer (DPAD_LEFT)
        AnimatedVisibility(
            visible = activeOverlay == PlayerOverlay.CHANNEL_DRAWER,
            enter = slideInHorizontally { -it } + fadeIn(),
            exit = slideOutHorizontally { -it } + fadeOut(),
            modifier = Modifier.align(Alignment.CenterStart),
        ) {
            QuickChannelDrawer(
                channels = channels,
                activeChannelId = activeChannel?.id,
                onSelectChannel = { ch ->
                    activeOverlay = PlayerOverlay.NONE
                    onSelectChannel(ch)
                },
            )
        }

        // Right Slide-Out Quick Options Menu (DPAD_RIGHT / MENU / Hold OK)
        AnimatedVisibility(
            visible = activeOverlay == PlayerOverlay.QUICK_MENU && activeChannel != null,
            enter = slideInHorizontally { it } + fadeIn(),
            exit = slideOutHorizontally { it } + fadeOut(),
            modifier = Modifier.align(Alignment.CenterEnd),
        ) {
            if (activeChannel != null) {
                QuickPlayerMenu(
                    channel = activeChannel,
                    isFavorite = liveFavorite,
                    activeServerIndex = playbackState.serverIndex,
                    serverLatenciesMs = playbackState.serverLatenciesMs,
                    aspectRatioMode = aspectRatioMode,
                    onSelectServer = { idx ->
                        activeOverlay = PlayerOverlay.NONE
                        onSwitchServer(idx)
                    },
                    onSelectAspectRatio = { mode ->
                        onChangeAspectRatio(mode)
                    },
                    onToggleFavorite = { onToggleFavorite(activeChannel) },
                    onReloadStream = {
                        activeOverlay = PlayerOverlay.NONE
                        onRetry()
                    },
                )
            }
        }
    }
}

@Composable
private fun MinimalChannelOsd(channel: Channel) {
    val palette = LocalTvPalette.current
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(RoundedCornerShape(14.dp))
            .background(Color(0xCC0D111A))
            .border(1.dp, Color(0x33FFFFFF), RoundedCornerShape(14.dp))
            .padding(horizontal = 14.dp, vertical = 10.dp),
    ) {
        ChannelLogo(
            name = channel.name,
            logoUrl = channel.logoUrl,
            modifier = Modifier.size(46.dp),
            monogramSize = 16.sp,
        )
        Spacer(modifier = Modifier.width(12.dp))
        Column {
            Text(
                text = "CH ${channel.number}",
                color = palette.accent,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = channel.name,
                color = Color.White,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun QuickChannelDrawer(
    channels: List<Channel>,
    activeChannelId: String?,
    onSelectChannel: (Channel) -> Unit,
) {
    val palette = LocalTvPalette.current
    val listState = rememberLazyListState()
    val focusRequester = remember { FocusRequester() }
    val activeIdx = remember(channels, activeChannelId) {
        channels.indexOfFirst { it.id == activeChannelId }.coerceAtLeast(0)
    }

    LaunchedEffect(Unit) {
        if (channels.isNotEmpty()) {
            listState.scrollToItem(activeIdx)
            runCatching { focusRequester.requestFocus() }
        }
    }

    Column(
        modifier = Modifier
            .width(340.dp)
            .fillMaxHeight()
            .background(palette.drawerPanel)
            .border(1.dp, palette.borderSubtle)
            .padding(18.dp),
    ) {
        Text(
            text = "Channels",
            color = palette.textPrimary,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
        )
        Spacer(modifier = Modifier.height(10.dp))

        LazyColumn(
            state = listState,
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(bottom = 16.dp),
            modifier = Modifier.fillMaxSize(),
        ) {
            items(channels, key = { it.id }) { ch ->
                val isCurrent = ch.id == activeChannelId
                var focused by remember { mutableStateOf(false) }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .fillMaxWidth()
                        .then(if (isCurrent) Modifier.focusRequester(focusRequester) else Modifier)
                        .clip(TvShapes.LogoBox)
                        .background(
                            when {
                                focused -> palette.accent
                                isCurrent -> palette.surfaceElevated
                                else -> palette.surfaceCard
                            },
                        )
                        .border(
                            width = if (focused) 2.dp else 1.dp,
                            color = if (focused) palette.focusRingOverlay else if (isCurrent) palette.accent else palette.borderSubtle,
                            shape = TvShapes.LogoBox,
                        )
                        .onPreviewKeyEvent { key ->
                            if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                                TvRemoteKeys.isConfirmKey(key.nativeKeyEvent.keyCode)
                            ) {
                                onSelectChannel(ch)
                                true
                            } else {
                                false
                            }
                        }
                        .onFocusChanged { focused = it.isFocused }
                        .focusable()
                        .clickable { onSelectChannel(ch) }
                        .padding(horizontal = 12.dp, vertical = 9.dp),
                ) {
                    ChannelLogo(
                        name = ch.name,
                        logoUrl = ch.logoUrl,
                        modifier = Modifier.size(40.dp),
                        monogramSize = 13.sp,
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "${ch.number}. ${ch.name}",
                        color = if (focused) palette.onAccent else palette.textPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f),
                    )
                    if (isCurrent) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (focused) palette.onAccent else palette.liveGreen),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun QuickPlayerMenu(
    channel: Channel,
    isFavorite: Boolean,
    activeServerIndex: Int,
    serverLatenciesMs: Map<Int, Long>,
    aspectRatioMode: AspectRatioMode,
    onSelectServer: (Int) -> Unit,
    onSelectAspectRatio: (AspectRatioMode) -> Unit,
    onToggleFavorite: () -> Unit,
    onReloadStream: () -> Unit,
) {
    val palette = LocalTvPalette.current
    val firstOptionFocus = remember { FocusRequester() }
    LaunchedEffect(Unit) {
        runCatching { firstOptionFocus.requestFocus() }
    }

    LazyColumn(
        verticalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier
            .width(320.dp)
            .fillMaxHeight()
            .background(palette.drawerPanel)
            .border(1.dp, palette.borderSubtle)
            .padding(18.dp),
    ) {
        item {
            Text(
                text = "Options",
                color = palette.textPrimary,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = channel.name,
                color = palette.accent,
                fontSize = 13.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Spacer(modifier = Modifier.height(8.dp))
        }

        item {
            MenuOptionRow(
                title = if (isFavorite) "Remove from Favorites" else "Add to Favorites",
                icon = if (isFavorite) Icons.Rounded.Star else Icons.Rounded.StarBorder,
                selected = isFavorite,
                modifier = Modifier.focusRequester(firstOptionFocus),
                onClick = onToggleFavorite,
            )
        }

        item {
            MenuOptionRow(
                title = "Reload Stream",
                icon = Icons.Rounded.Refresh,
                selected = false,
                onClick = onReloadStream,
            )
        }

        if (channel.servers.size > 1) {
            item {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Links (${channel.servers.size})",
                    color = palette.textSecondary,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
            items(channel.servers.indices.toList()) { idx ->
                val srv = channel.servers[idx]
                val ping = serverLatenciesMs[idx]?.let { " • ${it}ms" } ?: ""
                MenuOptionRow(
                    title = "${srv.label}$ping",
                    icon = Icons.Rounded.Dns,
                    selected = idx == activeServerIndex,
                    onClick = { onSelectServer(idx) },
                )
            }
        }

        item {
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "Aspect Ratio",
                color = palette.textSecondary,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
            )
        }

        items(AspectRatioMode.entries) { mode ->
            MenuOptionRow(
                title = mode.title,
                icon = Icons.Rounded.AspectRatio,
                selected = mode == aspectRatioMode,
                onClick = { onSelectAspectRatio(mode) },
            )
        }
    }
}

@Composable
private fun MenuOptionRow(
    title: String,
    icon: ImageVector,
    selected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    val bg = when {
        focused -> palette.accent
        selected -> palette.surfaceElevated
        else -> palette.surfaceCard
    }
    val fg = if (focused) palette.onAccent else palette.textPrimary

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = modifier
            .fillMaxWidth()
            .clip(TvShapes.LogoBox)
            .background(bg)
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) palette.focusRingOverlay else if (selected) palette.accent else palette.borderSubtle,
                shape = TvShapes.LogoBox,
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
            .padding(horizontal = 14.dp, vertical = 10.dp),
    ) {
        Icon(imageVector = icon, contentDescription = null, tint = fg, modifier = Modifier.size(17.dp))
        Spacer(modifier = Modifier.width(10.dp))
        Text(
            text = title,
            color = fg,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.weight(1f),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        if (selected) {
            Icon(
                imageVector = Icons.Rounded.Check,
                contentDescription = null,
                tint = if (focused) palette.onAccent else palette.accent,
                modifier = Modifier.size(17.dp),
            )
        }
    }
}
