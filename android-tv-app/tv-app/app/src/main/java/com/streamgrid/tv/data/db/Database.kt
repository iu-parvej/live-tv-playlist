package com.streamgrid.tv.data.db

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.Transaction
import androidx.room.TypeConverter
import androidx.room.TypeConverters
import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.data.model.StreamServer
import kotlinx.coroutines.flow.Flow
import kotlinx.serialization.json.Json

@Entity(tableName = "channels")
data class ChannelEntity(
    @PrimaryKey val id: String,
    val number: Int,
    val name: String,
    val category: String,
    val logoUrl: String?,
    val tvgId: String?,
    val servers: List<StreamServer>,
    val isFavorite: Boolean,
    val lastWatchedMillis: Long,
    val sortOrder: Int,
    val syncStamp: Long,
)

fun ChannelEntity.toDomain(): Channel = Channel(
    id = id,
    number = number,
    name = name,
    category = category,
    logoUrl = logoUrl,
    tvgId = tvgId,
    servers = servers,
    isFavorite = isFavorite,
    lastWatchedMillis = lastWatchedMillis,
    sortOrder = sortOrder,
)

class Converters {
    private val json = Json { ignoreUnknownKeys = true }

    @TypeConverter
    fun fromServerList(value: List<StreamServer>): String = json.encodeToString(value)

    @TypeConverter
    fun toServerList(value: String): List<StreamServer> =
        runCatching { json.decodeFromString<List<StreamServer>>(value) }.getOrDefault(emptyList())
}

@Dao
interface ChannelDao {
    @Query("SELECT * FROM channels ORDER BY sortOrder ASC")
    fun observeAll(): Flow<List<ChannelEntity>>

    @Query("SELECT COUNT(*) FROM channels")
    suspend fun count(): Int

    @Query("SELECT id, isFavorite, lastWatchedMillis FROM channels")
    suspend fun getUserFlags(): List<ChannelUserFlags>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(items: List<ChannelEntity>)

    @Query("DELETE FROM channels WHERE syncStamp < :currentStamp")
    suspend fun deleteOlderThan(currentStamp: Long)

    @Query("UPDATE channels SET isFavorite = :favorite WHERE id = :channelId")
    suspend fun setFavorite(channelId: String, favorite: Boolean)

    @Query("UPDATE channels SET lastWatchedMillis = :timestamp WHERE id = :channelId")
    suspend fun markWatched(channelId: String, timestamp: Long)

    @Transaction
    suspend fun replaceCataloguePreservingUserFlags(
        incoming: List<Channel>,
        syncStamp: Long,
    ) {
        val existingFlags = getUserFlags().associateBy { it.id }
        val entities = incoming.map { ch ->
            val saved = existingFlags[ch.id]
            ChannelEntity(
                id = ch.id,
                number = ch.number,
                name = ch.name,
                category = ch.category,
                logoUrl = ch.logoUrl,
                tvgId = ch.tvgId,
                servers = ch.servers,
                isFavorite = saved?.isFavorite ?: ch.isFavorite,
                lastWatchedMillis = saved?.lastWatchedMillis ?: ch.lastWatchedMillis,
                sortOrder = ch.sortOrder,
                syncStamp = syncStamp,
            )
        }
        entities.chunked(300).forEach { batch -> upsertAll(batch) }
        deleteOlderThan(syncStamp)
    }
}

data class ChannelUserFlags(
    val id: String,
    val isFavorite: Boolean,
    val lastWatchedMillis: Long,
)

@Database(
    entities = [ChannelEntity::class],
    version = 1,
    exportSchema = true,
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun channelDao(): ChannelDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "streamgrid_tv.db",
                ).build().also { INSTANCE = it }
            }
    }
}
