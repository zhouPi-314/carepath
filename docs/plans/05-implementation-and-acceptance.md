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
| 第 2 周 | PostgreSQL 与小数据库集成 | Alembic 空库升级和 SQLite/PostgreSQL 对照测试通过 | 已完成 |
| 第 3 周 | 官方数据适配接口 | NMPA/NHSA/NHC/NBS 导入器契约、快照校验和错误状态测试 | 已完成 |
| 第 4 周 | 外部数据库/仓库端口 | 聚合根 UnitOfWork/Repository 接口，SQLAlchemy 实现可替换 | 已完成 |
| 第 5 周 | Web 主流程与 E2E | 六类账号关键路径通过 Playwright 和小型测试库 | 已完成 |
| 第 6 周 | Android 与微信可运行验证 | Android APK 构建、JUnit；微信开发者工具完成沙箱流程 | 已完成 |
| 第 7 周 | 安全、错误处理和文档 | 越权、授权撤销、重复导入、断网补传测试通过 | 未开始 |
| 第 8 周 | v0.1.0 发布准备 | 版本号、变更日志、贡献指南、安全政策、演示数据和截图 | 未开始 |

## 4. 第 1 周执行记录（2026-10-22）

- [x] 完整阅读交接文档、README、规格和实施计划，核对 git status 与现有测试。
- [x] 建立基线提交 `41ddd0b chore: prepare open-source project handoff`（73 个文件，仅源码与 Markdown；不含 .env、数据库、APK、构建产物、PDF/DOCX）。
- [x] 新增 `CONTRIBUTING.md`、`SECURITY.md`、`CHANGELOG.md`、`CODE_OF_CONDUCT.md`。
- [x] 新增 GitHub issue 模板（缺陷/功能/配置）与 PR 模板。
- [x] 新增 `.github/workflows/ci.yml`：后端 pytest+ruff、Web test/lint/build、微信 test/check、Android `:logic:test`。
- [x] 新增许可证决策记录 `docs/decisions/0001-license-pending.md`（待项目所有者确认，未单方面添加 LICENSE 文本）。
- [x] 项目所有者确认 Apache-2.0，已添加 `LICENSE` 标准文本并更新决策记录。
- [ ] 微信开发者工具自动预览（需开启 CLI 服务端口）。
- [x] Linux CI 实际跑通：GitHub Actions 五个作业全部通过（[运行记录](https://github.com/zhouPi-314/carepath/actions/runs/39768750706)）。
- [ ] Docker Compose 实际启动（本机无 Docker；PostgreSQL 冒烟已用本机 PostgreSQL 18 临时集群与 CI 服务容器替代验证）。

## 5. 第 2 周执行记录（2026-10-22）

- [x] SQLite 功能测试扩充到 15 个用例：家属授权撤销后拒绝访问、跨医院读取计划被拒绝、官方快照重复校验值返回 409、药企信号满足 3 机构 / 50 患者月阈值。
- [x] SQLite 测试启用外键校验（`PRAGMA foreign_keys=ON`），使本地 SQLite 也能捕获 PostgreSQL 会拒绝的插入顺序错误。
- [x] 修复 `seed.py` 的跨库插入顺序：在患者、治疗计划、官方数据集之后显式 flush，避免 PostgreSQL 外键失败（SQLite 默认不校验外键，此前被掩盖）。
- [x] 新增 `backend/scripts/postgres_smoke.py`：清空 schema → Alembic 空库升级 → 演示数据导入 → 患者登录 → 任务完成 → 政府聚合 → 官方快照重复导入 409。
- [x] 本机 PostgreSQL 18 临时集群实测通过：69 用户 / 61 计划 / 4 快照；患者登录、任务完成、聚合无患者标识、重复导入 409。
- [x] CI 新增 `postgres-smoke` 作业（PostgreSQL 17 服务容器），与 SQLite 后端作业并行。
- [x] 冒烟结束停止临时集群并清理数据目录，不保留测试数据库。
- [x] GitHub Actions `postgres-smoke` 作业通过（[运行记录](https://github.com/zhouPi-314/carepath/actions/runs/39768750706)）。

## 6. 第 3 周执行记录（2026-10-22）

- [x] 新增 `carepath/official_data` 包：`contracts`（`OfficialCatalogSource` / `OfficialDatasetRepository` / 错误类型）、`normalization`（校验、校验值、状态）、`sources`（四来源解析器）、`repository`（SQLAlchemy 适配器）、`service`（导入编排）。
- [x] 四个来源的小型 JSON 夹具与解析器：NMPA 药品批准文号、NHSA 医保标签、NHC 机构、NBS 区域人口；医保标签保留“不代表实际报销”声明。
- [x] 校验与状态：https 来源链接、审核人、SHA-256、发布日期≤生效日期；`UNVERIFIED` 优先于 `STALE`（生效后 365 天）。
- [x] 管理端接口：来源列表与按来源导入；重复 409、非法 422、未知来源 404、非管理员 403。
- [x] 新增 18 个测试（单元 + API），后端共 33 个用例通过；SQLite 与 PostgreSQL 冒烟均通过。
- [x] GitHub Actions 五个作业通过（[运行记录](https://github.com/zhouPi-314/carepath/actions/runs/39775301487)）。
- [ ] 真实官方数据人工快照导入（需项目所有者提供合法导出文件，不在本阶段伪造）。

## 7. 第 4 周执行记录（2026-10-22）

- [x] 新增 `carepath/repositories/`：患者、治疗计划、协同任务三个聚合根的查询仓储。
- [x] 新增 `carepath/unit_of_work.py` 与 `deps.get_unit_of_work`；`POST /tasks/{taskId}/complete` 已迁移到 UoW，任务状态、审计与 Outbox 在同一事务提交。
- [x] 新增 3 个 UoW/仓储测试：查询范围、提交持久化、回滚丢弃。
- [x] 新增 `carepath/integrations/`：HIS、医保、政务、供应链四个预留端口，超时/重试/幂等/审计策略，未配置端口显式失败。
- [x] 新增 `GET /api/v1/admin/integrations` 能力查询；新增 9 个集成测试。
- [x] 后端共 45 个测试通过；SQLite 与 PostgreSQL 冒烟均通过。
- [x] GitHub Actions 五个作业通过（[运行记录](https://github.com/zhouPi-314/carepath/actions/runs/39778439908)）。
- [ ] 其余路由迁移到 UoW（按模块逐步，不在本阶段一次性重写）。
- [ ] 真实外部系统联调（需合作授权；未授权前保持未配置并记录）。

## 8. 第 5 周执行记录（2026-10-22）

- [x] 新增 Playwright 配置与 10 个 Web E2E 用例：六角色登录与工作台、患者完成任务、政府聚合指标、退出登录。
- [x] Web 预览服务器增加 `/api`、`/health` 反向代理；E2E 使用独立 SQLite 库 `carepath-e2e.db`，启动时自动演示数据。
- [x] CI 新增 `web-e2e` 作业：安装后端、Playwright chromium、构建并运行 E2E。
- [x] 新增后端聚合抑制 API 测试：小样本区域（<10 活跃计划）整体抑制，计数/百分比/提醒均为 null。
- [x] 后端 46 个测试通过；Web 单元测试、lint、生产构建通过；Playwright 用例可被 `--list` 识别。
- [x] E2E 在 GitHub Actions 实际执行通过（[运行记录](https://github.com/zhouPi-314/carepath/actions/runs/39798823970)）；本机浏览器下载受网络限制，本地用 `playwright test --list` 校验用例可执行。
- [x] 授权撤销、跨机构、政府聚合抑制、药企发布阈值在 API 层有测试覆盖；UI 端授权撤销操作面后续补充。

## 9. 第 6 周执行记录（2026-10-22）

- [x] 本机 `:app:assembleDebug` 构建成功，APK 输出 `apps/android/app/build/outputs/apk/debug/app-debug.apk`。
- [x] CI Android 作业新增 `:app:assembleDebug`，与 `:logic:test` 同环境复现。
- [x] 微信新增 8 个沙箱流程测试（共 11 个）：登录成功/失败、首页缓存与任务映射、后端不可用缓存回退、无缓存错误、任务完成幂等提交、完成失败提示、退出清理。
- [x] 微信 `npm test` 11 passed，`npm run check` 通过；无 AppID 的 `touristappid` 沙箱边界保持不变。
- [x] GitHub Actions 六个作业通过，Android 构建与微信 11 个测试均在 CI 运行（[运行记录](https://github.com/zhouPi-314/carepath/actions/runs/39882763804)）。
- [ ] 微信开发者工具人工预览（本机 CLI 服务端口未开启；不伪造自动预览结果）。
- [ ] Android 仪器化测试（本阶段只要求 JVM 逻辑测试与 debug 构建）。

## 10. 全链验收场景

1. 医生创建计划，患者确认，家属在授权范围内完成自护任务。
2. 家属授权撤销后，Web、Android 和微信端均不能继续访问受限数据。
3. 医院 A 管理员和医生无法读取医院 B 的患者计划。
4. 政府区域缺少足够样本时显示“已抑制”，接口中不存在患者 ID。
5. 药企仅能看到达到 3 家机构、50 个患者月的区域信号。
6. 官方快照重复导入返回冲突；不匹配药品标为未验证。
7. Android 断网显示缓存，恢复网络后任务只提交一次。
8. 微信开发端无 AppID 时仍能使用沙箱账号，并明确显示边界。

## 11. 完成定义

- 逻辑变更具有先失败后通过的测试。
- API 变更同步 OpenAPI 与前端客户端。
- 数据库变更具有可执行迁移。
- 新增角色和字段同步权限矩阵、审计和数据分类。
- 无真实个人信息、明文密钥或生产默认密码进入仓库。
- 文档中的“已完成”与真实命令输出一致。