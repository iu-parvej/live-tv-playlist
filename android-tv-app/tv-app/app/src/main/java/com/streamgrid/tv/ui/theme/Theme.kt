package com.streamgrid.tv.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.streamgrid.tv.data.model.AppThemeMode

@Immutable
data class TvPalette(
    val isDark: Boolean,
    val backgroundTop: Color,
    val backgroundBottom: Color,
    val surfaceCard: Color,
    val surfaceCardFocused: Color,
    val surfaceElevated: Color,
    val logoPlate: Color,
    val accent: Color,
    val onAccent: Color,
    val accentSoft: Color,
    val gold: Color,
    val liveGreen: Color,
    val dangerRed: Color,
    val textPrimary: Color,
    val textSecondary: Color,
    val borderSubtle: Color,
    val focusRingOverlay: Color,
    val overlayScrim: Color,
    val drawerPanel: Color,
    val badgeNeutralBg: Color,
) {
    val backgroundGradient: Brush
        get() = Brush.verticalGradient(listOf(backgroundTop, backgroundBottom))
}

val RetroLightPalette = TvPalette(
    isDark = false,
    backgroundTop = Color(0xFFF6F1E7),
    backgroundBottom = Color(0xFFEAE2D2),
    surfaceCard = Color(0xFFFFFDF8),
    surfaceCardFocused = Color(0xFFFFFFFF),
    surfaceElevated = Color(0xFFEDE5D6),
    logoPlate = Color(0xFFF3EDE0),
    accent = Color(0xFFD94826),
    onAccent = Color(0xFFFFFDF9),
    accentSoft = Color(0x1FD94826),
    gold = Color(0xFFB7791F),
    liveGreen = Color(0xFF15803D),
    dangerRed = Color(0xFFDC2626),
    textPrimary = Color(0xFF181A1F),
    textSecondary = Color(0xFF635D52),
    borderSubtle = Color(0xFFD8CEBC),
    focusRingOverlay = Color(0xFF9A2E14),
    overlayScrim = Color(0xD91A1815),
    drawerPanel = Color(0xF5F6F1E7),
    badgeNeutralBg = Color(0xFFE7DEC9),
)

val MidnightDarkPalette = TvPalette(
    isDark = true,
    backgroundTop = Color(0xFF070B14),
    backgroundBottom = Color(0xFF0F172A),
    surfaceCard = Color(0xFF161F33),
    surfaceCardFocused = Color(0xFF1E2B45),
    surfaceElevated = Color(0xFF1C263D),
    logoPlate = Color(0xFF222E47),
    accent = Color(0xFF38BDF8),
    onAccent = Color(0xFF04101B),
    accentSoft = Color(0x2E38BDF8),
    gold = Color(0xFFFBBF24),
    liveGreen = Color(0xFF22C55E),
    dangerRed = Color(0xFFEF4444),
    textPrimary = Color(0xFFF8FAFC),
    textSecondary = Color(0xFF94A3B8),
    borderSubtle = Color(0x1FFFFFFF),
    focusRingOverlay = Color(0xFFFFFFFF),
    overlayScrim = Color(0xCC070B14),
    drawerPanel = Color(0xEB0B1120),
    badgeNeutralBg = Color(0x33FFFFFF),
)

val LocalTvPalette = staticCompositionLocalOf { RetroLightPalette }

object TvShapes {
    val Card = RoundedCornerShape(16.dp)
    val LogoBox = RoundedCornerShape(12.dp)
    val Pill = RoundedCornerShape(50)
    val Panel = RoundedCornerShape(20.dp)
}

@Composable
fun StreamGridTvTheme(
    themeMode: AppThemeMode = AppThemeMode.RETRO_LIGHT,
    content: @Composable () -> Unit,
) {
    val palette = when (themeMode) {
        AppThemeMode.RETRO_LIGHT -> RetroLightPalette
        AppThemeMode.MIDNIGHT_DARK -> MidnightDarkPalette
    }

    val colorScheme = if (palette.isDark) {
        darkColorScheme(
            primary = palette.accent,
            onPrimary = palette.onAccent,
            secondary = palette.gold,
            background = palette.backgroundTop,
            surface = palette.surfaceCard,
            onBackground = palette.textPrimary,
            onSurface = palette.textPrimary,
            surfaceVariant = palette.surfaceElevated,
            onSurfaceVariant = palette.textSecondary,
        )
    } else {
        lightColorScheme(
            primary = palette.accent,
            onPrimary = palette.onAccent,
            secondary = palette.gold,
            background = palette.backgroundTop,
            surface = palette.surfaceCard,
            onBackground = palette.textPrimary,
            onSurface = palette.textPrimary,
            surfaceVariant = palette.surfaceElevated,
            onSurfaceVariant = palette.textSecondary,
        )
    }

    val typography = Typography(
        headlineMedium = TextStyle(
            fontSize = 26.sp,
            fontWeight = FontWeight.Bold,
            color = palette.textPrimary,
            letterSpacing = (-0.3).sp,
        ),
        titleLarge = TextStyle(
            fontSize = 20.sp,
            fontWeight = FontWeight.SemiBold,
            color = palette.textPrimary,
        ),
        titleMedium = TextStyle(
            fontSize = 16.sp,
            fontWeight = FontWeight.SemiBold,
            color = palette.textPrimary,
        ),
        bodyMedium = TextStyle(
            fontSize = 14.sp,
            fontWeight = FontWeight.Normal,
            color = palette.textSecondary,
        ),
        labelMedium = TextStyle(
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            color = palette.textSecondary,
        ),
    )

    CompositionLocalProvider(LocalTvPalette provides palette) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = typography,
            content = content,
        )
    }
}
