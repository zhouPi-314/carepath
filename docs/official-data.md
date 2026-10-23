# 官方公开数据接入

本平台只处理**人工合法获取**的官方公开数据快照，不抓取、不绕过 WAF、验证码或登录。所有快照必须记录来源、版本、发布日期、生效日期、校验值、审核人与状态。

## 1. 首批来源

| 来源 | 内容 | 获取方式 |
|---|---|---|
| NMPA | 药品批准文号、通用名、生产单位 | 官网公开查询页人工导出 |
| NHSA | 医保药品目录与标签 | 年度公开目录人工整理 |
| NHC | 医疗机构公开信息 | 官网/公开统计材料人工整理 |
| NBS | 区域人口与统计基线 | 国家统计局公开数据人工导出 |

医保标签仅为信息展示，不代表实际报销。

## 2. 快照格式

```json
{
  "title": "快照标题",
  "version": "2026-10",
  "sourceUrl": "https://example.gov.cn/",
  "publishedAt": "2026-10-01",
  "effectiveAt": "2026-10-01",
  "records": [
    { "approvalNumber": "国药准字H20260001", "name": "示例药品", "manufacturer": "示例企业" }
  ]
}
```

不同来源的 `records` 字段由对应解析器定义：

- NMPA：`approvalNumber`、`name`、`manufacturer`
- NHSA：`drugName`、`insuranceLabel`
- NHC：`institutionName`、`regionCode`
- NBS：`regionCode`、`populationBaseline`

## 3. 导入

```powershell
cd backend
.\.venv\Scripts\python scripts\import_official_snapshot.py NMPA .\tests\fixtures\official\nmpa.json --reviewer "数据审核员"
```

或指定数据库：

```powershell
.\.venv\Scripts\python scripts\import_official_snapshot.py NBS .\nbs.json --reviewer "数据审核员" --database-url "sqlite+aiosqlite:///./carepath.db"
```

输出包含 `source`、`version`、`status`、`checksum` 与记录 ID。重复校验值返回 409 对应的 `FAIL`。

## 4. 校验与状态

- 相同 `checksum` 不得重复导入。
- 来源链接必须为 `https`。
- 审核人、标题、版本不能为空。
- 发布日期不得晚于生效日期。
- 记录缺字段或为空：`UNVERIFIED`。
- 生效日期超过 365 天：`STALE`。
- 其余为 `VERIFIED`。

## 5. 测试夹具

仓库内的四来源 JSON 夹具位于 `backend/tests/fixtures/official/`，仅用于测试与演示，不代表真实监管数据。
