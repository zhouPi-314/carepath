# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 与语义化版本。

## [0.1.0] - 2026-10-23

首个开源 MVP 版本。使用合成病例与官方公开数据快照，仅用于教学、工程演示和后续试点评估，**不用于真实诊疗**。

### 新增（整理前基线）

- FastAPI 模块化单体、SQLAlchemy 模型、Alembic 初始迁移和合成演示数据。
- 五类业务角色与系统管理员权限、家属授权、治疗计划与任务闭环。
- 政府最小人数抑制、药企双阈值聚合和官方数据快照通用导入。
- Vue 多角色 Web 工作台、Android 患者/家属端、微信小程序沙箱端。
- Docker Compose（PostgreSQL、Redis、MinIO、后端、Web）与 Nginx 配置。

### 第 2 周：小型数据库验证

- 新增 PostgreSQL 冒烟脚本 `backend/scripts/postgres_smoke.py`（空库迁移、演示数据、登录、任务、聚合、重复导入 409）。
- CI 增加 PostgreSQL 17 服务容器作业；后端 SQLite 测试启用外键校验。
- 修复 `seed.py` 在 PostgreSQL 下的外键插入顺序问题（显式 flush）。
- SQLite 功能测试新增家属授权撤销、跨院读取、重复快照、药企发布阈值四类场景。

### 第 3 周：官方数据适配契约

- 新增 `carepath/official_data`：`OfficialCatalogSource` 与 `OfficialDatasetRepository` 契约、校验/状态规则、四来源解析器、SQLAlchemy 仓储适配器和导入服务。
- 管理端新增来源列表与按来源导入接口；重复校验值 409、非法快照 422、未知来源 404。
- 新增四个来源的 JSON 测试夹具与 18 个测试。

### 第 4 周：仓储/工作单元与外部端口

- 新增 `carepath/repositories/`（患者、治疗计划、任务）与 `SqlAlchemyUnitOfWork`；任务完成接口改用 UoW。
- 新增 `carepath/integrations/`：HIS、医保、政务、供应链四个预留端口，超时/重试/幂等/审计策略，未配置时显式失败。
- 新增 `GET /api/v1/admin/integrations` 能力查询与 12 个测试。

### 第 5 周：Web 主流程 E2E

- 新增 Playwright 配置与 10 个 Web E2E 用例，覆盖六角色登录、患者任务、政府聚合与退出。
- Web 预览服务器增加 API 代理；CI 新增 `web-e2e` 作业。
- 后端新增小样本区域聚合抑制测试。

### 第 6 周：移动端可运行验证

- CI Android 作业新增 `:app:assembleDebug`；本机 debug APK 构建成功。
- 微信小程序新增 8 个沙箱流程测试（登录、首页缓存、离线回退、任务完成、退出），共 11 个 Node 测试。

### 第 7 周：安全与错误处理

- 新增日志脱敏工具与统一参数校验错误结构；请求日志不记录请求体。
- 新增任务完成幂等重试测试；依赖升级消除 Python 已知漏洞，Node 侧修复 tinypool critical 告警。
- CI 新增安全扫描作业：gitleaks、pip-audit、bandit、pnpm audit。

### 变更

- 运行依赖升级：FastAPI 0.161、starlette 1.9、pytest 9.1、pytest-asyncio 1.4。
- Web 通过 `pnpm-workspace.yaml` 将 `tinypool` 覆盖到 2.2.0。
- `/health` 返回 `version` 字段，与应用版本保持一致。

### 安全

- 日志与错误响应不包含令牌、密码、证件号、完整手机号或请求体。
- 秘密扫描、依赖漏洞扫描和静态扫描在 CI 中执行。

### 已知限制

- 本机无 Docker，Docker Compose 未实际启动；PostgreSQL 已用本机 18 与 CI 17 冒烟验证。
- 微信开发者工具自动预览未执行（`touristappid` 沙箱，需人工打开）。
- 本机 Windows 中文路径下 Gradle JUnit worker 受限，逻辑测试以 CI Linux 为准。
- 未接入真实 HIS、医保、政务或供应链系统；端口为预留契约。

### 许可证

- 项目所有者确认采用 **Apache-2.0 或 MIT 双许可**：`LICENSE-APACHE` 与 `LICENSE-MIT`，使用者可任选其一；决策记录见 `docs/decisions/0001-license-dual.md`。
