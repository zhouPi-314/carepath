package com.carepath.ycth.data

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CarePathRepository @Inject constructor(
    private val api: CarePathApi,
    private val sessionStore: SessionStore,
    private val dashboardDao: DashboardDao,
    private val json: Json,
) {
    fun cachedDashboard(): Flow<PatientDashboardDto?> =
        dashboardDao.observe().map { cached ->
            cached?.let { json.decodeFromString<PatientDashboardDto>(it.payload) }
        }

    suspend fun login(username: String, password: String): SessionSnapshot {
        val login = api.login(LoginRequest(username = username, password = password))
        sessionStore.save(login)
        return requireNotNull(sessionStore.session()) { "登录状态保存失败" }
    }

    suspend fun mobileSummary(): MobileSummaryDto {
        val token = requireNotNull(sessionStore.accessToken()) { "登录状态不存在" }
        return api.mobileSummary("Bearer $token")
    }

    suspend fun restoreDashboard(): PatientDashboardDto? {
        if (sessionStore.accessToken() == null) return null
        return runCatching { refresh() }.getOrNull()
    }

    suspend fun refresh(): PatientDashboardDto {
        val token = requireNotNull(sessionStore.accessToken()) { "登录状态不存在" }
        val dashboard = api.dashboard("Bearer $token")
        dashboardDao.upsert(
            CachedDashboardEntity(
                payload = json.encodeToString(PatientDashboardDto.serializer(), dashboard),
                cachedAt = System.currentTimeMillis(),
            ),
        )
        return dashboard
    }

    suspend fun completeTask(taskId: String): PatientDashboardDto {
        val token = requireNotNull(sessionStore.accessToken()) { "登录状态不存在" }
        api.completeTask(
            authorization = "Bearer $token",
            taskId = taskId,
            request = CompleteTaskRequest(note = "Android 端确认完成"),
        )
        return refresh()
    }

    fun hasSession(): Boolean = sessionStore.accessToken() != null

    fun session(): SessionSnapshot? = sessionStore.session()

    fun logout() = sessionStore.clear()
}
