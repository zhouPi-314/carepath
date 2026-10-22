# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 与语义化版本。

## [未发布]

### 新增

- 开源仓库整理：交接文档、社区文档（贡献指南、安全政策、行为准则、变更日志）。
- GitHub Actions CI 骨架（后端、Web、微信、Android 纯逻辑模块）。
- 8 周开源路线与验收计划（见 `docs/plans/05-implementation-and-acceptance.md`）。

### 既有基线（整理前已实现）

- FastAPI 模块化单体、SQLAlchemy 模型、Alembic 初始迁移和合成演示数据。
- 五类业务角色与系统管理员权限、家属授权、治疗计划与任务闭环。
- 政府最小人数抑制、药企双阈值聚合和官方数据快照通用导入。
- Vue 多角色 Web 工作台、Android 患者/家属端、微信小程序沙箱端。
- Docker Compose（PostgreSQL、Redis、MinIO、后端、Web）与 Nginx 配置。

### 许可证

- 项目所有者确认采用 **Apache License 2.0**，仓库根目录新增 `LICENSE` 标准文本；决策记录见 `docs/decisions/0001-license-apache-2.0.md`。
