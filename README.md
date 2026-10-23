# 医程共护 CarePath

[![CI](https://github.com/zhouPi-314/carepath/actions/workflows/ci.yml/badge.svg)](https://github.com/zhouPi-314/carepath/actions/workflows/ci.yml)
[![License: Apache-2.0 OR MIT](https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg)](LICENSE-APACHE)
[![Version](https://img.shields.io/badge/version-v0.1.0-green.svg)](docs/release/v0.1.0.md)

> 面向教学与开源协作的治疗方案进度协同 MVP。使用合成病例与官方公开数据快照，**不提供诊断或治疗建议，不用于真实患者**。

CarePath is an open-source MVP for coordinating treatment-plan progress across patients, caregivers, clinicians, hospitals, regulators and pharmaceutical companies. Synthetic data only; not for clinical use.

## 为什么做这个项目

长期治疗的关键不是单次就诊，而是计划、任务、授权、提醒和多方反馈能否被持续追踪。CarePath 用一套可审计的权限模型把六类角色放进同一条治疗路径，并以模块化单体保持可部署、可测试、可替换。

## 功能概览

| 角色 | 能力 |
|---|---|
| 患者 | 查看计划与任务、完成自护任务、记录观察、查看提醒 |
| 家属 | 在患者授权范围内查看与代办任务，授权撤销后立即失效 |
| 医生 | 从已发布模板创建计划、查看患者队列与提醒 |
| 医院管理员 | 院内成员、计划、任务完成率与提醒统计 |
| 政府监管 | 区域脱敏聚合与平台内审核，小样本整体抑制 |
| 药企 | 自有药品目录、区域需求信号（≥3 机构且 ≥50 患者月）、产能反馈 |
| 系统管理员 | 官方数据快照导入、外部端口能力查询 |

技术要点：FastAPI + SQLAlchemy 2 + Alembic；Vue 3 + TypeScript；Kotlin Compose；原生微信小程序；SQLite 演示、PostgreSQL 冒烟；JWT + scrypt；家属 ABAC；审计与 Outbox。

## 演示账号

六个业务角色 + 系统管理员，密码按角色区分（沙箱专用，生产必须替换）：

| 角色 | 账号 | 密码 |
|---|---|---|
| 患者 | `patient` | `Pa2026!care` |
| 家属 | `caregiver` | `Ca2026!care` |
| 医生 | `doctor` | `Do2026!care` |
| 医院管理员 | `hospital` | `Ho2026!care` |
| 政府监管 | `regulator` | `Re2026!care` |
| 药企 | `pharma` | `Ph2026!care` |
| 系统管理员 | `admin` | `Ad2026!care` |

## 如何体验演示

本项目**没有公网托管实例**，请在本地启动后体验：

| 端 | 方式 |
|---|---|
| Web | 一键脚本或手动启动后访问 <http://localhost:5173>，选择角色自动填入账号密码 |
| Android | 构建 `app-debug.apk` 安装到模拟器/真机；模拟器默认 API 地址为 `http://10.0.2.2:8000` |
| 微信小程序 | 用微信开发者工具打开 `apps/wechat`，AppID 为 `touristappid` 沙箱 |

## 一键启动（Windows）

要求：Python 3.13、Node.js 24（含 corepack）。双击或在 PowerShell 执行：

```powershell
.\scripts\dev-up.cmd
```

脚本会创建后端虚拟环境、安装依赖、导入演示数据，并打开后端与 Web 两个窗口。首次运行需要联网下载依赖。

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

- 模块化单体，不拆微服务；领域规则与 Web/ORM 解耦。
- 外部系统以端口预留：HIS、医保、政务、供应链；未配置时显式失败，不伪造联调。
- 官方数据只解析人工导出的 JSON 快照，不绕过访问控制。
- 概念对齐 FHIR R4（Patient / CarePlan / Task / Observation / Consent 等），不宣称完整互操作。

## 目录结构

```text
backend/        FastAPI、SQLAlchemy、Alembic、测试与演示数据
apps/web/       Vue 3 多角色工作台 + Playwright E2E
apps/android/   Kotlin Compose 患者/家属端
apps/wechat/    原生微信小程序（沙箱）
docs/           规格、实施计划、发布说明、故障排查
ops/            Docker Compose / Nginx
scripts/        一键启动脚本
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

# Android
cd apps/android
.\gradlew.bat :logic:test
.\gradlew.bat :app:assembleDebug

# PostgreSQL 冒烟（需要 PostgreSQL）
cd backend
$env:CAREPATH_SMOKE_DATABASE_URL='postgresql+asyncpg://user:pass@127.0.0.1:5432/carepath_smoke'
.\.venv\Scripts\python scripts\postgres_smoke.py
```

CI 共 7 个作业：后端 pytest+ruff、PostgreSQL 冒烟、Web test/lint/build、Web E2E、微信、Android build+JUnit、安全扫描（gitleaks / pip-audit / bandit / pnpm audit）。

## 路线图

| 阶段 | 内容 |
|---|---|
| 近期 | Web 端授权撤销操作面、Docker Compose 实际验证、微信 AppID 流程、E2E 扩展 |
| 中期 | HIS / 医保 / 政务适配器落地（需合作授权）、PostgreSQL 多租户隔离、通知与对象存储、FHIR 子集 |
| 长期 | 医院试点、等保与 PIPL 合规、部署与高可用、移动端推送 |

不计划：AI 诊断、电子处方、医保结算或真实行政处置。详见 [ROADMAP.md](ROADMAP.md)。

## 参与贡献

欢迎 issue、讨论与 PR。适合入手的方向：文档、测试夹具、适配器契约、前端可访问性、移动端体验。

- [贡献指南](CONTRIBUTING.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [路线图](ROADMAP.md)
- [讨论与建议](https://github.com/zhouPi-314/carepath/discussions)
- [问题反馈](https://github.com/zhouPi-314/carepath/issues)
- [故障排查](docs/troubleshooting.md)

提交前请运行对应测试；不要提交真实个人信息、密钥、数据库或构建产物。

## 安全与隐私

- 合成数据；日志与错误响应不含令牌、密码、证件号、完整手机号或请求体。
- 家属授权按字段与有效期校验，撤销后立即失效。
- 政府聚合执行最小人数抑制；药企只看到达到发布阈值的聚合信号。
- 细节与报告方式见 [SECURITY.md](SECURITY.md)。

## 已知限制

- 未接入真实 HIS、医保、政务、供应链；相关端口为预留契约。
- Docker Compose 未在 CI 实际启动；PostgreSQL 已用本机与 CI 冒烟验证。
- 微信为 `touristappid` 沙箱，未完成真实登录、订阅消息或上线。
- 不构成等保、PIPL、互联网医院或医保合规结论。

## 数据来源与许可

- 合成病例与演示数据；官方公开快照：NMPA、NHSA、NHC、NBS（仓库仅含测试夹具）。
- 医保标签仅为信息展示，不代表实际报销。
- 代码采用 **Apache-2.0 或 MIT 双许可**，任选其一。见 [LICENSE-APACHE](LICENSE-APACHE) 与 [LICENSE-MIT](LICENSE-MIT)。

## English

CarePath is an open-source MVP for treatment-plan progress coordination. It ships a FastAPI modular monolith, a Vue 3 role-based workspace, a Kotlin Compose patient app and a native WeChat mini-program (sandbox). Data is synthetic; official public snapshots are used only as fixtures. This is **not** a medical device, diagnosis tool or production EHR.

Quick start (Windows): `.\scripts\dev-up.cmd`. Requirements: Python 3.13, Node.js 24. See [README.en.md](README.en.md) for the English overview.
