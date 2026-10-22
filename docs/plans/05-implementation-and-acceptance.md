# 医程共护实施与验收计划

## 1. 已完成基线

- [x] 建立 Python 模块化单体、SQLAlchemy 模型、Alembic 初始迁移和演示数据。
- [x] 实现密码哈希、访问/刷新令牌、Cookie/Bearer 双入口和 CSRF 校验。
- [x] 实现五类业务角色与系统管理员的权限控制。
- [x] 实现治疗模板、计划、任务、用药、观察、提醒和患者/家属闭环。
- [x] 实现医院、政府聚合、药企需求和官方数据接口。
- [x] 实现 Vue 多角色 Web、角色独立面板和生产构建。
- [x] 实现 Android 患者/家属端源码、Room 缓存、WorkManager 提醒和 debug APK。
- [x] 实现原生微信小程序登录、患者任务和本地缓存。
- [x] 提供 Docker Compose、PostgreSQL、Redis、MinIO 和 Nginx 配置。

## 2. 当前验证命令

后端：

```powershell
cd backend
.\venv\Scripts\python -m pytest -q
.\venv\Scripts\python -m ruff check src tests migrations
.\venv\Scripts\alembic.exe upgrade head
```

Web：

```powershell
cd apps/web
pnpm test
pnpm lint
pnpm build
```

Android：

```powershell
cd apps/android
$env:JAVA_HOME='D:\Development\Android\AndroidStudio\jbr'
& 'D:\Development\Cache\gradle\gradle-9.6.0\bin\gradle.bat' :app:assembleDebug
```

微信：

```powershell
cd apps/wechat
npm test
npm run check
```

## 3. 8 周开源交付路线

| 周次 | 目标 | 完成标准 | 状态 |
|---|---|---|---|
| 第 1 周 | 仓库整理、许可证决策、GitHub 文档、CI | 新开发者可按 README 启动；CI 跑通现有检查 | 进行中 |
| 第 2 周 | PostgreSQL 与小数据库集成 | Alembic 空库升级和 SQLite/PostgreSQL 对照测试通过 | 进行中 |
| 第 3 周 | 官方数据适配接口 | NMPA/NHSA/NHC/NBS 导入器契约、快照校验和错误状态测试 | 未开始 |
| 第 4 周 | 外部数据库/仓库端口 | 聚合根 UnitOfWork/Repository 接口，SQLAlchemy 实现可替换 | 未开始 |
| 第 5 周 | Web 主流程与 E2E | 六类账号关键路径通过 Playwright 和小型测试库 | 未开始 |
| 第 6 周 | Android 与微信可运行验证 | Android APK 构建、JUnit；微信开发者工具完成沙箱流程 | 未开始 |
| 第 7 周 | 安全、错误处理和文档 | 越权、授权撤销、重复导入、断网补传测试通过 | 未开始 |
| 第 8 周 | v0.1.0 发布准备 | 版本号、变更日志、贡献指南、安全政策、演示数据和截图 | 未开始 |

## 4. 第 1 周执行记录（2026-10-22）

- [x] 完整阅读交接文档、README、规格和实施计划，核对 git status 与现有测试。
- [x] 建立基线提交 `41ddd0b chore: prepare open-source project handoff`（73 个文件，仅源码与 Markdown；不含 .env、数据库、APK、构建产物、PDF/DOCX）。
- [x] 新增 `CONTRIBUTING.md`、`SECURITY.md`、`CHANGELOG.md`、`CODE_OF_CONDUCT.md`。
- [x] 新增 GitHub issue 模板（缺陷/功能/配置）与 PR 模板。
- [x] 新增 `.github/workflows/ci.yml`：后端 pytest+ruff、Web test/lint/build、微信 test/check、Android `:logic:test`。
- [x] 新增许可证决策记录 `docs/decisions/0001-license-pending.md`（待项目所有者确认，未单方面添加 LICENSE 文本）。
- [ ] 许可证正式确认并添加 `LICENSE` 文本（等待项目所有者）。
- [ ] 微信开发者工具自动预览（需开启 CLI 服务端口）。
- [ ] Linux CI 实际跑通（提交后由 GitHub Actions 验证）。
- [ ] Docker Compose 实际启动（本机无 Docker）。

## 5. 第 2 周执行记录（2026-10-22）

- [x] SQLite 功能测试扩充到 15 个用例：家属授权撤销后拒绝访问、跨医院读取计划被拒绝、官方快照重复校验值返回 409、药企信号满足 3 机构 / 50 患者月阈值。
- [x] SQLite 测试启用外键校验（`PRAGMA foreign_keys=ON`），使本地 SQLite 也能捕获 PostgreSQL 会拒绝的插入顺序错误。
- [x] 修复 `seed.py` 的跨库插入顺序：在患者、治疗计划、官方数据集之后显式 flush，避免 PostgreSQL 外键失败（SQLite 默认不校验外键，此前被掩盖）。
- [x] 新增 `backend/scripts/postgres_smoke.py`：清空 schema → Alembic 空库升级 → 演示数据导入 → 患者登录 → 任务完成 → 政府聚合 → 官方快照重复导入 409。
- [x] 本机 PostgreSQL 18 临时集群实测通过：69 用户 / 61 计划 / 4 快照；患者登录、任务完成、聚合无患者标识、重复导入 409。
- [x] CI 新增 `postgres-smoke` 作业（PostgreSQL 17 服务容器），与 SQLite 后端作业并行。
- [x] 冒烟结束停止临时集群并清理数据目录，不保留测试数据库。

## 6. 全链验收场景

1. 医生创建计划，患者确认，家属在授权范围内完成自护任务。
2. 家属授权撤销后，Web、Android 和微信端均不能继续访问受限数据。
3. 医院 A 管理员和医生无法读取医院 B 的患者计划。
4. 政府区域缺少足够样本时显示“已抑制”，接口中不存在患者 ID。
5. 药企仅能看到达到 3 家机构、50 个患者月的区域信号。
6. 官方快照重复导入返回冲突；不匹配药品标为未验证。
7. Android 断网显示缓存，恢复网络后任务只提交一次。
8. 微信开发端无 AppID 时仍能使用沙箱账号，并明确显示边界。

## 6. 完成定义

- 逻辑变更具有先失败后通过的测试。
- API 变更同步 OpenAPI 与前端客户端。
- 数据库变更具有可执行迁移。
- 新增角色和字段同步权限矩阵、审计和数据分类。
- 无真实个人信息、明文密钥或生产默认密码进入仓库。
- 文档中的“已完成”与真实命令输出一致。