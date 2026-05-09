"""Simple daily backtester for index timing signals."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd

from backtest.performance import summarize_performance


def run_backtest(
    signal_df: pd.DataFrame,
    transaction_cost: float = 0.0002,
    annual_trading_days: int = 252,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest dynamic index exposure versus buy-and-hold benchmark."""

    required = ["trade_date", "close", "position"]
    missing = [col for col in required if col not in signal_df.columns]
    if missing:
        raise ValueError(f"Missing required backtest columns: {missing}")

    df = signal_df.sort_values("trade_date").reset_index(drop=True).copy()
    df["index_return"] = df["close"].pct_change().fillna(0.0)
    df["turnover"] = df["position"].diff().abs().fillna(df["position"].abs())
    df["strategy_return"] = df["position"] * df["index_return"] - df["turnover"] * transaction_cost
    df["benchmark_return"] = df["index_return"]
    df["strategy_equity"] = (1 + df["strategy_return"]).cumprod()
    df["benchmark_equity"] = (1 + df["benchmark_return"]).cumprod()

    summary = pd.DataFrame(
        [
            {"portfolio": "strategy", **summarize_performance(df["strategy_return"], df["strategy_equity"], annual_trading_days)},
            {"portfolio": "benchmark", **summarize_performance(df["benchmark_return"], df["benchmark_equity"], annual_trading_days)},
        ]
    )
    return df, summary


def save_backtest_outputs(
    ts_code: str,
    backtest_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    output_dir: str | Path = "reports",
    figure_dir: str | Path = "reports/figures",
) -> tuple[Path, Path, Path]:
    """Save equity data, summary CSV, and an equity comparison chart."""

    output_path = Path(output_dir)
    figure_path = Path(figure_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    figure_path.mkdir(parents=True, exist_ok=True)

    safe_code = ts_code.replace(".", "_")
    curve_csv = output_path / f"{safe_code}_backtest_curve.csv"
    summary_csv = output_path / f"{safe_code}_backtest_summary.csv"
    figure_file = figure_path / f"{safe_code}_equity_curve.png"

    export_curve = backtest_df.copy()
    export_curve["trade_date"] = export_curve["trade_date"].dt.strftime("%Y-%m-%d")
    export_curve.to_csv(curve_csv, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    plot_equity_curve(backtest_df, ts_code, figure_file)
    return curve_csv, summary_csv, figure_file


def plot_equity_curve(backtest_df: pd.DataFrame, title: str, output_path: str | Path) -> None:
    """Plot strategy and benchmark equity curves."""

    plt.figure(figsize=(11, 6))
    plt.plot(backtest_df["trade_date"], backtest_df["strategy_equity"], label="Strategy", linewidth=1.6)
    plt.plot(backtest_df["trade_date"], backtest_df["benchmark_equity"], label="Benchmark", linewidth=1.2)
    plt.title(f"{title} Risk Timing Backtest")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
