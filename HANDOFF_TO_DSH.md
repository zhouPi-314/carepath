# 医程共护 CarePath 开发交接文档

**交接日期：** 2026-10-22  
**交接对象：** dsh / 后续开发 Agent  
**仓库路径：** `D:\项目设计\医院治疗方案进度协同体02`  
**当前分支：** `feature/ycth-mvp`

## 1. 先读什么

按顺序阅读：

1. `README.md`：项目定位、启动方式、演示账号和 8 周开源路线。
2. `docs/spec/01-requirements-and-domain.md`：角色、边界、状态机和业务规则。
3. `docs/spec/02-architecture-data-api.md`：模块、数据、接口和 FHIR 对齐。
4. `docs/spec/03-security-privacy-compliance.md`：安全、隐私、聚合和合规边界。
5. `docs/spec/04-official-data-and-rea.md`：官方数据来源及 REA 使用边界。
6. `docs/plans/05-implementation-and-acceptance.md`：当前基线和 8 周任务。

本交接文档优先级高于口头历史。若代码与计划冲突，以“安全边界 + 可运行事实 + 本文明确决策”为准；不要凭猜测扩功能。

## 2. 当前目标

项目当前不再以竞赛或 PDF/Word 汇报为主线，目标是在 **8 周内**形成可公开协作的 GitHub 开源 MVP：

- 后端使用 Python 模块化单体。
- Web、Android、微信小程序共享同一套 API 契约。
- 使用合成病例和官方公开数据快照。
- 使用小型数据库完成功能验证，重点是 SQLite 功能测试和一次 PostgreSQL 冒烟验证。
- 预留官方数据源、外部数据库、身份、通知和对象存储适配接口。
- 不追求完整 EHR、完整 FHIR 服务器、AI 诊断、电子处方、医保结算或真实行政处置。

竞赛与答辩材料只保留归档，后续需要时再单独扩展，不进入当前 GitHub 主线。

## 3. 当前仓库状态

当前仓库已有 3 个提交：

```text
ed8d396 feat: build multi-role CarePath web workspace
8a8f324 feat: add CarePath API and demo workflows
c0b6150 feat: establish backend policy and aggregation rules
```

交接时仍有未提交的基线改动，包括：

- Python 业务 API、SQLAlchemy 模型、Alembic 初始迁移和演示数据。
- Android 原生工程与 debug APK 构建配置。
- 微信小程序源码。
- Docker Compose、Nginx、MinIO、Redis 配置。
- Markdown 规格、实施计划和安全文档。
- 原始 Word 文件已从工作树移出，Git 会显示删除；文件本体已归档，不丢失。

**第一步不要重置工作树，也不要执行 `git checkout --`、`git reset --hard` 或删除未跟踪目录。** 先运行 `git status`、阅读本文和 `README.md`，确认现有改动后再提交基线。

提交前建议：

```powershell
git status
git diff --stat
git add README.md HANDOFF_TO_DSH.md backend apps docs ops .gitignore .env.example
git commit -m "chore: prepare open-source project handoff"
```

只提交确实需要的 Markdown 和源码；不要提交 `.env`、数据库文件、APK、构建产物、PDF、DOCX 或真实数据。

## 4. 已实现内容

### 4.1 Python 后端

位置：`backend/`

- Python 3.13、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic。
- scrypt 密码哈希、访问/刷新令牌、Web Cookie、Bearer Token 和 CSRF 校验。
- 组织范围、角色和家属授权 ABAC 检查。
- 患者、家属、医生、医院、政府、药企和系统管理员接口。
- 治疗模板、计划、任务、用药、观察、提醒、Outbox 和审计模型。
- 政府最小人数抑制和药企需求双阈值逻辑。
- 官方数据快照的通用导入接口。
- 初始 Alembic 迁移和合成演示数据。

关键入口：

```text
backend/src/carepath/main.py
backend/src/carepath/policies.py
backend/src/carepath/services.py
backend/src/carepath/models.py
backend/src/carepath/seed.py
backend/migrations/versions/
```

### 4.2 Web

位置：`apps/web/`

- Vue 3 + TypeScript + Vite + Pinia + Element Plus + ECharts。
- 六角色演示登录入口。
- 患者任务完成、医生创建计划、医院成员/指标、政府聚合/审核、药企产能、官方数据导入。
- 按角色异步加载面板，生产构建已成功。

