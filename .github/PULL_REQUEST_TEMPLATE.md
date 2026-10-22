## 变更内容

<!-- 说明本次改动，遵循 Conventional Commits。 -->

## 影响范围

- [ ] 后端（模型 / 迁移 / 路由 / 策略）
- [ ] Web（面板 / 契约 / 类型）
- [ ] Android / 微信
- [ ] 文档
- [ ] CI / 运维

## 测试

- [ ] 后端：`pytest -q` 与 `ruff check src tests migrations` 通过
- [ ] Web：`pnpm test`、`pnpm lint`、`pnpm build` 通过
- [ ] 微信：`npm test` 与 `npm run check` 通过
- [ ] Android：`:logic:test`（如涉及）

## 检查

- [ ] 未提交 `.env`、数据库文件、APK、构建产物、PDF/DOCX 或真实数据
- [ ] 日志不包含令牌、密码、证件号、完整手机号或诊疗正文
- [ ] 文档中的“已完成”与真实命令输出一致
- [ ] 数据库变更附 Alembic 迁移

## 相关 issue

<!-- 修复 #123 / 关联 #456 -->
