package com.carepath.ycth.data

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "cached_dashboard")
data class CachedDashboardEntity(
    @PrimaryKey val id: Int = 1,
    val payload: String,
    val cachedAt: Long,
)

@Dao
interface DashboardDao {
    @Query("SELECT * FROM cached_dashboard WHERE id = 1")
    fun observe(): Flow<CachedDashboardEntity?>

    @Upsert
    suspend fun upsert(entity: CachedDashboardEntity)
}

@Database(
    entities = [CachedDashboardEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class OfflineDatabase : RoomDatabase() {
    abstract fun dashboardDao(): DashboardDao
}
