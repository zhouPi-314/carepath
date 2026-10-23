# 实施方案与验收

## 1. 范围

本平台面向治疗方案进度的多方协同，覆盖医院、社区与志愿组织、药企、政府与用户（病患/家属）。实现以合成病例与官方公开数据快照为输入，不接入真实患者数据，不提供诊断、处方、医保结算或行政处置。

## 2. 角色与权限

| 角色 | 默认范围 | 关键约束 |
|---|---|---|
| 患者 | 本人计划、任务、用药、观察、提醒 | 不得修改医生计划 |
| 家属 | 授权字段与有效期内的任务与用药 | 授权撤销或过期后立即拒绝 |
| 医生 | 本人负责且属于当前医院的计划 | 禁止跨院访问 |
| 医院管理员 | 本院成员、计划、提醒与指标 | 禁止查看其他医院 |
| 政府监管 | 脱敏区域指标与平台内审核 | 不得访问患者级数据 |
| 药企 | 自有目录、聚合需求与产能反馈 | 不得获取患者或医院明细 |
| 系统管理员 | 官方数据快照、外部端口能力 | 不浏览临床正文 |

## 3. 交付内容

- 后端：FastAPI 模块化单体、SQLAlchemy 2、Alembic 迁移、合成演示数据。
- 业务：治疗模板、计划版本、任务、用药、观察、提醒、审计与 Outbox。
- 安全：scrypt 密码、访问/刷新令牌、Cookie/Bearer、CSRF、家属 ABAC、组织隔离。
- 聚合：政府最小人数抑制；药企 3 家机构 / 50 患者月双阈值。
- 数据：官方快照导入（NMPA / NHSA / NHC / NBS），校验值去重与状态规则。
- 边界：仓储 / UnitOfWork；HIS、医保、政务、供应链预留端口。
- 客户端：Vue 3 协同工作台、Android 患者/家属端、微信小程序沙箱。
- 质量：单元/接口/E2E/移动端测试、PostgreSQL 冒烟、安全扫描。

## 4. 验收场景

1. 医生从已发布模板创建计划；患者确认后可见任务；家属在授权范围内完成自护任务。
2. 家属授权撤销后，后续读取与任务提交被拒绝。
3. 医院 A 的医生与管理员无法读取医院 B 的患者计划。
4. 政府区域活跃计划少于 10 时，计数、百分比与提醒数整体抑制，响应不含患者标识。
5. 药企仅能看到覆盖至少 3 家机构、50 个患者月的区域月度信号。
6. 官方快照重复校验值返回 409；不匹配记录标记 `UNVERIFIED`；过期快照标记 `STALE`。
7. Android 断网时显示缓存，恢复网络后任务只提交一次。
8. 微信沙箱在无 AppID 时仍可登录、查看任务与使用缓存，并明确展示边界。

## 5. 验证命令

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check src tests migrations scripts

cd apps/web
pnpm test; pnpm lint; pnpm build

cd apps/wechat
npm test; npm run check

cd apps/android
.\gradlew.bat :logic:test
.\gradlew.bat :app:assembleDebug
```

PostgreSQL 冒烟：

```powershell
cd backend
$env:CAREPATH_SMOKE_DATABASE_URL='postgresql+asyncpg://user:pass@127.0.0.1:5432/carepath_smoke'
.\.venv\Scripts\python scripts\postgres_smoke.py
```

## 6. 完成定义

- 逻辑变更具有先失败后通过的测试。
- API 变更同步前端类型与文档。
- 数据库变更具有可执行迁移。
- 新增角色或字段同步权限矩阵、审计和数据分类。
- 不提交真实个人信息、明文密钥或生产默认密码。
- 文档“已完成”与真实命令输出一致。

## 7. 后续工作

见 [ROADMAP.md](../ROADMAP.md)。近期包括授权撤销操作面、Docker Compose 验证、微信 AppID 流程；外部系统落地需合作授权。
