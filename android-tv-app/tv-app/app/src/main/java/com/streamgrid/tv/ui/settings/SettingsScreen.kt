package com.streamgrid.tv.ui.settings

import android.view.KeyEvent
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
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.PlaylistPlay
import androidx.compose.material.icons.rounded.AddLink
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.DeleteSweep
import androidx.compose.material.icons.rounded.Palette
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Speed
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.streamgrid.tv.data.model.AppThemeMode
import com.streamgrid.tv.data.model.AspectRatioMode
import com.streamgrid.tv.data.model.BufferPreset
import com.streamgrid.tv.data.model.DefaultPlaylists
import com.streamgrid.tv.data.model.PlaylistPreset
import com.streamgrid.tv.data.prefs.UserSettings
import com.streamgrid.tv.ui.remote.TvRemoteKeys
import com.streamgrid.tv.ui.theme.LocalTvPalette
import com.streamgrid.tv.ui.theme.TvShapes
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private enum class SettingsSection(val title: String, val icon: ImageVector) {
    PLAYLISTS("Playlists & Sync", Icons.AutoMirrored.Rounded.PlaylistPlay),
    PLAYBACK("Playback & Recovery", Icons.Rounded.Speed),
    APPEARANCE("Appearance & Grid", Icons.Rounded.Palette),
}

