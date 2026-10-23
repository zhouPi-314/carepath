param(
    [string]$Version = '0.1.0'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$android = Join-Path $root 'apps\android'
$env:JAVA_HOME = if ($env:JAVA_HOME) { $env:JAVA_HOME } else { 'D:\Development\Android\AndroidStudio\jbr' }

Push-Location $android
try {
    & '.\gradlew.bat' :app:assembleDebug --no-daemon
    if ($LASTEXITCODE -ne 0) { throw 'APK 构建失败' }
} finally {
    Pop-Location
}

$source = Join-Path $android 'app\build\outputs\apk\debug\app-debug.apk'
$target = Join-Path $android "app\build\outputs\apk\debug\TreatmentPlanCoordinationPlatform-v$Version-debug.apk"
Copy-Item -Force $source $target
Write-Host "APK: $target" -ForegroundColor Green
