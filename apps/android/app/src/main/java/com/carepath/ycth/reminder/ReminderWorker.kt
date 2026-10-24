package com.carepath.ycth.reminder

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.carepath.ycth.MainActivity
import com.carepath.ycth.R
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.concurrent.TimeUnit

class ReminderWorker(
    appContext: Context,
    workerParams: WorkerParameters,
) : CoroutineWorker(appContext, workerParams) {
    override suspend fun doWork(): Result {
        val manager = applicationContext.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                applicationContext.getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_DEFAULT,
            ).apply {
                description = applicationContext.getString(
                    R.string.notification_channel_description,
                )
            },
        )
        val intent = Intent(applicationContext, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("医疗健康保障协同平台任务提醒")
            .setContentText(inputData.getString(KEY_TITLE) ?: "请查看今天的治疗任务")
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        manager.notify(REMINDER_ID, notification)
        return Result.success()
    }

    companion object {
        const val CHANNEL_ID = "carepath_tasks"
        const val REMINDER_ID = 4201
        private const val KEY_TITLE = "taskTitle"
        private const val UNIQUE_WORK = "carepath-next-task"

        fun schedule(context: Context, taskTitle: String, dueAt: String?) {
            val due = dueAt?.let {
                runCatching { Instant.parse(it) }.getOrNull()
            } ?: return
            val delayMillis = ChronoUnit.MILLIS.between(Instant.now(), due).coerceAtLeast(5_000)
            val request = OneTimeWorkRequestBuilder<ReminderWorker>()
                .setInitialDelay(delayMillis, TimeUnit.MILLISECONDS)
                .setInputData(Data.Builder().putString(KEY_TITLE, taskTitle).build())
                .build()
            WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE_WORK,
                ExistingWorkPolicy.REPLACE,
                request,
            )
        }
    }
}
