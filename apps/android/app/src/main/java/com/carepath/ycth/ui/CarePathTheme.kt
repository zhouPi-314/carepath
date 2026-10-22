package com.carepath.ycth.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val CarePathColors = lightColorScheme(
    primary = Color(0xFF0D5C63),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE5F2F0),
    onPrimaryContainer = Color(0xFF173437),
    secondary = Color(0xFFC77932),
    onSecondary = Color.White,
    background = Color(0xFFF3F7F5),
    onBackground = Color(0xFF173437),
    surface = Color.White,
    onSurface = Color(0xFF173437),
    surfaceVariant = Color(0xFFF1F6F4),
    onSurfaceVariant = Color(0xFF617477),
    error = Color(0xFFA83E32),
)

private val CarePathTypography = Typography(
    headlineLarge = TextStyle(
        fontSize = 32.sp,
        lineHeight = 38.sp,
        fontWeight = FontWeight.Bold,
    ),
    headlineMedium = TextStyle(
        fontSize = 25.sp,
        lineHeight = 31.sp,
        fontWeight = FontWeight.Bold,
    ),
    titleLarge = TextStyle(
        fontSize = 20.sp,
        lineHeight = 26.sp,
        fontWeight = FontWeight.SemiBold,
    ),
    bodyLarge = TextStyle(
        fontSize = 16.sp,
        lineHeight = 24.sp,
    ),
    bodyMedium = TextStyle(
        fontSize = 14.sp,
        lineHeight = 21.sp,
    ),
)

@Composable
fun CarePathTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = CarePathColors,
        typography = CarePathTypography,
        content = content,
    )
}
