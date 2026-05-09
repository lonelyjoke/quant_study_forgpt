"""Run factor scoring, timing strategy, and backtest for configured indices."""

from __future__ import annotations

from common import load_config, resolve_project_path
from data.data_loader import TushareIndexDataLoader
from factors.factor_pipeline import calculate_factor_table
from strategy.risk_score import calculate_risk_score
from strategy.timing_strategy import apply_position_rules
from backtest.backtester import run_backtest, save_backtest_outputs


def main() -> None:
    """Run the complete MVP pipeline and save reports."""

    config = load_config()
    data_cfg = config["data"]
    score_cfg = config["risk_score"]
    strategy_cfg = config["strategy"]
    backtest_cfg = config["backtest"]

    loader = TushareIndexDataLoader(cache_dir=resolve_project_path(data_cfg["cache_dir"]))
    for ts_code, name in config["indices"].items():
        price_df = loader.get_index_daily(
            ts_code,
            start_date=data_cfg["start_date"],
            end_date=data_cfg.get("end_date"),
            refresh=bool(data_cfg.get("refresh", False)),
        )
        factor_df = calculate_factor_table(price_df)
        scored_df = calculate_risk_score(factor_df, score_cfg["weights"])
        signal_df = apply_position_rules(
            scored_df,
            position_rules=strategy_cfg["position_rules"],
            signal_lag_days=int(strategy_cfg.get("signal_lag_days", 1)),
        )
        backtest_df, summary_df = run_backtest(
            signal_df,
            transaction_cost=float(backtest_cfg.get("transaction_cost", 0.0)),
            annual_trading_days=int(backtest_cfg.get("annual_trading_days", 252)),
        )
        curve_csv, summary_csv, figure_file = save_backtest_outputs(
            ts_code,
            backtest_df,
            summary_df,
            output_dir=resolve_project_path(backtest_cfg["output_dir"]),
            figure_dir=resolve_project_path(backtest_cfg["figure_dir"]),
        )
        latest = signal_df.dropna(subset=["risk_score"]).iloc[-1]
        print(f"\n{ts_code} {name}")
        print(f"Latest signal: {latest['trade_date'].date()} score={latest['risk_score']:.2f}, level={latest['risk_level']}, position={latest['target_position']:.0%}")
        print(summary_df.to_string(index=False))
        print(f"Saved: {curve_csv}, {summary_csv}, {figure_file}")


if __name__ == "__main__":
    main()
