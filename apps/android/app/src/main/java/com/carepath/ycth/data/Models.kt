package com.carepath.ycth.data

import kotlinx.serialization.Serializable

@Serializable
data class LoginRequest(
    val username: String,
    val password: String,
)

@Serializable
data class UserDto(
    val id: String,
    val username: String,
    val displayName: String,
    val role: String,
    val organizationId: String? = null,
    val organizationName: String? = null,
    val identityLabel: String? = null,
)

@Serializable
data class LoginResponse(
    val accessToken: String,
    val refreshToken: String,
    val csrfToken: String,
    val user: UserDto,
)

@Serializable
data class PatientDto(
    val id: String,
    val displayName: String,
    val recordNumber: String,
    val regionCode: String,
)

@Serializable
data class CarePlanDto(
    val id: String,
    val title: String,
    val status: String,
    val version: Int,
    val startDate: String,
    val endDate: String? = null,
    val organizationId: String,
    val doctorId: String,
    val content: PlanContentDto = PlanContentDto(),
)

@Serializable
data class PlanContentDto(
    val summary: String? = null,
)

@Serializable
data class TaskDto(
    val id: String,
    val planId: String,
    val patientId: String,
    val title: String,
    val description: String,
    val category: String,
    val dueAt: String,
    val status: String,
    val isOverdue: Boolean = false,
    val completedAt: String? = null,
)

@Serializable
data class MedicationDto(
    val id: String,
    val drugName: String,
    val approvalNumber: String? = null,
    val doseText: String,
    val frequencyText: String,
    val startDate: String,
    val endDate: String? = null,
    val status: String,
)

@Serializable
data class AlertDto(
    val id: String,
    val type: String,
    val severity: String,
    val title: String,
    val detail: String,
    val status: String,
    val createdAt: String,
)

@Serializable
data class CaregiverDto(
    val caregiverUserId: String,
    val displayName: String,
    val scopes: List<String>,
    val active: Boolean,
    val expiresAt: String? = null,
)

@Serializable
data class PatientDashboardDto(
    val patient: PatientDto,
    val plan: CarePlanDto? = null,
    val tasks: List<TaskDto> = emptyList(),
    val medications: List<MedicationDto> = emptyList(),
    val alerts: List<AlertDto> = emptyList(),
    val caregivers: List<CaregiverDto> = emptyList(),
)

@Serializable
data class CompleteTaskRequest(
    val note: String,
)

@Serializable
data class SessionSnapshot(
    val userId: String,
    val displayName: String,
    val role: String,
    val organizationName: String? = null,
)


@Serializable
data class MobileMetricDto(
    val label: String,
    val value: Int,
)

@Serializable
data class MobileItemDto(
    val title: String,
    val detail: String,
)

@Serializable
data class MobileSummaryDto(
    val role: String,
    val identityLabel: String,
    val heading: String,
    val metrics: List<MobileMetricDto> = emptyList(),
    val items: List<MobileItemDto> = emptyList(),
)
