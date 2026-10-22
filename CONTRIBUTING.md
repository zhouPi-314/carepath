# 贡献指南

感谢您对医程共护 CarePath 的关注。本项目处于开源 MVP 整理阶段，欢迎以问题、讨论、代码和文档方式参与。

## 快速开始

请先阅读 [README.md](README.md) 和 [HANDOFF_TO_DSH.md](HANDOFF_TO_DSH.md)，并按 README 在本机启动后端与 Web。

## 分支与提交

- 当前主线分支：`feature/ycth-mvp`（整理完成后将合并到默认分支）。
- 提交信息使用 Conventional Commits：`feat:`、`fix:`、`chore:`、`docs:`、`test:`、`refactor:` 等。
- 每次改动应附带对应测试：后端 `pytest`、Web `vitest`、微信 `npm test`、Android `logic` 模块 JUnit。
- 不混入无关重构；小步提交。

## 代码与文档规范

- 保持模块化单体，不拆微服务；不为想象中的功能预建空抽象。
- FastAPI 路由只做 HTTP 适配；业务规则放在应用服务或策略模块。
- 权限判断 fail-closed；新增角色和字段同步权限矩阵、审计和数据分类。
- 数据库变化必须补 Alembic 迁移。
- 使用合成数据和官方公开数据快照，不引入真实患者信息。
- 文档先写结论，再写依据、边界和风险；“已完成”必须与真实命令输出一致。
- 不新增 Word/PDF 生成、竞赛演示页面、微服务或 AI 诊断。

## 测试命令

```powershell
# 后端
cd backend
.\venv\Scripts\python -m pytest -q
.\venv\Scripts\python -m ruff check src tests migrations

# Web
cd apps/web
pnpm test
pnpm lint
pnpm build

# 微信
cd apps/wechat
npm test
npm run check

# Android（纯逻辑模块 JUnit，需 JDK 17+）
cd apps/android
./gradlew :logic:test
```

## 提交前检查

1. 不提交 `.env`、`*.db`、APK、构建产物、PDF、DOCX 或真实数据。
2. 日志不输出令牌、密码、证件号、完整手机号或诊疗正文。
3. 文档中的“已完成”与测试输出一致。
4. 关联 issue（如适用）。

## 行为准则

参与本项目即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
