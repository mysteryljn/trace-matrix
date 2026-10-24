# trace-matrix

把需求 CSV 和测试用例 CSV 做成可审查的双向追踪矩阵。工具检查缺失覆盖、孤立测试、重复 ID，并输出 JSON 摘要，适合 CI 阶段阻止需求变更后测试没有跟上的情况。

使用：python trace.py examples/requirements.csv examples/tests.csv。需求文件需要 id,description,test_ids；test_ids 用分号分隔。测试文件需要 test_id,name。

汽车软件项目的需求、实现和验证常由不同工具管理，变更影响分析很慢。一个纯文本接口可以先提供稳定基线，再接入 ALM、DOORS 或自研平台。

## 许可证

MIT
