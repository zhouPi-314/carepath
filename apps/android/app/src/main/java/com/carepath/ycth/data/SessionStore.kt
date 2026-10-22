package com.carepath.ycth.data

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SessionStore @Inject constructor(
    @ApplicationContext context: Context,
) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val preferences = EncryptedSharedPreferences.create(
        context,
        "carepath_session",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun save(login: LoginResponse) {
        preferences.edit()
            .putString("accessToken", login.accessToken)
            .putString("refreshToken", login.refreshToken)
            .putString("userId", login.user.id)
            .putString("displayName", login.user.displayName)
            .putString("role", login.user.role)
            .putString("organizationName", login.user.organizationName)
            .apply()
    }

    fun accessToken(): String? = preferences.getString("accessToken", null)

    fun session(): SessionSnapshot? {
        val userId = preferences.getString("userId", null) ?: return null
        val displayName = preferences.getString("displayName", null) ?: return null
        val role = preferences.getString("role", null) ?: return null
        return SessionSnapshot(
            userId = userId,
            displayName = displayName,
            role = role,
            organizationName = preferences.getString("organizationName", null),
        )
    }

    fun clear() {
        preferences.edit().clear().apply()
    }
}
