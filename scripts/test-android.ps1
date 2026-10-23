param(
    [string]$GradlePath = '',
    [switch]$Assemble
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$drive = $null
foreach ($candidate in @('X:', 'Y:', 'Z:')) {
    if (-not (Test-Path $candidate)) { $drive = $candidate; break }
}
if (-not $drive) { throw '没有可用的盘符（X/Y/Z）用于映射仓库路径。' }

if (-not $GradlePath) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\gradle\gradle-9.6.0\bin\gradle.bat'),
        'D:\Development\Cache\gradle\gradle-9.6.0\bin\gradle.bat'
    )
    $GradlePath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $GradlePath) {
    $GradlePath = Join-Path $root 'apps\android\gradlew.bat'
}

subst $drive $root
try {
    Write-Host "映射 $drive -> $root（ASCII 路径，规避中文路径下的 JUnit 进程问题）" -ForegroundColor Cyan
    Push-Location "$drive\apps\android"
    try {
        & $GradlePath :logic:test --no-daemon
        if ($LASTEXITCODE -ne 0) { throw 'Android JUnit 测试失败' }
        if ($Assemble) {
            & $GradlePath :app:assembleDebug --no-daemon
            if ($LASTEXITCODE -ne 0) { throw 'Android debug 构建失败' }
        }
        Write-Host 'Android 本机验证通过。' -ForegroundColor Green
    } finally {
        Pop-Location
    }
} finally {
    subst $drive /d | Out-Null
}
