# 中长线指数风险择时系统 MVP

这个项目用于衡量上证50和沪深300指数的中长线风险与机会。当前版本是一个可运行 MVP：从 Tushare 获取指数日线数据，计算技术类择时因子，生成 0-100 风险评分，按评分调整指数仓位，并输出回测结果和净值曲线。

## 指数范围

| 指数 | Tushare 代码 |
| --- | --- |
| 上证50 | `000016.SH` |
| 沪深300 | `000300.SH` |

## 安装依赖

```bash
cd quant_risk_timing
pip install -r requirements.txt
```

## 设置 Tushare Token

代码不会写死任何 API key。请把 token 放到环境变量 `TUSHARE_TOKEN`。

PowerShell:

```powershell
$env:TUSHARE_TOKEN="你的token"
```

Linux/macOS:

```bash
export TUSHARE_TOKEN="你的token"
```

## 运行流程

更新或读取数据缓存：

```bash
python scripts/run_data_update.py
```

计算因子：

```bash
python scripts/run_factor_calc.py
```

运行完整回测：

```bash
python scripts/run_backtest.py
```

不配置 Tushare token 时，也可以先跑合成数据 demo，验证本地环境和报表输出：

```bash
python scripts/run_demo.py
```

输出文件：

- 数据缓存：`data/cache/*_index_daily.csv`
- 因子文件：`data/cache/*_factors.csv`
- 回测明细：`reports/*_backtest_curve.csv`
- 结果汇总：`reports/*_backtest_summary.csv`
- 净值图表：`reports/figures/*_equity_curve.png`

## 当前因子

趋势因子：

- `close / MA20 - 1`
- `close / MA60 - 1`
- `close / MA120 - 1`
- `MA20 / MA60 - 1`
- `MA60 / MA120 - 1`

动量因子：

- 20日收益率
- 60日收益率
- 120日收益率

波动率与回撤因子：

- 20日年化波动率
- 60日年化波动率
- 120日滚动最大回撤
- 当前价格距离过去120日高点的回撤幅度

成交额/流动性因子：

- 成交额20日均值
- 成交额60日均值
- 成交额放大倍数

## 风险评分逻辑

风险分数为 0-100 分，分数越高表示风险越高。权重在 `config/config.yaml` 中配置：

- 趋势风险：30%
- 动量风险：20%
- 波动率风险：20%
- 回撤风险：20%
- 成交额/流动性风险：10%

风险等级：

- 0-30：机会区
- 30-50：偏机会
- 50-70：中性偏风险
- 70-100：高风险区

## 仓位规则

仓位规则同样在 `config/config.yaml` 中配置：

- 风险分数 <= 30：100%
- 30 < 风险分数 <= 50：70%
- 50 < 风险分数 <= 70：40%
- 风险分数 > 70：20%

回测中默认使用下一交易日仓位，降低直接用当日收盘信号带来的前视偏差。

## 估值因子扩展

`factors/valuation_factors.py` 预留了估值接口，当前尝试使用 Tushare 的 `index_dailybasic` 获取 `pe`、`pe_ttm`、`pb`。不同 Tushare 账号的接口权限可能不同，因此 MVP 默认不把估值纳入评分。后续可以：

1. 在 `valuation_factors.py` 中确认可用估值字段。
2. 在 `factor_pipeline.py` 中合并估值数据。
3. 在 `strategy/risk_score.py` 中增加估值风险组件。
4. 在 `config/config.yaml` 中加入估值权重。

## 运行测试

测试使用合成数据，不需要 Tushare token：

```bash
pytest tests
```

## 当前版本优势

- 模块化结构清晰，数据、因子、评分、策略、回测相互独立。
- 所有关键参数放在 `config/config.yaml`，便于后续调整。
- 本地 CSV 缓存降低重复调用 Tushare API 的次数。
- 评分规则透明，适合作为研究起点。

## 当前局限性

- 因子主要来自价格和成交额，尚未纳入宏观、估值、盈利或利率环境。
- 风险评分是启发式规则，不代表最优参数。
- 回测为简化日频回测，未处理真实交易滑点、申赎限制、节假日特殊情况等细节。
- 当前没有做参数寻优，也不建议在 MVP 阶段为了提高历史收益过拟合。

## 后续可扩展方向

- 增加指数估值分位数、股债性价比、信用利差、资金面等中长期因子。
- 引入多指数组合层面的风险预算和仓位约束。
- 增加更完整的报告模板，例如 Markdown/HTML 自动报告。
- 将缓存升级为 parquet 或数据库，并增加增量更新逻辑。
