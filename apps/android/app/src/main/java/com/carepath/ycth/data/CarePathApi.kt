package com.carepath.ycth.data

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface CarePathApi {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @GET("patient/dashboard")
    suspend fun dashboard(
        @Header("Authorization") authorization: String,
    ): PatientDashboardDto

    @GET("mobile/summary")
    suspend fun mobileSummary(
        @Header("Authorization") authorization: String,
    ): MobileSummaryDto

    @POST("tasks/{taskId}/complete")
    suspend fun completeTask(
        @Header("Authorization") authorization: String,
        @Path("taskId") taskId: String,
        @Body request: CompleteTaskRequest,
    ): TaskDto
}
