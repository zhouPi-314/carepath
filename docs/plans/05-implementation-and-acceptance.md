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
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\ruff check src tests migrations
.\.venv\Scripts\alembic.exe upgrade head
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

| 周次 | 目标 | 完成标准 |
|---|---|---|
| 第 1 周 | 仓库整理、许可证决策、GitHub 文档、CI | 新开发者可按 README 启动；CI 跑通现有检查 |
| 第 2 周 | PostgreSQL 与小数据库集成 | Alembic 空库升级和 SQLite/PostgreSQL 对照测试通过 |
| 第 3 周 | 官方数据适配接口 | NMPA/NHSA/NHC/NBS 导入器契约、快照校验和错误状态测试 |
| 第 4 周 | 外部数据库/仓库端口 | 聚合根 UnitOfWork/Repository 接口，SQLAlchemy 实现可替换 |
| 第 5 周 | Web 主流程与 E2E | 六类账号关键路径通过 Playwright 和小型测试库 |
| 第 6 周 | Android 与微信可运行验证 | Android APK 构建、JUnit；微信开发者工具完成沙箱流程 |
| 第 7 周 | 安全、错误处理和文档 | 越权、授权撤销、重复导入、断网补传测试通过 |
| 第 8 周 | v0.1.0 发布准备 | 版本号、变更日志、贡献指南、安全政策、演示数据和截图 |

## 4. 全链验收场景

1. 医生创建计划，患者确认，家属在授权范围内完成自护任务。
2. 家属授权撤销后，Web、Android 和微信端均不能继续访问受限数据。
3. 医院 A 管理员和医生无法读取医院 B 的患者计划。
4. 政府区域缺少足够样本时显示“已抑制”，接口中不存在患者 ID。
5. 药企仅能看到达到 3 家机构、50 个患者月的区域信号。
6. 官方快照重复导入返回冲突；不匹配药品标为未验证。
7. Android 断网显示缓存，恢复网络后任务只提交一次。
8. 微信开发端无 AppID 时仍能使用沙箱账号，并明确显示边界。

## 5. 完成定义

- 逻辑变更具有先失败后通过的测试。
- API 变更同步 OpenAPI 与前端客户端。
- 数据库变更具有可执行迁移。
- 新增角色和字段同步权限矩阵、审计和数据分类。
- 无真实个人信息、明文密钥或生产默认密码进入仓库。
- 文档中的“已完成”与真实命令输出一致。
