# 三端与角色演示指南

以下命令默认在仓库根目录执行（Windows PowerShell）。所有数据均为合成数据。

## 0. 前置条件

| 软件 | 版本 | 用途 |
|---|---|---|
| Python | 3.13 | 后端 |
| Node.js | 24 + corepack | Web |
| JDK | 17 | Android（可选） |
| Android SDK | compileSdk 37 | Android（可选） |
| 微信开发者工具 | 最新稳定版 | 小程序（可选） |

## 1. Web 端（六类业务角色 + 管理员）

一条命令启动：

```powershell
.\scripts\dev-up.cmd
```

等价手动命令：

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m carepath.seed
.\.venv\Scripts\uvicorn carepath.main:app --reload --port 8000
```

```powershell
cd apps/web
corepack enable
pnpm install
pnpm dev
```

打开 <http://localhost:5173>，选择角色后账号密码自动填入。

### 各角色操作

| 角色 | 账号 / 密码 | 操作 |
|---|---|---|
| 患者 | `patient` / `Pa2026!care` | 登录 → 查看计划与任务 → 「标记为已完成」→ 查看用药、提醒、授权照护者 |
| 家属 | `caregiver` / `Ca2026!care` | 登录 → 进入患者进度 → 完成授权范围内的任务 |
| 医生 | `doctor` / `Do2026!care` | 登录 → 医生工作台 → 查看患者队列、提醒与已发布模板 |
| 医院管理员 | `hospital` / `Ho2026!care` | 登录 → 医院协同中心 → 成员、任务完成率、近期提醒 |
| 政府监管 | `regulator` / `Re2026!care` | 登录 → 区域监管沙箱 → 聚合指标、最小发布单元、审核决定 |
| 社区与志愿组织 | `community` / `Co2026!care` | 登录 → 社区照护与志愿调度 → 志愿者、社区任务、药品配送 |
| 药企 | `pharma` / `Ph2026!care` | 登录 → 药品供应与产能 → 区域信号、提交产能反馈 |
| 系统管理员 | `admin` / `Ad2026!care` | 访问 <http://127.0.0.1:8000/docs> 管理官方数据快照；Web 登录页未列出该角色 |

### 医院工作流（Web）

医院管理员登录后，在「医院协同中心」下方可：
1. 查看/录入本院职工（医生、管理人员）；
2. 查看分级转入记录并登记医院—社区转入；
3. 为患者写入治疗记录，其他医生可按患者调取；
4. 在患者计划内与病患/家属留言沟通。

### 社区工作流（Web）

社区协调员登录后可查看志愿者、社区任务与配送单，并创建新的随访/配送任务。

## 2. Android 端（患者 / 家属）

```powershell
.\scripts\build-android.ps1
```

构建产物：`apps\android\app\build\outputs\apk\debug\TreatmentPlanCoordinationPlatform-v0.1.0-debug.apk`（CI 作为 artifact 上传）。

安装到已连接的模拟器/真机：

```powershell
adb install -r apps\android\app\build\outputs\apk\debug\TreatmentPlanCoordinationPlatform-v0.1.0-debug.apk
```

- 模拟器访问宿主机后端使用 `http://10.0.2.2:8000/api/v1/`（已作为默认 BuildConfig）。
- 真机需将 `carepathApiBaseUrl` 改为电脑局域网地址后重新构建。
- 登录患者或家属账号，查看任务、完成打卡、查看用药与提醒。
- 断网演示：停止后端后下拉刷新，界面显示本地缓存与「最后同步」提示；恢复后端后任务只提交一次。

## 3. 微信小程序（患者 / 家属沙箱）

1. 打开微信开发者工具 → 导入项目 → 选择 `apps\wechat`。
2. AppID 选择「测试号」或使用 `touristappid`（沙箱）。
3. 详情 → 本地设置 → 勾选「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」。
4. 编译后使用 `patient / Pa2026!care` 或 `caregiver / Ca2026!care` 登录。
5. 首页查看任务并完成；停止后端后重新进入，验证缓存提示。

无 AppID 时无法使用真实微信登录、订阅消息或上线，这是当前演示边界。

## 4. Docker Compose（可选）

安装 Docker Desktop 后：

```powershell
Copy-Item .env.example .env
docker compose -f ops/docker-compose.yml up --build
```

Web：<http://localhost:8080>；API 文档：<http://localhost:8000/docs>；MinIO 控制台：<http://localhost:9001>。该方式已在 Docker Desktop（WSL2）与 CI 验证。

## 5. 停止与清理

- 一键脚本会打开两个 PowerShell 窗口，关闭窗口即停止服务。
- 重置演示数据：删除 `backend/carepath.db` 后重新执行 `python -m carepath.seed`。
- 测试数据库与临时文件已在脚本/测试结束后清理。

## 6. 常见问题

见 [troubleshooting.md](troubleshooting.md)。提交问题时请附操作系统、命令与完整错误，不要粘贴令牌或真实个人信息。