# 医程共护 CarePath

医程共护是一个面向教学、竞赛和工程展示的治疗方案进度协同 MVP。它覆盖患者、家属、医生、医院、政府监管和药企角色，并提供 Web、Android 与微信小程序客户端。

> 本项目使用合成病例和官方公开数据快照。它不提供诊断或治疗建议，不处理真实处方、医保结算或行政处置，也不得直接用于真实患者。

## 仓库结构

- `backend/`：FastAPI 模块化单体、数据库模型、测试与演示数据。
- `apps/web/`：多角色 Web 工作台。
- `apps/android/`：原生 Android 患者/家属端。
- `apps/wechat/`：原生微信小程序。
- `docs/`：需求、架构、安全、调研、实施和验收文档。
- `ops/`：容器化与本地运行配置。

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
