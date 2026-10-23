# 开发交接说明

- 版本：**v0.1.0**（2026-10-23）
- 状态：8 周开源整理完成；CI 7 个作业全绿；标签 `v0.1.0` 已推送。
- 适用对象：后续维护者、贡献者、接手试点的工程团队。

本文件是开发上下文入口。产品与架构细节以 `docs/spec/` 为准，发布信息以 `docs/release/v0.1.0.md` 为准。

## 1. 当前状态

- 后端：FastAPI 模块化单体、SQLAlchemy 2、Alembic、SQLite 演示与 PostgreSQL 冒烟。
- 角色：患者、家属、医生、医院管理员、政府监管、药企、系统管理员。
- 已交付：治疗计划/任务闭环、家属字段级授权、医院隔离、政府小样本抑制、药企双阈值聚合、官方快照导入、仓储/UnitOfWork 边界、外部端口预留。
- 客户端：Vue 3 多角色工作台、Android 患者/家属端、微信小程序沙箱。
- 质量：后端 51 个测试、Web 单元测试与 10 个 E2E、微信 11 个测试、Android 构建与 JVM 测试、安全扫描。
- 演示账号与密码按角色区分，见 `README.md`。

## 2. 架构与模块

```text
backend/src/carepath/
  main.py            FastAPI 入口、请求 ID、统一错误、健康检查
  deps.py            认证、角色依赖、UnitOfWork 依赖
  security.py        scrypt、JWT、CSRF
  policies.py        RBAC/ABAC 判定
  services.py        患者仪表盘与访问检查
  repositories/      患者、计划、任务仓储
  unit_of_work.py    事务边界
  official_data/     官方快照契约、解析器、校验、仓储、导入服务
  integrations/      HIS/医保/政务/供应链端口与重试/幂等策略
  routers/           按角色拆分的 HTTP 适配层
  seed.py            合成演示数据
```

领域规则不依赖 FastAPI/SQLAlchemy；HTTP、数据库、外部系统适配器位于外层。跨聚合根通过应用服务或 Outbox 交互。

## 3. 本地启动与测试

最短路径：`scripts/dev-up.cmd`（Windows，一键安装并启动）。

手动命令与全部测试命令见 `README.md` 的「手动启动」「测试与质量」两节。常用：

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check src tests migrations scripts
```

数据库变更必须补 Alembic 迁移；API 变更同步前端类型与文档。

## 4. 代码规范（摘要）

- 模块化单体，不拆微服务；只实现当前需求，不预建空抽象。
- FastAPI 路由只做 HTTP 适配；业务规则放服务/策略层。
- 权限 fail-closed；新增角色/字段同步权限矩阵、审计与数据分类。
- 标识使用 UUID 字符串，时间写入 UTC；JSON 使用 camelCase，数据库 snake_case。
- 日志不记录请求体、令牌、密码、证件号、完整手机号或诊疗正文。
- 提交使用 Conventional Commits；改动附对应测试。
- 不提交 `.env`、数据库、APK、构建产物、PDF/DOCX 或真实个人信息。

## 5. 安全与合规边界

- 仅使用合成病例与公开数据快照；不提供诊断、处方、医保结算或行政处置。
- 未接入真实 HIS/医保/政务/供应链；端口未配置时显式失败。
- 家属授权按字段与有效期校验，撤销立即生效。
- 政府聚合最小人数抑制；药企仅见达到阈值的聚合信号。
- 本项目不等同于完成等保、PIPL、互联网医院准入或医保对接。
- 漏洞报告与限制见 `SECURITY.md`。

## 6. 文档索引

- `README.md` / `README.en.md`：项目入口与快速开始。
- `ROADMAP.md`：已交付、近期、中期、长期与明确不做。
- `docs/spec/`：需求、架构、安全、官方数据。
- `docs/plans/05-implementation-and-acceptance.md`：逐周执行记录与验收。
- `docs/release/v0.1.0.md`：发布说明、安装、配置、限制。
- `docs/troubleshooting.md`：常见问题与修复。
- `docs/decisions/`：许可证等决策记录。
- `CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`。

## 7. 后续工作与交接注意

- 优先事项见 `ROADMAP.md`；外部系统落地需合作授权与接口文档。
- 不要 `git reset --hard`、不要 force-push 共享分支；保留历史与未提交改动。
- 数据库迁移不可回退已发布版本；新增字段先兼容再清理。
- 真实试点前必须完成合规评估与临床内容审核。
