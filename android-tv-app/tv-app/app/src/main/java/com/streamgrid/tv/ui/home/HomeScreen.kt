package com.streamgrid.tv.ui.home

import android.view.KeyEvent
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.itemsIndexed
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.streamgrid.tv.R
import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.data.model.SyncStatus
import com.streamgrid.tv.data.prefs.UserSettings
import com.streamgrid.tv.ui.components.ChannelLogo
import com.streamgrid.tv.ui.remote.TvRemoteKeys
import com.streamgrid.tv.ui.theme.LocalTvPalette
import com.streamgrid.tv.ui.theme.TvShapes
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    settings: UserSettings,
    categories: List<String>,
    selectedCategory: String,
    channels: List<Channel>,
    syncStatus: SyncStatus,
    searchQuery: String,
    focusedChannelId: String?,
    onSelectCategory: (String) -> Unit,
    onSearchQueryChange: (String) -> Unit,
    onChannelClick: (Channel) -> Unit,
    onToggleFavorite: (Channel) -> Unit,
    onRefreshClick: () -> Unit,
    onResumeLastClick: () -> Unit,
    onSettingsClick: () -> Unit,
) {
    val palette = LocalTvPalette.current
    val gridState = rememberLazyGridState()
    val coroutineScope = rememberCoroutineScope()
    val firstCardFocusRequester = remember { FocusRequester() }
    val targetCardFocusRequester = remember { FocusRequester() }

    LaunchedEffect(channels.isNotEmpty(), focusedChannelId) {
        if (channels.isNotEmpty()) {
            val idx = focusedChannelId?.let { id -> channels.indexOfFirst { it.id == id } } ?: -1
            if (idx >= 0) {
                gridState.scrollToItem(idx)
                runCatching { targetCardFocusRequester.requestFocus() }
            } else {
                runCatching { firstCardFocusRequester.requestFocus() }
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(palette.backgroundGradient)
            .onPreviewKeyEvent { key ->
                val native = key.nativeKeyEvent
                if (native.action == KeyEvent.ACTION_UP) {
                    when {
                        TvRemoteKeys.isChannelNextKey(native.keyCode) ||
                            native.keyCode == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE -> {
                            onResumeLastClick()
                            true
                        }
                        else -> false
                    }
                } else {
                    false
                }
            },
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 24.dp, vertical = 14.dp),
        ) {
            // Minimal Top Bar: Left = Logo + "Live TV", Right = Compact Search + Settings Icon
            HomeTopBar(
                searchQuery = searchQuery,
                onSearchQueryChange = onSearchQueryChange,
                onSettings = onSettingsClick,
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Clean Category Tabs Strip (nothing extra below it)
            CategoryTabsRow(
                categories = categories,
                selectedCategory = selectedCategory,
                onSelectCategory = { cat ->
                    onSelectCategory(cat)
                    coroutineScope.launch { gridState.scrollToItem(0) }
                },
            )

            Spacer(modifier = Modifier.height(10.dp))

            Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                when {
                    channels.isEmpty() && syncStatus is SyncStatus.Checking -> {
                        LoadingPlaylistView(message = syncStatus.message)
                    }
                    channels.isEmpty() && syncStatus is SyncStatus.Error -> {
                        EmptyOrErrorView(
                            title = "Could not load playlist",
                            subtitle = syncStatus.message,
                            actionLabel = "Retry",
                            onAction = onRefreshClick,
                        )
                    }
                    channels.isEmpty() -> {
                        val emptyMsg = if (selectedCategory == "Favorites") {
                            "No favorite channels yet. Hold OK on any channel to star it."
                        } else {
                            "No channels match your search."
                        }
                        EmptyOrErrorView(
                            title = if (selectedCategory == "Favorites") "Favorites is empty" else "No channels found",
                            subtitle = emptyMsg,
                            actionLabel = "Show All Channels",
                            onAction = {
                                onSearchQueryChange("")
                                onSelectCategory("All Channels")
                            },
                        )
                    }
                    else -> {
                        LazyVerticalGrid(
                            state = gridState,
                            columns = GridCells.Fixed(settings.gridColumns),
                            contentPadding = PaddingValues(top = 4.dp, bottom = 16.dp, start = 2.dp, end = 2.dp),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.fillMaxSize(),
                        ) {
                            itemsIndexed(
                                items = channels,
                                key = { _, ch -> ch.id },
                            ) { index, channel ->
                                val itemModifier = when {
                                    channel.id == focusedChannelId -> Modifier.focusRequester(targetCardFocusRequester)
                                    index == 0 -> Modifier.focusRequester(firstCardFocusRequester)
                                    else -> Modifier
                                }
                                ChannelGridCard(
                                    channel = channel,
                                    modifier = itemModifier,
                                    onClick = { onChannelClick(channel) },
                                    onToggleFavorite = { onToggleFavorite(channel) },
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HomeTopBar(
    searchQuery: String,
    onSearchQueryChange: (String) -> Unit,
    onSettings: () -> Unit,
) {
    val palette = LocalTvPalette.current

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(40.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        // Left: App Logo + "Live TV"
        Row(verticalAlignment = Alignment.CenterVertically) {
            Image(
                painter = painterResource(id = R.drawable.tv_program_logo),
                contentDescription = "Live TV",
                modifier = Modifier.size(32.dp),
            )
            Spacer(modifier = Modifier.width(10.dp))
            Text(
                text = "Live TV",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = palette.textPrimary,
                maxLines = 1,
            )
        }

        // Right: Compact Search Bar + Settings Icon (no text)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            CompactSearchBar(
                query = searchQuery,
                onQueryChange = onSearchQueryChange,
            )
            SettingsIconButton(onClick = onSettings)
        }
    }
}

@Composable
private fun CompactSearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    var isEditing by remember { mutableStateOf(false) }
    val pillFocusRequester = remember { FocusRequester() }
    val inputFocusRequester = remember { FocusRequester() }

    LaunchedEffect(isEditing) {
        if (isEditing) {
            runCatching { inputFocusRequester.requestFocus() }
        }
    }

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .width(220.dp)
            .height(36.dp)
            .clip(TvShapes.Pill)
            .background(if (focused || isEditing) palette.surfaceCardFocused else palette.surfaceCard)
            .border(
                width = if (focused || isEditing) 2.dp else 1.dp,
                color = if (focused || isEditing) palette.accent else palette.borderSubtle,
                shape = TvShapes.Pill,
            )
            .then(
                if (!isEditing) {
                    Modifier
                        .focusRequester(pillFocusRequester)
                        .onPreviewKeyEvent { key ->
                            if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                                TvRemoteKeys.isConfirmKey(key.nativeKeyEvent.keyCode)
                            ) {
                                isEditing = true
                                true
                            } else {
                                false
                            }
                        }
                        .onFocusChanged { focused = it.isFocused }
                        .focusable()
                        .clickable { isEditing = true }
                } else {
                    Modifier.onPreviewKeyEvent { key ->
                        if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                            key.nativeKeyEvent.keyCode == KeyEvent.KEYCODE_BACK
                        ) {
                            isEditing = false
                            true
                        } else {
                            false
                        }
                    }
                },
            )
            .padding(horizontal = 12.dp),
    ) {
        Icon(
            imageVector = Icons.Rounded.Search,
            contentDescription = "Search",
            tint = if (focused || isEditing) palette.accent else palette.textSecondary,
            modifier = Modifier.size(16.dp),
        )
        Spacer(modifier = Modifier.width(8.dp))
        Box(
            modifier = Modifier.weight(1f),
            contentAlignment = Alignment.CenterStart,
        ) {
            if (!isEditing) {
                Text(
                    text = query.ifEmpty { "Search..." },
                    color = if (query.isEmpty()) palette.textSecondary else palette.textPrimary,
                    fontSize = 13.sp,
                    fontWeight = if (query.isEmpty()) FontWeight.Normal else FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            } else {
                if (query.isEmpty()) {
                    Text(
                        text = "Type channel...",
                        color = palette.textSecondary,
                        fontSize = 13.sp,
                        maxLines = 1,
                    )
                }
                BasicTextField(
                    value = query,
                    onValueChange = onQueryChange,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                    keyboardActions = KeyboardActions(onSearch = { isEditing = false }),
                    textStyle = TextStyle(
                        color = palette.textPrimary,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                    ),
                    cursorBrush = SolidColor(palette.accent),
                    modifier = Modifier
                        .fillMaxWidth()
                        .focusRequester(inputFocusRequester),
                )
            }
        }
        if (query.isNotEmpty()) {
            Spacer(modifier = Modifier.width(4.dp))
            Icon(
                imageVector = Icons.Rounded.Close,
                contentDescription = "Clear",
                tint = palette.textSecondary,
                modifier = Modifier
                    .size(15.dp)
                    .clickable {
                        onQueryChange("")
                        isEditing = false
                    },
            )
        }
    }
}

@Composable
private fun SettingsIconButton(onClick: () -> Unit) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .size(36.dp)
            .clip(CircleShape)
            .background(if (focused) palette.accent else palette.surfaceCard)
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) palette.focusRingOverlay else palette.borderSubtle,
                shape = CircleShape,
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
            .clickable(onClick = onClick),
    ) {
        Icon(
            imageVector = Icons.Rounded.Settings,
            contentDescription = "Settings",
            tint = if (focused) palette.onAccent else palette.textPrimary,
            modifier = Modifier.size(19.dp),
        )
    }
}

@Composable
private fun CategoryTabsRow(
    categories: List<String>,
    selectedCategory: String,
    onSelectCategory: (String) -> Unit,
) {
    val palette = LocalTvPalette.current
    LazyRow(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        contentPadding = PaddingValues(horizontal = 2.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        items(categories, key = { it }) { category ->
            val selected = category == selectedCategory
            var focused by remember { mutableStateOf(false) }

            val bg = when {
                focused -> palette.accent
                selected -> palette.surfaceElevated
                else -> palette.surfaceCard.copy(alpha = 0.7f)
            }
            val textColor = when {
                focused -> palette.onAccent
                selected -> palette.accent
                else -> palette.textSecondary
            }

            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .height(32.dp)
                    .clip(TvShapes.Pill)
                    .background(bg)
                    .border(
                        width = if (focused) 2.dp else 1.dp,
                        color = when {
                            focused -> palette.focusRingOverlay
                            selected -> palette.accent.copy(alpha = 0.65f)
                            else -> palette.borderSubtle
                        },
                        shape = TvShapes.Pill,
                    )
                    .onPreviewKeyEvent { key ->
                        if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                            TvRemoteKeys.isConfirmKey(key.nativeKeyEvent.keyCode)
                        ) {
                            onSelectCategory(category)
                            true
                        } else {
                            false
                        }
                    }
                    .onFocusChanged { focused = it.isFocused }
                    .focusable()
                    .clickable { onSelectCategory(category) }
                    .padding(horizontal = 15.dp),
            ) {
                Text(
                    text = formatCategoryLabel(category),
                    color = textColor,
                    fontSize = 13.sp,
                    fontWeight = if (selected || focused) FontWeight.Bold else FontWeight.SemiBold,
                    maxLines = 1,
                )
            }
        }
    }
}

