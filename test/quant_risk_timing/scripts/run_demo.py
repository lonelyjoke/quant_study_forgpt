"""Run the MVP pipeline on synthetic data without a Tushare token."""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import load_config, resolve_project_path
from factors.factor_pipeline import calculate_factor_table
from strategy.risk_score import calculate_risk_score
from strategy.timing_strategy import apply_position_rules
from backtest.backtester import run_backtest, save_backtest_outputs


def make_demo_data(rows: int = 320) -> pd.DataFrame:
    """Create deterministic synthetic index data for a smoke-test demo."""

    dates = pd.bdate_range("2020-01-01", periods=rows)
    trend = np.linspace(1000, 1280, rows)
    cycle = 35 * np.sin(np.linspace(0, 12, rows))
    close = trend + cycle
    return pd.DataFrame(
        {
            "ts_code": "DEMO.SH",
            "trade_date": dates,
            "open": close * 0.998,
            "high": close * 1.012,
            "low": close * 0.988,
            "close": close,
            "vol": np.linspace(100000, 135000, rows),
            "amount": np.linspace(1_000_000, 1_600_000, rows),
        }
    )


def main() -> None:
    """Run a local demo and save report outputs."""

    config = load_config()
    price_df = make_demo_data()
    factor_df = calculate_factor_table(price_df)
    scored_df = calculate_risk_score(factor_df, config["risk_score"]["weights"])
    signal_df = apply_position_rules(
        scored_df,
        config["strategy"]["position_rules"],
        signal_lag_days=int(config["strategy"].get("signal_lag_days", 1)),
    )
    backtest_df, summary_df = run_backtest(
        signal_df,
        transaction_cost=float(config["backtest"].get("transaction_cost", 0.0)),
        annual_trading_days=int(config["backtest"].get("annual_trading_days", 252)),
    )
    _, summary_csv, figure_file = save_backtest_outputs(
        "DEMO.SH",
        backtest_df,
        summary_df,
        output_dir=resolve_project_path(config["backtest"]["output_dir"]),
        figure_dir=resolve_project_path(config["backtest"]["figure_dir"]),
    )
    latest = signal_df.dropna(subset=["risk_score"]).iloc[-1]
    print(f"Demo latest signal: {latest['trade_date'].date()} score={latest['risk_score']:.2f}, level={latest['risk_level']}")
    print(summary_df.to_string(index=False))
    print(f"Saved demo summary: {summary_csv}")
    print(f"Saved demo figure: {figure_file}")


if __name__ == "__main__":
    main()
