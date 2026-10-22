# Docker Compose 本地部署

在仓库根目录执行：

```powershell
Copy-Item .env.example .env
docker compose -f ops/docker-compose.yml up --build
```

访问：

- Web：http://localhost:8080
- API 文档：http://localhost:8000/docs
- MinIO 控制台：http://localhost:9001

演示账号密码均为 `CarePath123!`。Compose 只用于课程与竞赛演示，默认配置使用明确标注的开发密钥，不可直接用于生产。
