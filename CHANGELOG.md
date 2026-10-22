# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 与语义化版本。

## [未发布]

### 新增

- 开源仓库整理：交接文档、社区文档（贡献指南、安全政策、行为准则、变更日志）。
- GitHub Actions CI 骨架（后端、Web、微信、Android 纯逻辑模块）。
- 8 周开源路线与验收计划（见 `docs/plans/05-implementation-and-acceptance.md`）。

### 第 2 周：小型数据库验证

- 新增 PostgreSQL 冒烟脚本 `backend/scripts/postgres_smoke.py`（空库迁移、演示数据、登录、任务、聚合、重复导入 409）。
- CI 增加 PostgreSQL 17 服务容器作业；后端 SQLite 测试启用外键校验。
- 修复 `seed.py` 在 PostgreSQL 下的外键插入顺序问题（显式 flush）。
- SQLite 功能测试新增家属授权撤销、跨院读取、重复快照、药企发布阈值四类场景。

### 第 3 周：官方数据适配契约

- 新增 `carepath/official_data`：`OfficialCatalogSource` 与 `OfficialDatasetRepository` 契约、校验/状态规则、四来源解析器、SQLAlchemy 仓储适配器和导入服务。
- 管理端新增来源列表与按来源导入接口；重复校验值 409、非法快照 422、未知来源 404。
- 新增四个来源的 JSON 测试夹具与 18 个测试，后端测试总数 33。

### 第 4 周：仓储/工作单元与外部端口

- 新增 `carepath/repositories/`（患者、治疗计划、任务）与 `SqlAlchemyUnitOfWork`；任务完成接口改用 UoW。
- 新增 `carepath/integrations/`：HIS、医保、政务、供应链四个预留端口，超时/重试/幂等/审计策略，未配置时显式失败。
- 新增 `GET /api/v1/admin/integrations` 能力查询与 12 个测试；后端测试总数 45。

### 第 5 周：Web 主流程 E2E

- 新增 Playwright 配置与 10 个 Web E2E 用例，覆盖六角色登录、患者任务、政府聚合与退出。
- Web 预览服务器增加 API 代理；CI 新增 `web-e2e` 作业。
- 后端新增小样本区域聚合抑制测试；后端测试总数 46。

### 既有基线（整理前已实现）

- FastAPI 模块化单体、SQLAlchemy 模型、Alembic 初始迁移和合成演示数据。
- 五类业务角色与系统管理员权限、家属授权、治疗计划与任务闭环。
- 政府最小人数抑制、药企双阈值聚合和官方数据快照通用导入。
- Vue 多角色 Web 工作台、Android 患者/家属端、微信小程序沙箱端。
- Docker Compose（PostgreSQL、Redis、MinIO、后端、Web）与 Nginx 配置。

### 许可证

- 项目所有者确认采用 **Apache-2.0 或 MIT 双许可**：新增 `LICENSE-APACHE` 与 `LICENSE-MIT`，使用者可任选其一；决策记录见 `docs/decisions/0001-license-dual.md`。