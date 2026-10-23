package com.carepath.ycth.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.carepath.ycth.data.CarePathRepository
import com.carepath.ycth.data.MobileSummaryDto
import com.carepath.ycth.data.PatientDashboardDto
import com.carepath.ycth.data.SessionSnapshot
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CarePathUiState(
    val session: SessionSnapshot? = null,
    val dashboard: PatientDashboardDto? = null,
    val summary: MobileSummaryDto? = null,
    val loading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class CarePathViewModel @Inject constructor(
    private val repository: CarePathRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(
        CarePathUiState(
            session = repository.session(),
        ),
    )
    val state = _state.asStateFlow()

    init {
        viewModelScope.launch {
            repository.cachedDashboard().collect { cached ->
                if (cached != null && _state.value.dashboard == null) {
                    _state.update { it.copy(dashboard = cached) }
                }
            }
        }
        if (repository.hasSession()) {
            refresh()
        }
    }

    fun login(username: String, password: String) {
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            runCatching {
                val session = repository.login(username.trim(), password)
                val isUser = session.role == "PATIENT" || session.role == "CAREGIVER"
                val dashboard = if (isUser) repository.refresh() else null
                val summary = if (isUser) null else repository.mobileSummary()
                Triple(session, dashboard, summary)
            }
                .onSuccess { (session, dashboard, summary) ->
                    _state.update {
                        it.copy(
                            session = session,
                            dashboard = dashboard,
                            summary = summary,
                            loading = false,
                            error = null,
                        )
                    }
                }
                .onFailure { error ->
                    _state.update {
                        it.copy(
                            loading = false,
                            error = error.message ?: "登录失败，请检查后端服务。",
                        )
                    }
                }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            val isUser = _state.value.session?.role in setOf("PATIENT", "CAREGIVER")
            if (!isUser) {
                runCatching { repository.mobileSummary() }
                    .onSuccess { summary ->
                        _state.update { it.copy(summary = summary, loading = false, error = null) }
                    }
                    .onFailure {
                        _state.update { it.copy(loading = false, error = "后端不可用，请稍后重试。") }
                    }
                return@launch
            }
            runCatching { repository.restoreDashboard() }
                .onSuccess { dashboard ->
                    _state.update {
                        it.copy(
                            dashboard = dashboard ?: it.dashboard,
                            session = repository.session(),
                            loading = false,
                            error = if (dashboard == null) "后端不可用，当前显示本地缓存。" else null,
                        )
                    }
                }
                .onFailure {
                    _state.update {
                        it.copy(
                            loading = false,
                            error = "后端不可用，当前显示本地缓存。",
                        )
                    }
                }
        }
    }

    fun completeTask(taskId: String) {
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            runCatching { repository.completeTask(taskId) }
                .onSuccess { dashboard ->
                    _state.update {
                        it.copy(dashboard = dashboard, loading = false, error = null)
                    }
                }
                .onFailure { error ->
                    _state.update {
                        it.copy(
                            loading = false,
                            error = error.message ?: "任务同步失败。",
                        )
                    }
                }
        }
    }

    fun logout() {
        repository.logout()
        _state.value = CarePathUiState()
    }
}
