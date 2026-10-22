# 医程共护架构、数据与 API 规格

## 1. 架构选择

后端采用模块化单体。选择理由：

- 五类角色共享同一治疗计划和授权模型，早期拆微服务会增加分布式事务和部署成本。
- 模块化单体可以通过模块边界、应用服务和事务性 Outbox 保留拆分路径。
- 开源开发和小型演示环境下，PostgreSQL、Redis、MinIO 和一个 API 进程即可演示完整业务。

领域模块不得直接依赖 FastAPI、SQLAlchemy 或第三方 SDK。HTTP、数据库、通知和官方数据适配器位于外层。跨聚合根只通过应用服务或 Outbox 事件交互。

## 2. 技术栈

| 层 | 当前实现 |
|---|---|
| API | Python 3.13、FastAPI、Pydantic v2 |
| 数据 | SQLAlchemy 2、Alembic、PostgreSQL；本地演示可用 SQLite |
| 缓存/任务 | Redis 已在 Compose 预留，当前关键通知使用数据库 Outbox |
| 文件 | MinIO 已在 Compose 预留 |
| Web | Vue 3、TypeScript、Vite、Pinia、Element Plus、ECharts |
| Android | Kotlin、Compose、Hilt、Retrofit、Room、WorkManager |
| 微信 | 原生 WXML/WXSS/JavaScript |
| 质量 | pytest、Ruff、ESLint、Vue TSC、Vitest、JUnit、Docker Compose |

## 3. 后端模块

```text
identity          登录、会话、令牌
organizations     机构、成员、认证
patients          患者档案和医院归属
consents          家属绑定、字段级授权、撤销
careplans         模板、计划版本和患者确认
tasks             协同任务和完成记录
medications       用药安排和服药记录
observations      自报指标
alerts            逾期、漏服和阈值提醒
government        脱敏聚合和审核
pharma            产品目录、区域需求和产能
official_data     官方快照和药品/机构匹配
audit             追加式审计
notifications     Outbox 和通知适配器
```

## 4. 数据模型

核心表：

| 表 | 说明 |
|---|---|
| `users` | 登录主体、角色和组织绑定 |
| `organizations` | 医院、监管机构、药企及合作机构 |
| `patient_profiles` | 患者档案，与账号一对一 |
| `caregiver_grants` | 家属授权范围、有效期和状态 |
| `care_plan_templates` | 已发布模板和 JSON 内容 |
| `treatment_plans` | 患者计划、版本、医生和机构 |
| `patient_consents` | 患者对计划的确认/撤销 |
| `care_tasks` | 任务、截止时间、状态和完成者 |
| `medication_schedules` | 用药计划和自报记录 |
| `observations` | 观察指标 |
| `alerts` | 提醒与处理状态 |
| `audit_events` | 临床读取、写入、授权、导出和审核审计 |
| `official_datasets` | 官方数据快照元数据和内容摘要 |
| `drug_products` | 药企药品及其官方匹配状态 |
| `supply_capacity_reports` | 区域月度产能反馈 |
| `outbox_events` | 可靠通知和后续异步事件 |

正式部署使用 PostgreSQL。SQLite 仅用于当前无 Docker 环境下的本地演示和单元测试。Alembic 初始迁移位于 `backend/migrations/versions/`。

## 5. API 约定

- 前缀：`/api/v1`
- JSON：`camelCase`
- 时间：UTC ISO 8601
- ID：UUID 字符串
- 鉴权：移动端 Bearer Token；Web 使用 HttpOnly Cookie，写请求要求 `X-CSRF-Token`
- 错误：FastAPI `detail`，后续统一封装为 `{code,message,requestId,details}`

主要端点：

```text
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
GET  /patient/dashboard
POST /tasks/{taskId}/complete
POST /observations
GET  /care-plan-templates
POST /treatment-plans
GET  /doctor/dashboard
GET  /hospital/dashboard
GET  /organizations/{organizationId}/members
GET  /government/metrics
GET  /government/reviews
POST /government/reviews/{caseId}/decision
GET  /pharma/dashboard
GET  /pharma/demand
POST /pharma/capacity
GET  /admin/official-datasets
POST /admin/official-datasets
GET  /events/stream
```

