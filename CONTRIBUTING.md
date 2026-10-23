# 贡献指南

感谢参与医疗健康协同体平台的建设。本项目欢迎问题反馈、讨论、代码与文档贡献。

## 快速开始

请先阅读 [README.md](README.md) 与 [docs/demo-guide.md](docs/demo-guide.md)，在本机启动后端与 Web 后再进行开发。

## 分支与提交

- 默认分支为 `main`；功能开发请从 `main` 创建特性分支。
- 提交信息使用 Conventional Commits：`feat:`、`fix:`、`chore:`、`docs:`、`test:`、`refactor:` 等。
- 每次改动附带对应测试；不混入无关重构，小步提交。

## 代码与文档规范

- 保持模块化单体，不拆微服务；不为想象中的功能预建空抽象。
- FastAPI 路由只做 HTTP 适配；业务规则放在应用服务或策略模块。
- 权限判断 fail-closed；新增角色和字段同步权限矩阵、审计和数据分类。
- 数据库变化必须补 Alembic 迁移。
- 使用合成数据和官方公开数据快照，不引入真实患者信息。
- 文档先写结论，再写依据、边界和风险；“已完成”必须与真实命令输出一致。
- 不新增 Word/PDF 生成、演示专用页面、微服务或诊断建议功能。

## 测试命令

```powershell
# 后端
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check src tests migrations scripts

# Web
cd apps/web
pnpm test
pnpm lint
pnpm build

# 微信
cd apps/wechat
npm test
npm run check

# Android（JDK 17+）
cd apps/android
.\gradlew.bat :logic:test
.\gradlew.bat :app:assembleDebug
```

## 提交前检查

1. 不提交 `.env`、`*.db`、APK、构建产物、PDF、DOCX 或真实数据。
2. 日志不输出令牌、密码、证件号、完整手机号或诊疗正文。
3. 文档中的“已完成”与测试输出一致。
4. 关联 issue（如适用）。

## 许可证

本项目采用 **Apache-2.0 或 MIT 双许可**（见 [LICENSE-APACHE](LICENSE-APACHE) 与 [LICENSE-MIT](LICENSE-MIT)）。提交贡献即表示你同意按该双许可授权你的贡献；请勿提交无权授权的第三方代码、素材或数据。
