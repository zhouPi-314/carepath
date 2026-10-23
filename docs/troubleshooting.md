# 故障排查

按「现象 → 原因 → 处理」组织。命令默认在仓库根目录执行。

## 启动与依赖

| 现象 | 原因 | 处理 |
|---|---|---|
| `pnpm` 不是命令 | Node 未启用 corepack | `corepack enable`；必要时 `corepack prepare pnpm@11.28.5 --activate` |
| `python` 不是命令 | Python 未加入 PATH | 安装 Python 3.13，重新打开终端 |
| `pip install -e` 失败 | 网络或代理 | 配置 pip 镜像/代理后重试；CI 使用默认源 |
| 端口被占用 | 8000/5173 已被其他程序使用 | 换端口：`uvicorn ... --port 8001`、`pnpm dev --port 5174` |
| 后端启动时报数据库错误 | 旧 SQLite 文件结构不兼容 | 删除 `backend/carepath.db` 后重新 `python -m carepath.seed` |

## 测试

| 现象 | 原因 | 处理 |
|---|---|---|
| 测试互相污染 | 外部 `DATABASE_URL` 影响测试库 | 测试已强制隔离；如自定义请用 `CAREPATH_TEST_DATABASE_URL` |
| SQLite 下外键不生效 | SQLite 默认关闭外键 | 测试夹具已执行 `PRAGMA foreign_keys=ON`；生产请用 PostgreSQL |
| `pip-audit` 报告漏洞 | 依赖版本过旧 | 升级依赖；当前基线要求 0 已知漏洞 |
| `pnpm audit` 报 endpoint 不存在 | 使用了不支持审计的镜像源 | 指定官方源：`pnpm audit --registry https://registry.npmjs.org` |
| gitleaks 命中演示密码 | 合成凭据被规则识别 | 已在 `.gitleaks.toml` 白名单；不要复用这些密码 |

## Web 与 E2E

| 现象 | 原因 | 处理 |
|---|---|---|
| `pnpm test:e2e` 启动失败 | 未安装浏览器 | `pnpm exec playwright install chromium` |
| 浏览器下载超时 | 网络无法访问 Playwright CDN | 配置镜像或代理；CI 中会实际执行 E2E |
| 预览页 404 / API 502 | 后端未启动或代理未生效 | 先启动后端 8000；确认 `vite.config.ts` 的 `preview.proxy` |
| 登录后立即跳回登录页 | Cookie 被浏览器拦截 | 使用 `localhost` 而非 `127.0.0.1` 访问 Web，并允许本地 Cookie |

## Android

| 现象 | 原因 | 处理 |
|---|---|---|
| `compileSdk 37` 缺失 | Android SDK 未安装对应平台 | 用 sdkmanager 安装 `platforms;android-37` |
| JUnit 测试进程找不到测试类 | Windows 中文路径 + Gradle 组合限制 | 运行 `scripts\test-android.ps1`（自动映射 ASCII 盘符）；或在 Linux CI 运行 |
| APK 名称不是正式名称 | 本地直接构建 | 使用 `scripts\build-android.ps1`，产物为 `TreatmentPlanCoordinationPlatform-v0.1.0-debug.apk` |
| 模拟器连不上后端 | 模拟器访问宿主机需 `10.0.2.2` | 默认 `BuildConfig.API_BASE_URL` 已使用 `http://10.0.2.2:8000/api/v1/` |
| 构建内存不足 | Gradle 默认堆较小 | 在 `gradle.properties` 调整 `org.gradle.jvmargs` |

## 微信小程序

| 现象 | 原因 | 处理 |
|---|---|---|
| 无法真实登录/推送 | 使用 `touristappid` 沙箱 | 需自行申请 AppID 并替换 `project.config.json`；沙箱不能上线 |
| 开发者工具打不开项目 | 目录选择错误 | 选择 `apps/wechat`，不要选仓库根目录 |
| 请求失败 | 未关闭域名校验或后端未启动 | 开发工具中勾选「不校验合法域名」；启动后端 8000 |

## PostgreSQL 与 Docker

| 现象 | 原因 | 处理 |
|---|---|---|
| `postgres_smoke.py` 跳过 | 未设置 `CAREPATH_SMOKE_DATABASE_URL` | 设置为 `postgresql+asyncpg://...` 后重试；脚本会清空目标 schema |
| Docker 引擎无法启动 | WSL2 未安装或未更新 | 管理员执行 `wsl --install --no-distribution`，按提示重启；再启动 Docker Desktop |
| `docker-credential-desktop` 找不到 | Docker 的 bin 未加入 PATH | 将 `<Docker安装目录>\DockerDesktop\resources\bin` 加入 PATH，或重启终端 |
| 拉取镜像超时/401 | Docker Hub 访问受限 | 在 `%USERPROFILE%\.docker\daemon.json` 配置 `registry-mirrors` 后重启 Docker Desktop |
| 官方 `minio/minio` 镜像不存在 | 官方镜像已下架 | 使用仓库内的 `elestio/minio` 等价镜像（Compose 已配置） |
| 生产环境启动被拒绝 | `APP_ENV=production` 校验 | 使用 PostgreSQL、显式 `SECRET_KEY` 与 `COOKIE_SECURE=true` |

## 官方数据导入

```powershell
cd backend
.\.venv\Scripts\python scripts\import_official_snapshot.py NMPA .\tests\fixtures\official\nmpa.json --reviewer "审核人"
```

快照格式与来源见 [official-data.md](official-data.md)。

## 仍然无法解决

请附上：操作系统、命令、完整错误、是否使用合成数据。提交到 [Issues](https://github.com/zhouPi-314/health-collaboration-platform/issues)，不要粘贴令牌、密码或真实个人信息。