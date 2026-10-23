# 医程共护 CarePath

医程共护是一个面向开源工程协作、教学和后续试点的治疗方案进度协同 MVP。它覆盖患者、家属、医生、医院、政府监管和药企角色，并提供 Web、Android 与微信小程序客户端。

> 本项目使用合成病例和官方公开数据快照。它不提供诊断或治疗建议，不处理真实处方、医保结算或行政处置，也不得直接用于真实患者。竞赛和答辩材料不作为当前主线，只在后续需要时单独扩展。

当前目标是在 **8 周内**整理为可公开协作的 GitHub 项目。项目文档只提交 Markdown 等适合版本控制的格式；Word、PDF 和竞赛材料已移出仓库，不参与当前主线。

## 仓库结构

- `backend/`：FastAPI 模块化单体、数据库模型、测试与演示数据。
- `apps/web/`：多角色 Web 工作台。
- `apps/android/`：原生 Android 患者/家属端。
- `apps/wechat/`：原生微信小程序。
- `docs/`：需求、架构、安全、调研、实施和验收文档。
- `ops/`：容器化与本地运行配置。
- `.github/`：issue/PR 模板与 CI 工作流。

交接开发请先阅读 [HANDOFF_TO_DSH.md](HANDOFF_TO_DSH.md)。

## 社区文档

- [贡献指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)
- [变更日志](CHANGELOG.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [文档索引](docs/README.md)
- [许可证决策记录](docs/decisions/0001-license-dual.md)（Apache-2.0 OR MIT）

## 快速开始

后端：

```powershell
cd backend
py -3.13 -m venv .venv
.\venv\Scripts\python -m pip install -e ".[dev]"
.\venv\Scripts\python -m carepath.seed
.\venv\Scripts\uvicorn carepath.main:app --reload --port 8000
```

Web：

```powershell
cd apps/web
pnpm install
pnpm dev
```

演示账号统一密码为 `CarePath123!`：

| 账号 | 角色 |
|---|---|
| `patient` | 患者 |
| `caregiver` | 家属 |
| `doctor` | 医生 |
| `hospital` | 医院管理员 |
| `regulator` | 政府监管者 |
| `pharma` | 药企用户 |

开发环境默认使用 SQLite 以便无 Docker 启动；设置 `DATABASE_URL=postgresql+asyncpg://...` 后使用 PostgreSQL。生产配置必须使用 PostgreSQL、HTTPS、真实密钥管理和正式身份提供方。

## 测试

仓库包含 GitHub Actions CI（`.github/workflows/ci.yml`），本地可执行相同检查：

```powershell
# 后端
cd backend
.\venv\Scripts\python -m pytest -q
.\venv\Scripts\python -m ruff check src tests migrations

# Web（pnpm 可通过 corepack 启用）
cd apps/web
pnpm test
pnpm lint
pnpm build

# 微信
cd apps/wechat
npm test
npm run check

# Web E2E（需先安装 Playwright 浏览器）
cd apps/web
pnpm exec playwright install chromium
pnpm test:e2e

# PostgreSQL 冒烟（需要可用的 PostgreSQL）
cd backend
$env:CAREPATH_SMOKE_DATABASE_URL='postgresql+asyncpg://user:pass@127.0.0.1:5432/carepath_smoke'
.\venv\Scripts\python scripts\postgres_smoke.py

# Android 纯逻辑模块（JDK 17+）
cd apps/android
./gradlew :logic:test
```

## 8 周开源路线

| 周次 | 重点 | 状态 |
|---|---|---|
| 1 | 仓库整理、许可证确认、GitHub 文档与 CI | 进行中 |
| 2 | PostgreSQL 与小数据库功能对照 | 已完成 |
| 3 | NMPA/NHSA/NHC/NBS 官方数据适配器契约 | 已完成 |
| 4 | 官方数据仓储与外部数据库端口 | 已完成 |
| 5 | Web 主流程 E2E 与小型测试库 | 已完成 |
| 6 | Android、微信小程序可运行验证 | 已完成 |
| 7 | 安全、越权、授权撤销、断网补传与错误处理 | 进行中 |
| 8 | v0.1.0 发布、变更日志、贡献与安全文档 | 未开始 |

详细拆解见 [`docs/plans/05-implementation-and-acceptance.md`](docs/plans/05-implementation-and-acceptance.md)。

## 开源许可

本项目采用 **Apache-2.0 或 MIT 双许可**，使用者可任选其一：

- [Apache License 2.0](LICENSE-APACHE)：包含明确的专利授权条款。
- [MIT License](LICENSE-MIT)：最简宽松许可。

决策记录见 [`docs/decisions/0001-license-dual.md`](docs/decisions/0001-license-dual.md)。

Word、PDF、原始构想和渲染 QA 文件归档在仓库外：

```text
D:\项目设计\医院治疗方案进度协同体02-archive\competition-materials
```