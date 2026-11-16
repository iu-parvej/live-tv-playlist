package com.streamgrid.tv.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.streamgrid.tv.ui.theme.LocalTvPalette
import com.streamgrid.tv.ui.theme.TvShapes
import kotlin.math.absoluteValue

private val fallbackPalettes = listOf(
    listOf(Color(0xFF0284C7), Color(0xFF0369A1)),
    listOf(Color(0xFF7C3AED), Color(0xFF5B21B6)),
    listOf(Color(0xFF059669), Color(0xFF047857)),
    listOf(Color(0xFFD97706), Color(0xFFB45309)),
    listOf(Color(0xFFDC2626), Color(0xFF991B1B)),
    listOf(Color(0xFF0D9488), Color(0xFF115E59)),
)

@Composable
fun ChannelLogo(
    name: String,
    logoUrl: String?,
    modifier: Modifier = Modifier,
    monogramSize: TextUnit = 24.sp,
) {
    var failed by remember(logoUrl) { mutableStateOf(false) }
    val palette = LocalTvPalette.current

    Box(
        modifier = modifier
            .clip(TvShapes.LogoBox)
            .background(palette.logoPlate),
        contentAlignment = Alignment.Center,
    ) {
        if (!logoUrl.isNullOrBlank() && !failed) {
            AsyncImage(
                model = ImageRequest.Builder(LocalContext.current)
                    .data(logoUrl)
                    .crossfade(120)
                    .build(),
                contentDescription = name,
                contentScale = ContentScale.Fit,
                onError = { failed = true },
                modifier = Modifier
                    .fillMaxSize()
                    .padding(10.dp),
            )
        } else {
            val palette = fallbackPalettes[(name.hashCode().absoluteValue) % fallbackPalettes.size]
            val initials = remember(name) {
                name.split(" ")
                    .filter { it.isNotBlank() }
                    .take(2)
                    .mapNotNull { it.firstOrNull()?.uppercaseChar() }
                    .joinToString("")
                    .ifBlank { "TV" }
            }
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Brush.linearGradient(palette)),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = initials,
                    color = Color.White,
                    fontSize = monogramSize,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}
