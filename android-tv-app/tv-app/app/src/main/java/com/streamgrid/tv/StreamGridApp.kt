package com.streamgrid.tv

import android.app.Application
import coil.ImageLoader
import coil.ImageLoaderFactory
import coil.disk.DiskCache
import coil.memory.MemoryCache
import com.streamgrid.tv.data.db.AppDatabase
import com.streamgrid.tv.data.prefs.SettingsRepository
import com.streamgrid.tv.data.repo.PlaylistRepository
import okhttp3.ConnectionPool
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

class StreamGridApp : Application(), ImageLoaderFactory {

    val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectionPool(ConnectionPool(16, 2, TimeUnit.MINUTES))
            .connectTimeout(6, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .followRedirects(true)
            .followSslRedirects(true)
            .retryOnConnectionFailure(true)
            .build()
    }

    val database: AppDatabase by lazy { AppDatabase.getInstance(this) }
    val settingsRepository: SettingsRepository by lazy { SettingsRepository(this) }
    val playlistRepository: PlaylistRepository by lazy {
        PlaylistRepository(
            channelDao = database.channelDao(),
            settingsRepository = settingsRepository,
            okHttpClient = okHttpClient,
        )
    }

    override fun newImageLoader(): ImageLoader {
        return ImageLoader.Builder(this)
            .okHttpClient(okHttpClient)
            .memoryCache {
                MemoryCache.Builder(this)
                    .maxSizePercent(0.20)
                    .build()
            }
            .diskCache {
                DiskCache.Builder()
                    .directory(cacheDir.resolve("channel_logos"))
                    .maxSizeBytes(80L * 1024L * 1024L)
                    .build()
            }
            .crossfade(150)
            .build()
    }
}