@Composable
private fun ChannelGridCard(
    channel: Channel,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
    onToggleFavorite: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    val scale by animateFloatAsState(
        targetValue = if (focused) 1.025f else 1f,
        animationSpec = tween(75),
        label = "cardFocusScale",
    )

    Surface(
        shape = RoundedCornerShape(12.dp),
        color = if (focused) palette.surfaceCardFocused else palette.surfaceCard,
        border = BorderStroke(
            width = if (focused) 2.dp else 1.dp,
            color = if (focused) palette.accent else palette.borderSubtle,
        ),
        shadowElevation = 0.dp,
        modifier = modifier
            .fillMaxWidth()
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            }
            .onPreviewKeyEvent { key ->
                val native = key.nativeKeyEvent
                val code = native.keyCode
                if (native.action == KeyEvent.ACTION_DOWN &&
                    TvRemoteKeys.isConfirmKey(code) &&
                    native.isLongPress
                ) {
                    onToggleFavorite()
                    return@onPreviewKeyEvent true
                }
                if (native.action == KeyEvent.ACTION_UP) {
                    if ((native.flags and KeyEvent.FLAG_CANCELED_LONG_PRESS) != 0) {
                        return@onPreviewKeyEvent true
                    }
                    when {
                        TvRemoteKeys.isConfirmKey(code) -> {
                            onClick()
                            true
                        }
                        TvRemoteKeys.isMenuOrOptionsKey(code) -> {
                            onToggleFavorite()
                            true
                        }
                        else -> false
                    }
                } else {
                    false
                }
            }
            .onFocusChanged { focused = it.isFocused }
            .focusable()
            .clickable(onClick = onClick),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(82.dp),
            ) {
                ChannelLogo(
                    name = channel.name,
                    logoUrl = channel.logoUrl,
                    modifier = Modifier.fillMaxSize(),
                    monogramSize = 22.sp,
                )

                if (channel.isFavorite) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(4.dp)
                            .size(20.dp)
                            .clip(CircleShape)
                            .background(palette.surfaceCard.copy(alpha = 0.9f)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Star,
                            contentDescription = "Favorite",
                            tint = palette.gold,
                            modifier = Modifier.size(13.dp),
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = channel.name,
                color = if (focused) palette.accent else palette.textPrimary,
                fontSize = 13.sp,
                fontWeight = if (focused) FontWeight.Bold else FontWeight.SemiBold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
private fun LoadingPlaylistView(message: String) {
    val palette = LocalTvPalette.current
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(color = palette.accent)
            Spacer(modifier = Modifier.height(14.dp))
            Text(
                text = message,
                color = palette.textPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.Medium,
            )
        }
    }
}

@Composable
private fun EmptyOrErrorView(
    title: String,
    subtitle: String,
    actionLabel: String,
    onAction: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(24.dp),
        ) {
            Text(text = title, color = palette.textPrimary, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = subtitle,
                color = palette.textSecondary,
                fontSize = 14.sp,
                textAlign = TextAlign.Center,
            )
            Spacer(modifier = Modifier.height(18.dp))
            Box(
                modifier = Modifier
                    .clip(TvShapes.Pill)
                    .background(if (focused) palette.focusRingOverlay else palette.accent)
                    .onPreviewKeyEvent { key ->
                        if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                            TvRemoteKeys.isConfirmKey(key.nativeKeyEvent.keyCode)
                        ) {
                            onAction()
                            true
                        } else {
                            false
                        }
                    }
                    .onFocusChanged { focused = it.isFocused }
                    .focusable()
                    .clickable(onClick = onAction)
                    .padding(horizontal = 22.dp, vertical = 10.dp),
            ) {
                Text(
                    text = actionLabel,
                    color = palette.onAccent,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

private fun formatCategoryLabel(raw: String): String =
    raw.replace(Regex("""^\d+\.\s*"""), "")
