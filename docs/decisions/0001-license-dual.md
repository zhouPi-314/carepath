# ADR-0001：开源许可证决策（双许可）

- 状态：**已确认（2026-10-22）**
- 决策人：项目所有者
- 结论：**Apache-2.0 或 MIT 双许可**，使用者可任选其一。

## 背景

项目所有者确认在 Apache-2.0 与 MIT 之间均可接受，并要求以双许可形式发布。

## 决策

仓库同时提供两份许可证文本：

- [`LICENSE-APACHE`](../LICENSE-APACHE)：Apache License 2.0，逐字采用官方文本，含明确专利授权。
- [`LICENSE-MIT`](../LICENSE-MIT)：MIT License，最简宽松许可。

使用者可以按任一许可证使用、修改和分发本项目；选择其中一个即可，无需同时满足两者。

## 理由

1. 需要专利授权或与 Apache-2.0 生态协作的使用者可选 Apache-2.0。
2. 只需要最简宽松许可的使用者可选 MIT。
3. 与常见开源项目（如 Rust 生态）的双许可实践一致，降低采用门槛。

## 影响

- README、CONTRIBUTING、CHANGELOG 同步声明双许可。
- 贡献默认按双许可授权（Apache-2.0 OR MIT）。
- 若项目所有者后续改为单一许可证，需保留已发布版本的历史许可，并在新版本中说明。

## 关联

- `LICENSE-APACHE`、`LICENSE-MIT`
- `README.md`“开源许可”
- `CONTRIBUTING.md`“许可证”
