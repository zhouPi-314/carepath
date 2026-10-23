# 官方数据与 REA 调研规范

## 1. 官方数据目标

官方数据只用于验证字段、版本、统计口径和演示可信度，不用于冒充真实监管实时数据。所有数据以人工合法获取的快照导入。

## 2. 首批来源

| 来源 | 用途 | 首版方式 |
|---|---|---|
| 国家药品监督管理局公开药品查询 | 药品批准文号、通用名、生产单位 | 人工导出或录入经过审核的演示子集 |
| 国家医疗保障局医保药品目录 | 展示信息性医保标签 | 导入当前年度公开目录快照 |
| 国家卫生健康委医疗机构公开信息 | 医院机构认证辅助 | 导入机构名称、地区等公开字段 |
| 国家统计局及卫生健康统计公开资料 | 区域人口和统计基线 | 导入年度聚合数据 |

官网可能存在 WAF、无稳定 API 或访问限制，首版不绕过限制、不进行高频抓取。

## 3. 快照契约

每个快照必须记录：

```text
sourceCode
title
version
sourceUrl
publishedAt
effectiveAt
importedAt
checksum
parserVersion
reviewer
status
content
```

校验规则：

- 相同 `checksum` 不得重复导入。
- `sourceUrl` 必须指向公开合法来源。
- 审核人不能为空。
- 药物或机构无法匹配时标记 `UNVERIFIED`，不可伪造为已验证。
- 超过约定有效期时标记 `STALE`。
- 医保标签必须注明“不代表实际报销”。

## 4. REA 使用边界

REA 只用于公开网页、开源项目和用户具有合法分析权限的本地应用包。允许：

- 观察公开页面结构、可访问性、信息架构和交互流程。
- 对公开 JavaScript 包进行静态依赖和 API 形状分析。
- 对有权分析的本地 APK 记录页面、权限门槛和公开数据模型。
- 记录来源 URL、时间、哈希、许可证和证据路径。

禁止：

- 绕过登录、验证码、访问控制、加密或技术保护措施。
- 复制专有源代码、数据库、素材、文案或品牌。
- 将逆向结果直接包装成来源应用的功能承诺。

## 5. 已参考开源项目

| 项目 | 许可证 | 借鉴内容 | 不采用 |
|---|---|---|---|
| OpenEMR | GPL-3.0 | 患者、预约、处方、审计、FHIR API 的领域完整性 | 不复制代码或界面 |
| OpenMRS | MPL-2.0 | 模块化和可配置医疗元数据 | 不继承其复杂平台 |
| Medplum | Apache-2.0 | FHIR、OIDC、前后端工程化 | 不引入完整托管 CDR |
| HAPI FHIR | Apache-2.0 | 标准资源、互操作和验证思路 | 不建设完整 Java FHIR 服务 |
| Android FHIR SDK | Apache-2.0 | 移动端离线优先 | 首版不直接接入完整 FHIR 存储 |
| OpenCare 类家庭照护项目 | AGPL-3.0 | 家属协同、用药提醒、任务分配 | 不复制代码和品牌 |

GitHub 星标、版本和许可证会变化，正式商用前必须重新核验。GPL/AGPL 项目只作为需求来源，避免在未完成许可证兼容审查时复制代码。

## 6. 公开产品调研维度

- 患者账号与家属绑定方式。
- 治疗计划和随访时间线。
- 用药提醒与任务完成反馈。
- 医生队列、异常提醒和院内权限。
- 政府对区域数据的脱敏和导出。
- 药企目录、供应反馈和最小聚合阈值。
- 离线、无障碍、错误恢复和隐私提示。

调研结果记录在 `docs/research/competitive-matrix.md`，不得从非授权目标提取私有业务代码。

## 7. 已实现适配契约

- `OfficialCatalogSource`（`backend/src/carepath/official_data/contracts.py`）：定义 `source_code`、`parser_version` 和 `parse(raw) -> ParsedDataset`。
- `OfficialDatasetRepository`：定义 `exists_by_checksum` 与 `add`；SQLAlchemy 适配器位于 `repository.py`，领域层不依赖 ORM。
- 四个来源解析器：`NmpaSource`、`NhsaSource`、`NhcSource`、`NbsSource`，只解析人工导出的 JSON 快照，不访问官网、不绕过 WAF/验证码/登录。
- 校验规则：来源代码、标题、版本、https 来源链接、审核人、解析器版本、SHA-256 校验值，以及发布日期不得晚于生效日期。
- 状态规则：记录缺字段或为空时 `UNVERIFIED`（优先）；生效日期超过 365 天为 `STALE`；否则 `VERIFIED`。
- 管理端接口：`GET /api/v1/admin/official-datasets/sources` 列出来源与解析器版本；`POST /api/v1/admin/official-datasets/sources/{sourceCode}/import` 导入快照。重复校验值 409，非法快照 422，未知来源 404。
- 测试夹具：`backend/tests/fixtures/official/*.json`；PostgreSQL 冒烟也会执行一次来源导入并验证重复导入 409。

