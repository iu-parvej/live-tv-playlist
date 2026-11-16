package com.streamgrid.tv.ui.remote

import android.view.KeyEvent
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.key.onPreviewKeyEvent

/**
 * Normalizes remote control inputs across Xiaomi Mi Box (all generations),
 * Google TV / Chromecast, Fire TV, and universal Android TV IR/BT remotes.
 */
object TvRemoteKeys {
    fun isConfirmKey(keyCode: Int): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_DPAD_CENTER,
        KeyEvent.KEYCODE_ENTER,
        KeyEvent.KEYCODE_NUMPAD_ENTER,
        KeyEvent.KEYCODE_BUTTON_A,
        -> true
        else -> false
    }

    fun isChannelNextKey(keyCode: Int): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_CHANNEL_UP,
        KeyEvent.KEYCODE_PAGE_UP,
        KeyEvent.KEYCODE_MEDIA_NEXT,
        -> true
        else -> false
    }

    fun isChannelPrevKey(keyCode: Int): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_CHANNEL_DOWN,
        KeyEvent.KEYCODE_PAGE_DOWN,
        KeyEvent.KEYCODE_MEDIA_PREVIOUS,
        -> true
        else -> false
    }

    fun isMenuOrOptionsKey(keyCode: Int): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_MENU,
        KeyEvent.KEYCODE_SETTINGS,
        KeyEvent.KEYCODE_BOOKMARK,
        KeyEvent.KEYCODE_GUIDE,
        -> true
        else -> false
    }

    fun isInfoKey(keyCode: Int): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_INFO,
        KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE,
        KeyEvent.KEYCODE_MEDIA_PLAY,
        KeyEvent.KEYCODE_MEDIA_PAUSE,
        -> true
        else -> false
    }

    fun digitOrNull(keyCode: Int): Int? = when (keyCode) {
        in KeyEvent.KEYCODE_0..KeyEvent.KEYCODE_9 -> keyCode - KeyEvent.KEYCODE_0
        in KeyEvent.KEYCODE_NUMPAD_0..KeyEvent.KEYCODE_NUMPAD_9 -> keyCode - KeyEvent.KEYCODE_NUMPAD_0
        else -> null
    }
}

/**
 * Intercepts remote key presses in full-screen playback when no drawer/menu is open.
 * Handles long-press on OK/Center (useful for Mi Box remotes that lack a Menu button).
 */
fun Modifier.tvPlayerRemoteHandler(
    overlayOpen: Boolean,
    onNextChannel: () -> Unit,
    onPrevChannel: () -> Unit,
    onOpenChannelDrawer: () -> Unit,
    onOpenQuickMenu: () -> Unit,
    onToggleOsd: () -> Unit,
    onTogglePlayPause: () -> Unit,
    onDigitPressed: (Int) -> Unit,
    onBack: () -> Unit,
): Modifier = this.onPreviewKeyEvent { composeKey ->
    val native = composeKey.nativeKeyEvent
    val code = native.keyCode

    if (overlayOpen) {
        if (native.action == KeyEvent.ACTION_UP && code == KeyEvent.KEYCODE_BACK) {
            onBack()
            return@onPreviewKeyEvent true
        }
        return@onPreviewKeyEvent false
    }

    // Long-press on OK / Center opens the Quick Options menu (for Mi Box / Fire TV remotes)
    if (native.action == KeyEvent.ACTION_DOWN &&
        TvRemoteKeys.isConfirmKey(code) &&
        native.repeatCount > 0 &&
        native.isLongPress
    ) {
        onOpenQuickMenu()
        return@onPreviewKeyEvent true
    }

    if (native.action == KeyEvent.ACTION_UP) {
        // Ignore UP after long-press
        if ((native.flags and KeyEvent.FLAG_CANCELED_LONG_PRESS) != 0) {
            return@onPreviewKeyEvent true
        }
        when {
            code == KeyEvent.KEYCODE_BACK -> {
                onBack()
                return@onPreviewKeyEvent true
            }
            code == KeyEvent.KEYCODE_DPAD_UP || TvRemoteKeys.isChannelNextKey(code) -> {
                onNextChannel()
                return@onPreviewKeyEvent true
            }
            code == KeyEvent.KEYCODE_DPAD_DOWN || TvRemoteKeys.isChannelPrevKey(code) -> {
                onPrevChannel()
                return@onPreviewKeyEvent true
            }
            code == KeyEvent.KEYCODE_DPAD_LEFT -> {
                onOpenChannelDrawer()
                return@onPreviewKeyEvent true
            }
            code == KeyEvent.KEYCODE_DPAD_RIGHT || TvRemoteKeys.isMenuOrOptionsKey(code) -> {
                onOpenQuickMenu()
                return@onPreviewKeyEvent true
            }
            code == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE ||
                code == KeyEvent.KEYCODE_MEDIA_PLAY ||
                code == KeyEvent.KEYCODE_MEDIA_PAUSE -> {
                onTogglePlayPause()
                onToggleOsd()
                return@onPreviewKeyEvent true
            }
            TvRemoteKeys.isConfirmKey(code) || code == KeyEvent.KEYCODE_INFO -> {
                onToggleOsd()
                return@onPreviewKeyEvent true
            }
            else -> {
                val digit = TvRemoteKeys.digitOrNull(code)
                if (digit != null) {
                    onDigitPressed(digit)
                    return@onPreviewKeyEvent true
                }
            }
        }
    }
    false
}