## 6. FHIR 对齐

内部模型不复制 FHIR 的完整复杂度，但概念映射到 R4：

| 内部对象 | FHIR 资源 |
|---|---|
| 患者 | `Patient` |
| 机构 | `Organization` |
| 医生角色 | `PractitionerRole` |
| 治疗计划 | `CarePlan` |
| 任务 | `Task` |
| 用药计划/记录 | `MedicationRequest` / `MedicationStatement` |
| 观察 | `Observation` |
| 预约 | `Appointment` |
| 授权 | `Consent` |
| 变更来源 | `Provenance` |
| 审计 | `AuditEvent` |

首版不宣称完整 FHIR 互操作。后续 HIS 接入通过适配器完成资源子集转换和契约测试。

## 7. 可替换接口

- `IdentityProviderPort`：本地认证、OIDC、医院 SSO。
- `OfficialCatalogSource`：NMPA、NHSA、NHC、NBS 文件导入。
- `NotificationPort`：Web SSE、Android 推送、微信订阅消息。
- `ObjectStoragePort`：MinIO 或合规对象存储。
- `EncryptionPort`：本地开发密钥、云 KMS 或医院密钥服务。
- `ClockPort`：可测试时间和时区。

## 8. 部署视图

```text
Browser / Android / WeChat
            |
        HTTPS / API
            |
      Nginx 或网关
            |
        FastAPI
       /   |    \
PostgreSQL Redis MinIO
```

Docker Compose 用于演示，不包含高可用、跨院专网、灾备和生产证书。

## 9. 仓储与工作单元边界（第 4 周）

- `carepath/repositories/`：`PatientRepository`、`TreatmentPlanRepository`、`CareTaskRepository` 封装查询，不处理事务。
- `carepath/unit_of_work.py`：`SqlAlchemyUnitOfWork` 持有单个 `AsyncSession` 并暴露仓储；`commit`/`rollback` 由调用方决定，退出上下文时未提交的修改被丢弃。
- `deps.get_unit_of_work`：FastAPI 请求级依赖。
- 迁移范围：`POST /tasks/{taskId}/complete` 已改用 UoW；其余路由继续使用 `get_db`，按模块逐步迁移，不一次性重写。
- 官方数据仓储保留在 `official_data/repository.py`，实现 `OfficialDatasetRepository` 契约。

## 10. 外部系统端口（第 4 周）

| 端口 | 用途 | 当前状态 |
|---|---|---|
| `HospitalInformationSystemPort` | 医院 HIS 患者/就诊/医嘱 | 预留，未配置 |
| `MedicalInsurancePort` | 医保参保/结算状态 | 预留，未配置 |
| `GovernmentDataPort` | 政务数据报送 | 预留，未配置 |
| `SupplyChainPort` | 药企供应/产能 | 预留，未配置 |

统一策略：

- 超时：默认 5 秒，可按请求覆盖，使用 `asyncio.wait_for` 包装。
- 重试：仅对 `TransientIntegrationError`（超时、5xx、连接重置）重试，默认最多 3 次，指数退避上限 2 秒；`PermanentIntegrationError` 不重试。
- 幂等：写操作必须提供 `idempotencyKey`，缺失直接拒绝；`InMemoryIdempotencyStore` 仅用于测试和单进程演示，生产需持久化实现。
- 审计：调用方在 UoW 内写入 `audit_events`（动作、资源、组织、请求 ID），不记录完整请求正文。
- 未配置端口：默认注册表全部为 `UnconfiguredIntegration`，调用直接抛出 `IntegrationNotConfiguredError`，不返回伪造成功。
- 能力查询：`GET /api/v1/admin/integrations` 返回端口、是否配置、能力、重试与超时策略。

