param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 5173
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$web = Join-Path $root 'apps\web'

function Ensure-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "缺少 $Name。$Hint"
    }
}

Ensure-Command python '请安装 Python 3.13 并加入 PATH。'
Ensure-Command node '请安装 Node.js 24 并加入 PATH。'

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    corepack enable
    corepack prepare pnpm@11.28.5 --activate
}

$venv = Join-Path $backend '.venv'
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Host '创建后端虚拟环境...' -ForegroundColor Cyan
    python -m venv $venv
}

Write-Host '安装后端依赖（首次较慢）...' -ForegroundColor Cyan
& $python -m pip install --upgrade pip | Out-Null
& $python -m pip install -e "$backend[dev]" | Out-Null

Write-Host '导入演示数据...' -ForegroundColor Cyan
Push-Location $backend
try { & $python -m carepath.seed } finally { Pop-Location }

Write-Host '安装 Web 依赖...' -ForegroundColor Cyan
Push-Location $web
try { pnpm install --prefer-offline | Out-Null } finally { Pop-Location }

$apiCommand = "& '$python' -m uvicorn carepath.main:app --reload --port $ApiPort"
Start-Process powershell.exe -ArgumentList @('-NoExit', '-Command', $apiCommand) -WorkingDirectory $backend
Start-Sleep -Seconds 2

$webCommand = "pnpm dev --port $WebPort"
Start-Process powershell.exe -ArgumentList @('-NoExit', '-Command', $webCommand) -WorkingDirectory $web

Write-Host ''
Write-Host 'CarePath 已启动：' -ForegroundColor Green
Write-Host "  Web      http://localhost:$WebPort"
Write-Host "  API 文档  http://127.0.0.1:$ApiPort/docs"
Write-Host '  演示账号  patient / Pa2026!care 等，见 README.md'
Write-Host '  关闭两个新窗口即可停止服务。'
