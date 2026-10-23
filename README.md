# 医疗健康协同体平台

[![CI](https://github.com/zhouPi-314/carepath/actions/workflows/ci.yml/badge.svg)](https://github.com/zhouPi-314/carepath/actions/workflows/ci.yml)
[![License: Apache-2.0 OR MIT](https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg)](LICENSE-APACHE)
[![Version](https://img.shields.io/badge/version-v0.1.0-green.svg)](docs/release/v0.1.0.md)

> 面向教学、科研协作与后续试点的医疗健康协同体平台。使用合成病例与官方公开数据快照，**不提供诊断或治疗建议，不用于真实患者**。

A multi-role platform for coordinating treatment-plan progress across patients, caregivers, clinicians, hospitals, regulators and pharmaceutical companies. Synthetic data only; not for clinical use.

## 项目定位

长期治疗的关键不在单次就诊，而在计划、任务、授权、提醒与多方反馈能否被持续追踪。本平台以统一的权限与审计模型连接六类业务角色，采用模块化单体架构，便于在有限环境中部署、测试与替换外部系统。

## 功能概览

| 角色 | 能力 |
|---|---|
| 医院（医生 / 院务管理） | 录入本院职工、标记病患与照护等级、分级转入、治疗记录写入与检索、患者队列与提醒 |
| 社区与志愿组织 | 志愿者管理、社区随访与照护任务、药品配送调度 |
| 药企 | 药品目录、区域需求信号（≥3 机构且 ≥50 患者月）、产能与供应反馈 |
| 政府 | 机构入驻认证、脱敏区域聚合与平台内审核 |
| 用户（病患 / 家属） | 病患查看计划、完成任务、记录观察、与医生持续沟通；家属按授权查看进展并代办任务 |
| 系统管理员 | 官方数据快照导入、外部端口能力查询 |

细化协同：转诊支持「待接收 → 接收/拒绝/完成」状态流转；计划内消息支持已读/未读；社区配送单可关联药企产品并由药企确认；Android 与微信登录后按角色进入原生管理面板。

## 演示账号

五个角色入口 + 系统管理员，密码按角色区分（沙箱专用，部署前必须替换）。登录页不区分病患与家属，登录后由医院数据标识身份：

| 角色 | 账号 | 密码 |
|---|---|---|
| 用户 · 病患 | `patient` | `Pa2026!care` |
| 用户 · 家属 | `caregiver` | `Ca2026!care` |
| 医院 · 医生 | `doctor` | `Do2026!care` |
| 医院 · 管理 | `hospital` | `Ho2026!care` |
| 社区与志愿组织 | `community` | `Co2026!care` |
| 政府 · 入驻认证 | `regulator` | `Re2026!care` |
| 药企 | `pharma` | `Ph2026!care` |
| 系统管理员 | `admin` | `Ad2026!care` |

## 三端体验

本平台不提供公网托管实例，请在本地启动后体验。完整操作清单见 [docs/demo-guide.md](docs/demo-guide.md)。

| 端 | 入口 |
|---|---|
| Web | `scripts\dev-up.cmd` 后访问 <http://localhost:5173>，选择角色自动填入账号密码 |
| Android | 构建并安装 `TreatmentPlanCoordinationPlatform-v0.1.0-debug.apk`；模拟器默认 API 为 `http://10.0.2.2:8000` |
| 微信小程序 | 微信开发者工具打开 `apps/wechat`，AppID 为 `touristappid` 沙箱 |

## 快速开始（Windows）

要求：Python 3.13、Node.js 24（含 corepack）。

```powershell
.\scripts\dev-up.cmd
```

脚本会创建后端虚拟环境、安装依赖、导入演示数据，并打开后端与 Web 两个窗口。

## 手动启动

```powershell
# 后端
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m carepath.seed
.\.venv\Scripts\uvicorn carepath.main:app --reload --port 8000

# Web（另开终端）
cd apps/web
corepack enable
pnpm install
pnpm dev
```

健康检查：`GET http://127.0.0.1:8000/health` → `{"status":"ok","service":"carepath-api","version":"0.1.0"}`。

## Docker Compose（可选）

```powershell
Copy-Item .env.example .env
docker compose -f ops/docker-compose.yml up --build -d
```

Web：<http://localhost:8080>；API：<http://localhost:8000>；MinIO 控制台：<http://localhost:9001>。

## 配置

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_ENV` | `development` | `production` 时强制 PostgreSQL、显式密钥和安全 Cookie |
| `DATABASE_URL` | `sqlite+aiosqlite:///./carepath.db` | 演示用 SQLite；生产用 PostgreSQL |
| `SECRET_KEY` | 开发占位值 | 生产必须替换为随机密钥 |
| `COOKIE_SECURE` | `false` | 生产必须为 `true`（HTTPS） |
| `CORS_ORIGINS` | 本地 5173 | 逗号分隔的允许来源 |

## 架构

```text
Web / Android / WeChat
          |
      FastAPI (/api/v1)
          |
  应用服务 + 仓储 + UnitOfWork
      /        |         \
 SQLAlchemy  Outbox   官方数据适配器
      |                    |
 SQLite / PostgreSQL   NMPA/NHSA/NHC/NBS 快照
```

- 模块化单体；领域规则与 Web、ORM 解耦。
- 外部系统以端口预留：HIS、医保、政务、供应链；未配置时显式失败。
- 官方数据只解析人工导出的 JSON 快照，不绕过访问控制。
- 概念对齐 FHIR R4（Patient / CarePlan / Task / Observation / Consent 等），不宣称完整互操作。

## 目录结构

```text
backend/        FastAPI、SQLAlchemy、Alembic、测试与演示数据
apps/web/       Vue 3 协同工作台 + Playwright E2E
apps/android/   Kotlin Compose 患者/家属端
apps/wechat/    原生微信小程序（沙箱）
docs/           规格、实施与验收、发布说明、演示指南、故障排查
ops/            Docker Compose / Nginx
scripts/        一键启动与构建脚本
.github/        CI、issue/PR 模板
```

## 环境要求

| 项 | 要求 |
|---|---|
| 操作系统 | Windows 10/11、Linux 或 macOS |
| 内存 / 磁盘 | 8 GB（Android 构建建议 16 GB）/ 约 5 GB |
| 后端 | Python 3.13 |
| Web | Node.js 24 + corepack（pnpm 11） |
| Android（可选） | JDK 17 + Android SDK（compileSdk 37） |
| 微信（可选） | 微信开发者工具 |
| 容器 / 数据库（可选） | Docker；PostgreSQL 17+ |

## 测试与质量

```powershell
# 后端
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check src tests migrations scripts
.\.venv\Scripts\python -m bandit -q -r src -x tests
.\.venv\Scripts\python -m pip_audit

# Web
cd apps/web
pnpm test; pnpm lint; pnpm build
pnpm test:e2e   # 需先 pnpm exec playwright install chromium

# 微信
cd apps/wechat
npm test; npm run check

# Android（Windows 中文路径推荐脚本）
.\scripts\test-android.ps1 -Assemble
# 或手动
cd apps/android
.\gradlew.bat :logic:test
.\gradlew.bat :app:assembleDebug

# PostgreSQL 冒烟（需要 PostgreSQL）
cd backend
$env:CAREPATH_SMOKE_DATABASE_URL='postgresql+asyncpg://user:pass@127.0.0.1:5432/carepath_smoke'
.\.venv\Scripts\python scripts\postgres_smoke.py
```

CI 共 8 个作业：后端 pytest+ruff、PostgreSQL 冒烟、Docker Compose 冒烟、Web test/lint/build、Web E2E、微信、Android build+JUnit、安全扫描（gitleaks / pip-audit / bandit / pnpm audit）。

## 路线图

| 阶段 | 内容 |
|---|---|
| 近期 | Web 端授权撤销操作面、Docker Compose 验证、微信 AppID 流程、E2E 扩展 |
| 中期 | HIS / 医保 / 政务适配器（需合作授权）、PostgreSQL 多租户隔离、通知与对象存储、FHIR 子集 |
| 长期 | 医院试点、等保与 PIPL 评估、部署与高可用、移动端推送 |

不计划：自动诊断建议、电子处方、医保结算或真实行政处置。详见 [ROADMAP.md](ROADMAP.md)。

## 参与贡献

欢迎 issue、讨论与 PR。适合入手的方向：文档、测试夹具、适配器契约、前端可访问性、移动端体验。

- [贡献指南](CONTRIBUTING.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [路线图](ROADMAP.md)
- [讨论与建议](https://github.com/zhouPi-314/carepath/discussions)
- [问题反馈](https://github.com/zhouPi-314/carepath/issues)
- [故障排查](docs/troubleshooting.md)

## 安全与隐私

- 合成数据；日志与错误响应不含令牌、密码、证件号、完整手机号或请求体。
- 家属授权按字段与有效期校验，撤销后立即失效。
- 政府聚合执行最小人数抑制；药企只看到达到发布阈值的聚合信号。
- 细节与报告方式见 [SECURITY.md](SECURITY.md)。

## 已知限制

- 未接入真实 HIS、医保、政务、供应链；相关端口为预留契约，官方公开数据通过人工快照导入。
- Docker Compose 已在本机 Docker Desktop（WSL2）与 CI 冒烟验证；受限网络需配置 registry mirrors。
- 微信为 `touristappid` 沙箱；当前无 AppID，未完成真实登录、订阅消息或上线。
- Windows 中文路径下的 Gradle JUnit 使用 `scripts\test-android.ps1` 解决。
- 不构成等保、PIPL、互联网医院或医保合规结论。

## 数据来源与许可

- 合成病例与演示数据；官方公开快照：NMPA、NHSA、NHC、NBS（仓库含测试夹具）。
- 官方快照导入：`python scripts/import_official_snapshot.py NMPA <file> --reviewer <name>`，格式见 [docs/official-data.md](docs/official-data.md)。
- 医保标签仅为信息展示，不代表实际报销。
- 代码采用 **Apache-2.0 或 MIT 双许可**，任选其一。见 [LICENSE-APACHE](LICENSE-APACHE) 与 [LICENSE-MIT](LICENSE-MIT)。

## English

A multi-role platform for treatment-plan progress coordination. It ships a FastAPI modular monolith, a Vue 3 role-based workspace, a Kotlin Compose patient app and a native WeChat mini-program (sandbox). Data is synthetic; official public snapshots are used only as fixtures. This is **not** a medical device, diagnosis tool or production EHR.

Quick start (Windows): `.\scripts\dev-up.cmd`. See [README.en.md](README.en.md).