@Composable
fun SettingsScreen(
    settings: UserSettings,
    onSelectPreset: (PlaylistPreset) -> Unit,
    onAddCustomPlaylist: (String, String) -> Unit,
    onRefreshNow: () -> Unit,
    onAutoUpdateChange: (Boolean) -> Unit,
    onBufferPresetChange: (BufferPreset) -> Unit,
    onAutoFailoverChange: (Boolean) -> Unit,
    onGroupMultiServerChange: (Boolean) -> Unit,
    onThemeModeChange: (AppThemeMode) -> Unit,
    onAspectRatioChange: (AspectRatioMode) -> Unit,
    onGridColumnsChange: (Int) -> Unit,
    onClearCache: () -> Unit,
    onBack: () -> Unit,
) {
    val palette = LocalTvPalette.current
    val firstNavFocus = remember { FocusRequester() }
    var activeSection by remember { mutableStateOf(SettingsSection.PLAYLISTS) }
    var showCustomDialog by remember { mutableStateOf(false) }
    var cacheClearedMsg by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        runCatching { firstNavFocus.requestFocus() }
    }

    val allPresets = remember(settings.customPlaylists) {
        DefaultPlaylists.presets + settings.customPlaylists
    }

    val lastSyncLabel = remember(settings.lastSyncTimeMillis) {
        if (settings.lastSyncTimeMillis <= 0L) {
            "Not synced yet"
        } else {
            "Synced " + SimpleDateFormat("MMM d, h:mm a", Locale.getDefault())
                .format(Date(settings.lastSyncTimeMillis))
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(palette.backgroundGradient)
            .padding(horizontal = 28.dp, vertical = 18.dp),
    ) {
        // Compact Enterprise Header Bar
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                SettingsPillButton(
                    label = "Back",
                    icon = Icons.AutoMirrored.Rounded.ArrowBack,
                    onClick = onBack,
                )
                Spacer(modifier = Modifier.width(14.dp))
                Text(
                    text = "Settings",
                    color = palette.textPrimary,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                )
                Spacer(modifier = Modifier.width(12.dp))
                Box(
                    modifier = Modifier
                        .clip(TvShapes.Pill)
                        .background(palette.surfaceElevated)
                        .padding(horizontal = 10.dp, vertical = 4.dp),
                ) {
                    Text(
                        text = lastSyncLabel,
                        color = palette.textSecondary,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                    )
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SettingsPillButton(
                    label = "Custom URL",
                    icon = Icons.Rounded.AddLink,
                    onClick = {
                        activeSection = SettingsSection.PLAYLISTS
                        showCustomDialog = !showCustomDialog
                    },
                )
                SettingsPillButton(
                    label = "Sync Now",
                    icon = Icons.Rounded.Refresh,
                    onClick = onRefreshNow,
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Two-Pane Enterprise Console Layout
        Row(
            horizontalArrangement = Arrangement.spacedBy(18.dp),
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
        ) {
            // Left Category Rail
            Column(
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier
                    .width(225.dp)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(14.dp))
                    .background(palette.surfaceCard)
                    .border(1.dp, palette.borderSubtle, RoundedCornerShape(14.dp))
                    .padding(10.dp),
            ) {
                SettingsSection.entries.forEachIndexed { idx, section ->
                    SectionNavItem(
                        title = section.title,
                        icon = section.icon,
                        selected = activeSection == section,
                        modifier = if (idx == 0) Modifier.focusRequester(firstNavFocus) else Modifier,
                        onClick = { activeSection = section },
                    )
                }
            }

            // Right Compact Content Panel
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(14.dp))
                    .background(palette.surfaceCard)
                    .border(1.dp, palette.borderSubtle, RoundedCornerShape(14.dp))
                    .padding(16.dp),
            ) {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                    contentPadding = PaddingValues(bottom = 12.dp),
                    modifier = Modifier.fillMaxSize(),
                ) {
                    when (activeSection) {
                        SettingsSection.PLAYLISTS -> {
                            if (showCustomDialog) {
                                item {
                                    CustomPlaylistBox(
                                        onSave = { name, url ->
                                            onAddCustomPlaylist(name, url)
                                            showCustomDialog = false
                                        },
                                        onCancel = { showCustomDialog = false },
                                    )
                                }
                            }

                            item {
                                CompactLabel("ACTIVE SOURCE")
                            }

                            items(allPresets, key = { it.id }) { preset ->
                                CompactOptionRow(
                                    title = preset.name,
                                    subtitle = preset.description,
                                    selected = settings.activePlaylistUrl == preset.url,
                                    onClick = { onSelectPreset(preset) },
                                )
                            }

                            item {
                                Spacer(modifier = Modifier.height(4.dp))
                                CompactLabel("SYNC RULES")
                            }

                            item {
                                CompactToggleRow(
                                    title = "Auto-update playlist on launch",
                                    subtitle = "Uses conditional GitHub ETag check on startup",
                                    checked = settings.autoUpdateOnStart,
                                    onToggle = { onAutoUpdateChange(!settings.autoUpdateOnStart) },
                                )
                            }

                            item {
                                CompactToggleRow(
                                    title = "Group multi-server backup links",
                                    subtitle = "Combines backup links of the same channel into one tile",
                                    checked = settings.groupMultiServer,
                                    onToggle = { onGroupMultiServerChange(!settings.groupMultiServer) },
                                )
                            }
                        }

                        SettingsSection.PLAYBACK -> {
                            item {
                                CompactLabel("LATENCY & BUFFER")
                            }

                            item {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    BufferPreset.entries.forEach { preset ->
                                        Box(modifier = Modifier.weight(1f)) {
                                            CompactOptionRow(
                                                title = preset.title,
                                                subtitle = preset.subtitle,
                                                selected = settings.bufferPreset == preset,
                                                onClick = { onBufferPresetChange(preset) },
                                            )
                                        }
                                    }
                                }
                            }

                            item {
                                Spacer(modifier = Modifier.height(4.dp))
                                CompactLabel("STREAM RECOVERY")
                            }

                            item {
                                CompactToggleRow(
                                    title = "Auto-failover & freeze recovery",
                                    subtitle = "Tries all backup links, recovers frozen streams, and skips dead channels automatically",
                                    checked = settings.autoFailoverServer,
                                    onToggle = { onAutoFailoverChange(!settings.autoFailoverServer) },
                                )
                            }

                            item {
                                Spacer(modifier = Modifier.height(4.dp))
                                CompactLabel("ASPECT RATIO")
                            }

                            item {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    AspectRatioMode.entries.forEach { mode ->
                                        Box(modifier = Modifier.weight(1f)) {
                                            CompactOptionRow(
                                                title = mode.title,
                                                subtitle = null,
                                                selected = settings.aspectRatioMode == mode,
                                                onClick = { onAspectRatioChange(mode) },
                                            )
                                        }
                                    }
                                }
                            }
                        }

                        SettingsSection.APPEARANCE -> {
                            item {
                                CompactLabel("THEME")
                            }

                            item {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    AppThemeMode.entries.forEach { mode ->
                                        Box(modifier = Modifier.weight(1f)) {
                                            CompactOptionRow(
                                                title = mode.title,
                                                subtitle = mode.subtitle,
                                                selected = settings.themeMode == mode,
                                                onClick = { onThemeModeChange(mode) },
                                            )
                                        }
                                    }
                                }
                            }

                            item {
                                Spacer(modifier = Modifier.height(4.dp))
                                CompactLabel("GRID DENSITY")
                            }

                            item {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    listOf(4 to "4 Columns", 5 to "5 Columns (Default)", 6 to "6 Columns").forEach { (cols, label) ->
                                        Box(modifier = Modifier.weight(1f)) {
                                            CompactOptionRow(
                                                title = label,
                                                subtitle = null,
                                                selected = settings.gridColumns == cols,
                                                onClick = { onGridColumnsChange(cols) },
                                            )
                                        }
                                    }
                                }
                            }

                            item {
                                Spacer(modifier = Modifier.height(4.dp))
                                CompactLabel("MAINTENANCE")
                            }

                            item {
                                SettingsPillButton(
                                    label = if (cacheClearedMsg) "Logo Cache Cleared" else "Clear Logo Cache",
                                    icon = Icons.Rounded.DeleteSweep,
                                    onClick = {
                                        onClearCache()
                                        cacheClearedMsg = true
                                    },
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
private fun CompactLabel(text: String) {
    val palette = LocalTvPalette.current
    Text(
        text = text,
        color = palette.accent,
        fontSize = 11.sp,
        fontWeight = FontWeight.Bold,
        letterSpacing = 0.8.sp,
        modifier = Modifier.padding(vertical = 2.dp),
    )
}

@Composable
private fun SectionNavItem(
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
        else -> palette.backgroundTop.copy(alpha = 0.45f)
    }
    val fg = if (focused) palette.onAccent else if (selected) palette.accent else palette.textPrimary

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(bg)
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) palette.focusRingOverlay else if (selected) palette.accent.copy(alpha = 0.5f) else palette.borderSubtle,
                shape = RoundedCornerShape(10.dp),
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
            .padding(horizontal = 12.dp, vertical = 11.dp),
    ) {
        Icon(imageVector = icon, contentDescription = null, tint = fg, modifier = Modifier.size(18.dp))
        Spacer(modifier = Modifier.width(10.dp))
        Text(
            text = title,
            color = fg,
            fontSize = 13.sp,
            fontWeight = if (selected || focused) FontWeight.Bold else FontWeight.SemiBold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun CompactOptionRow(
    title: String,
    subtitle: String?,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    val bg = when {
        focused -> palette.surfaceCardFocused
        selected -> palette.surfaceElevated
        else -> palette.backgroundTop.copy(alpha = 0.5f)
    }

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(bg)
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) palette.accent else if (selected) palette.accent.copy(alpha = 0.5f) else palette.borderSubtle,
                shape = RoundedCornerShape(10.dp),
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
            .padding(horizontal = 12.dp, vertical = 10.dp),
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                color = palette.textPrimary,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            if (!subtitle.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(1.dp))
                Text(
                    text = subtitle,
                    color = palette.textSecondary,
                    fontSize = 11.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
        if (selected) {
            Spacer(modifier = Modifier.width(8.dp))
            Icon(
                imageVector = Icons.Rounded.CheckCircle,
                contentDescription = "Selected",
                tint = palette.accent,
                modifier = Modifier.size(18.dp),
            )
        }
    }
}

@Composable
private fun CompactToggleRow(
    title: String,
    subtitle: String,
    checked: Boolean,
    onToggle: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(if (focused) palette.surfaceCardFocused else palette.backgroundTop.copy(alpha = 0.5f))
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) palette.accent else palette.borderSubtle,
                shape = RoundedCornerShape(10.dp),
            )
            .onPreviewKeyEvent { key ->
                if (key.nativeKeyEvent.action == KeyEvent.ACTION_UP &&
                    TvRemoteKeys.isConfirmKey(key.nativeKeyEvent.keyCode)
                ) {
                    onToggle()
                    true
                } else {
                    false
                }
            }
            .onFocusChanged { focused = it.isFocused }
            .focusable()
            .clickable(onClick = onToggle)
            .padding(horizontal = 12.dp, vertical = 8.dp),
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = title, color = palette.textPrimary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            Text(text = subtitle, color = palette.textSecondary, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Spacer(modifier = Modifier.width(10.dp))
        Switch(
            checked = checked,
            onCheckedChange = null,
            colors = SwitchDefaults.colors(
                checkedThumbColor = palette.onAccent,
                checkedTrackColor = palette.accent,
            ),
        )
    }
}