### 4.3 Android

位置：`apps/android/`

- Kotlin、Compose、Hilt、Retrofit、Room、WorkManager、EncryptedSharedPreferences。
- 患者/家属登录、计划进度、任务完成、用药、提醒和离线缓存。
- `FLAG_SECURE` 阻止敏感页面被系统截屏。
- 纯展示逻辑拆在 `logic/` 独立 Kotlin JVM 模块，便于不启动 Android 运行时做单元测试。
- 当前已生成 debug APK。

### 4.4 微信小程序

位置：`apps/wechat/`

- 原生 WXML/WXSS/JavaScript。
- 沙箱账号登录、患者仪表盘、任务完成和本地缓存。
- 无真实微信 AppID，当前使用 `touristappid`，必须明确显示开发边界。
- 订阅消息、真实微信登录和推送尚未接入。

### 4.5 基础设施和文档

- `ops/docker-compose.yml`：PostgreSQL、Redis、MinIO、后端和 Web。
- `apps/web/nginx.conf`：SPA 与 API 反向代理。
- `docs/spec/`：需求、架构、安全、官方数据。
- `docs/plans/`：8 周实施与验收计划。
- `docs/research/competitive-matrix.md`：同类项目研究。

## 5. 已验证与未验证

### 已验证

后端：

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\ruff check src tests migrations
```

当前后台测试基线为 11 个 pytest 用例，覆盖认证、权限、任务闭环、聚合和官方快照接口。Alembic 已执行 `upgrade head`。

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

APK 输出：

```text
apps/android/app/build/outputs/apk/debug/app-debug.apk
```

微信：

```powershell
cd apps/wechat
npm test
npm run check
```

### 已知环境限制

1. 本机没有安装 Docker，因此 Compose、PostgreSQL 和 MinIO 尚未实际启动验证。
2. 当前开发库为 SQLite；PostgreSQL URL 已配置，但没有真实 PostgreSQL 功能测试。
3. 微信开发者工具的命令行服务端口未开启，无法自动预览或上传；小程序仍需人工在开发者工具中打开。
4. 当前 Windows 中文路径和 AGP 9.4/Gradle 9.6 组合下，Gradle 的 JUnit 进程出现过“测试类已编译但测试进程找不到”的环境问题；纯 Kotlin 逻辑曾通过直接 JUnit 运行验证，但必须在 Linux CI 或稳定 JDK/Gradle 组合中重新跑通正式测试任务。
5. `android.overridePathCheck=true` 是因为项目路径包含中文；后续应尽量在 CI 和部署环境使用 ASCII 路径。
6. 原始 Word 文件曾进入首个 Git 提交。当前工作树已移出，但如果公开仓库必须完全不含二进制历史，需由项目所有者批准后重写 Git 历史。不要擅自 force-push。

## 6. 当前存档

Word、PDF、图表、页面渲染 QA 和原始构想已移到仓库外：

```text
D:\项目设计\医院治疗方案进度协同体02-archive\competition-materials
```

包含：

```text
documents\医院治疗方案进度协同体_原始构想.docx
documents\医程共护_MVP总体设计与实施计划.docx
documents\医程共护_MVP总体设计与实施计划.pdf
report-generator\assets\
qa-renders\report-pages\
```

不要再把这些文件复制回开源仓库。后续竞赛或答辩需要时，单独从归档目录取用。

## 7. 8 周工作要求

### 第 1 周：仓库整理

- 完成 GitHub README、贡献指南、安全政策、变更日志和文档索引。
- 明确开源许可证；许可证未确认前不得宣称仓库已经是法律意义上的开源项目。
- 增加 CI，运行后端 pytest/Ruff、Web test/lint/build、微信 test/check 和 Android assemble。
- 检查 Git 历史、密钥、数据库文件和构建产物。

### 第 2 周：小型数据库验证

- 使用 SQLite 跑功能测试，不引入真实患者数据。
- 增加 PostgreSQL 冒烟测试：空库迁移、演示数据导入、登录、患者任务和聚合接口。
- 不引入大型生产 ETL，不做大规模压力测试。
- 测试数据库应在测试结束后清理。

### 第 3 周：官方数据接口

- 定义 `OfficialCatalogSource` 和 `OfficialDatasetRepository` 稳定契约。
- 为 NMPA、NHSA、NHC、NBS 分别建立小型测试夹具和导入器。
- 校验来源、版本、发布日期、生效期、校验值、审核人和状态。
- 不绕过 WAF、验证码、登录或访问控制；没有公开稳定接口时使用人工快照。

### 第 4 周：数据库和外部依赖解耦

- 为核心聚合根补齐 Repository/UnitOfWork 边界。
- 保持 SQLAlchemy 为当前实现，不假装支持所有数据库方言。
- 预留医院 HIS、医保、政务和供应链接口，但不在没有合作授权时伪造联调结果。
- 记录外部接口的错误、超时、重试、幂等和审计策略。

### 第 5 周：Web 主流程

- 用小型测试库完成六角色关键链路。
- 增加 Playwright 或等价 E2E；没有浏览器环境时至少保留可执行的 CI 用例。
- 检查授权撤销、跨机构、政府聚合抑制和药企最小发布阈值。

### 第 6 周：移动端验证

- Android 保证 assembleDebug 和纯逻辑测试在 CI 可重复运行。
- 微信在开发者工具中完成登录、首页、任务完成和后端不可用缓存流程。
- 没有 AppID 时不得把沙箱流程写成真实微信上线。

### 第 7 周：安全和错误处理

- 覆盖越权、跨机构、授权撤销、重复导入、断网后幂等补传和异常提示。
- 确保日志不包含临床正文、令牌、密码、真实身份证号或完整手机号。
- 运行依赖漏洞、秘密扫描和基础静态扫描。

### 第 8 周：v0.1.0 发布准备

- 固定版本号，更新 CHANGELOG。
- 写清安装、配置、演示账号、限制、数据来源和许可证。
- 保证新开发者能在干净环境完成启动和测试。
- 不以“演示成功”替代医院生产合规结论。

## 8. GitHub 完整项目文档

当前最少应保留以下 Markdown 或 GitHub 标准文件：

```text
README.md
LICENSE                    # 由项目所有者确认许可证后添加
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
CODE_OF_CONDUCT.md         # GitHub 社区推荐，可按实际需要添加
docs/README.md
docs/spec/01-requirements-and-domain.md
docs/spec/02-architecture-data-api.md
docs/spec/03-security-privacy-compliance.md
docs/spec/04-official-data-and-rea.md
docs/plans/05-implementation-and-acceptance.md
docs/research/competitive-matrix.md
.github/ISSUE_TEMPLATE/
.github/PULL_REQUEST_TEMPLATE.md
```

许可证建议只作为决策参考：

- Apache-2.0：包含明确专利授权，适合希望降低专利风险的协作项目。
- MIT：文本短、使用门槛低，但专利授权表达不如 Apache-2.0 完整。
- GPL/AGPL：不适合当前“便于后续合作和演示”的默认路径，且与已参考项目代码混用会增加义务。

没有项目所有者确认，不要单方面选择许可证。

## 9. 代码风格

### 总原则

- 保持模块化单体，不拆微服务。
- 高内聚、低耦合；领域模块不直接依赖 Web 框架或数据库会话。
- 只实现当前需求，不为想象中的未来功能预建空抽象。
- 优先复用已有模式；新增依赖必须有明确收益。
- 安全、授权、事务和错误处理不能为了少代码而省略。

### Python

- 使用 Python 3.13。
- FastAPI 路由只做 HTTP 适配，业务规则放到应用服务或策略模块。
- Pydantic 模型使用显式字段和约束；API JSON 使用 camelCase，内部数据库使用 snake_case。
- SQLAlchemy 2 typed mapping；数据库变化必须补 Alembic 迁移。
- 标识使用 UUID 字符串，时间为 UTC ISO 8601，避免本地时间写入。
- 权限判断使用 fail-closed；未知角色、未知范围和过期授权默认拒绝。
- 日志不输出令牌、密码、证件号、完整手机号或诊疗正文。
- 注释只解释“为什么不能从代码直接看出”，不要复述代码。

### 前端

- Vue 使用 Composition API 和 TypeScript。
- 角色权限先由后端决定，前端只做展示和交互裁剪，不把隐藏按钮当作安全控制。
- 重要操作显示明确错误，不吞掉异常。
- API 调用复用 `src/lib/api.ts`；新增接口先更新契约。
- 页面组件按角色职责拆分，避免把六角色塞进单一巨型组件。

### Android 和微信

- Android 使用 Compose、Hilt 和显式 ViewModel 状态。
- 离线缓存必须有“最后同步/当前为缓存”的提示。
- 令牌保存在安全存储，不写入普通日志。
- 微信端区分开发沙箱与真实 AppID 流程，不伪造订阅消息能力。

### 测试

- 新规则、权限、聚合阈值和错误恢复先写失败测试。
- 小型数据库只验证功能和迁移，不引入生产规模数据。
- 后端权限和聚合规则优先覆盖；前端测试关注角色导航和错误处理；移动端纯逻辑放可独立测试模块。
- 每个完成声明必须附上实际命令和输出结果。

## 10. 文档写作风格

- 使用中文主文档，代码标识和接口名保留英文。
- 先写结论，再写依据、边界和风险。
- 事实、假设、建议、未验证内容必须分开。
- 不写空泛口号，不夸大“实时”“智能”“合规”或“已接入”。
- 表格只用于角色矩阵、接口映射、测试场景、风险和路线等适合横向比较的内容。
- 不把尚未获得授权的政府、医保、医院或药企接口写成已实现。
- 涉及医疗、隐私、监管和药品供应时，必须保留风险说明。
- 文档改动要同步 README、规格、测试和当前状态，避免“文档说完成、代码没有”。

## 11. 任务处理习惯

1. 先检查仓库、`git status`、相关代码和现有测试，再决定改动。
2. 能从仓库找到答案的问题不反问用户；只有产品取舍或权限边界不清时才提出具体问题。
3. 改动前列出影响范围：调用方、测试、迁移、配置、前端类型、Android/微信端和文档。
4. 修 bug 先复现并补失败测试；规则变更先写行为测试。
5. 小步提交，使用 Conventional Commits；不要混入无关重构。
6. 完成任务后运行实际验证命令，报告通过和失败项；失败不能藏在“应该可以”中。
7. 不删除用户已有文件、不覆盖未提交改动、不执行 `git reset --hard`、不擅自 force-push。
8. 默认所有新项目数据放在 D 盘；本机中文路径问题要记录并尽量在 CI 使用 ASCII 路径。
9. 当前不扩大范围：不新增微服务、不接 AI 诊断、不生成 Word/PDF、不增加竞赛演示页面。
10. 交接时更新本文件或 `docs/plans/05-implementation-and-acceptance.md`，让下一位开发者能恢复上下文。

## 12. 当前验收清单

- [x] 后端五类业务角色权限和家属授权。
- [x] 患者/家属任务闭环。
- [x] 政府聚合抑制和药企发布阈值。
- [x] 官方数据快照通用导入接口。
- [x] Web 六角色演示工作台。
- [x] Android 源码和 debug APK。
- [x] 微信小程序源码和纯逻辑测试。
- [x] Alembic 初始迁移。
- [x] Docker Compose 配置。
- [ ] Docker Compose 实际启动。
- [ ] PostgreSQL 功能冒烟。
- [ ] 微信开发者工具自动预览。
- [ ] 正式开源许可证确认。
- [ ] Git 历史中的原始 Word 文件处理决策。
- [ ] Linux CI 跑通所有测试任务。

## 13. 给 dsh 的第一轮任务

第一轮只做以下事情，不要先扩业务：

1. 读取 README、本文和 `docs/plans/05-implementation-and-acceptance.md`。
2. 保留当前未提交改动，检查 `git diff`，建立一个基线提交。
3. 修复 CI 和本地命令不一致的问题，重点验证 SQLite、PostgreSQL 冒烟、Android assemble 和微信脚本检查。
4. 补齐 `LICENSE` 决策、`CONTRIBUTING.md`、`SECURITY.md` 和 CI。
5. 定义官方数据适配器和数据库仓储接口，不伪造真实外部接口。
6. 跑完一轮小数据库功能测试后，再决定是否开始 Web E2E。

如果必须在本机继续开发，优先使用 SQLite 和小型测试数据；PostgreSQL 只做启动和一条业务链冒烟，不在本机导入大量真实数据。
