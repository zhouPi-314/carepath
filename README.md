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

交接开发请先阅读 [HANDOFF_TO_DSH.md](HANDOFF_TO_DSH.md)。

## 快速开始

后端：

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m carepath.seed
.\.venv\Scripts\uvicorn carepath.main:app --reload --port 8000
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

## 8 周开源路线

| 周次 | 重点 |
|---|---|
| 1 | 仓库整理、许可证确认、GitHub 文档与 CI |
| 2 | PostgreSQL 与小数据库功能对照 |
| 3 | NMPA/NHSA/NHC/NBS 官方数据适配器契约 |
| 4 | 官方数据仓储与外部数据库端口 |
| 5 | Web 主流程 E2E 与小型测试库 |
| 6 | Android、微信小程序可运行验证 |
| 7 | 安全、越权、授权撤销、断网补传与错误处理 |
| 8 | v0.1.0 发布、变更日志、贡献与安全文档 |

详细拆解见 [`docs/plans/05-implementation-and-acceptance.md`](docs/plans/05-implementation-and-acceptance.md)。

## 开源状态

项目当前尚未选定开源许可证。没有明确许可证的公开仓库默认保留全部权利，不构成有效开源授权。正式发布前必须由项目所有者确认许可证；若需要明确专利授权，可优先评估 Apache-2.0，若只需最简宽松许可可评估 MIT。

Word、PDF、原始构想和渲染 QA 文件归档在仓库外：

```text
D:\项目设计\医院治疗方案进度协同体02-archive\competition-materials
```