@Composable
private fun SettingsPillButton(
    label: String,
    icon: ImageVector,
    onClick: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var focused by remember { mutableStateOf(false) }
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(TvShapes.Pill)
            .background(if (focused) palette.accent else palette.surfaceCard)
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
            .padding(horizontal = 14.dp, vertical = 8.dp),
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = if (focused) palette.onAccent else palette.textPrimary,
            modifier = Modifier.size(16.dp),
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = label,
            color = if (focused) palette.onAccent else palette.textPrimary,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun CustomPlaylistBox(
    onSave: (String, String) -> Unit,
    onCancel: () -> Unit,
) {
    val palette = LocalTvPalette.current
    var name by remember { mutableStateOf("") }
    var url by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(palette.surfaceElevated)
            .border(1.dp, palette.accent.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
            .padding(14.dp),
    ) {
        Text(
            text = "Add Custom M3U URL",
            color = palette.textPrimary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
        )
        Spacer(modifier = Modifier.height(8.dp))
        OutlinedTextField(
            value = name,
            onValueChange = { name = it },
            label = { Text("Playlist Name") },
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = palette.textPrimary,
                unfocusedTextColor = palette.textPrimary,
                focusedBorderColor = palette.accent,
                unfocusedBorderColor = palette.borderSubtle,
            ),
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(modifier = Modifier.height(8.dp))
        OutlinedTextField(
            value = url,
            onValueChange = { url = it },
            label = { Text("M3U URL") },
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = palette.textPrimary,
                unfocusedTextColor = palette.textPrimary,
                focusedBorderColor = palette.accent,
                unfocusedBorderColor = palette.borderSubtle,
            ),
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(modifier = Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            SettingsPillButton(
                label = "Save & Load",
                icon = Icons.Rounded.CheckCircle,
                onClick = { onSave(name, url) },
            )
            SettingsPillButton(
                label = "Cancel",
                icon = Icons.AutoMirrored.Rounded.ArrowBack,
                onClick = onCancel,
            )
        }
    }
}
