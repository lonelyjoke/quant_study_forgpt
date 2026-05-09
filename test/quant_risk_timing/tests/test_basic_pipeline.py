"""Basic tests for the MVP pipeline using synthetic index data."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtest.backtester import run_backtest
from factors.factor_pipeline import calculate_factor_table
from strategy.risk_score import calculate_risk_score
from strategy.timing_strategy import apply_position_rules


def _synthetic_index_data(rows: int = 260) -> pd.DataFrame:
    dates = pd.bdate_range("2020-01-01", periods=rows)
    trend = np.linspace(1000, 1250, rows)
    cycle = 20 * np.sin(np.linspace(0, 10, rows))
    close = trend + cycle
    return pd.DataFrame(
        {
            "ts_code": "000300.SH",
            "trade_date": dates,
            "open": close * 0.998,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "vol": np.linspace(100000, 130000, rows),
            "amount": np.linspace(1_000_000, 1_500_000, rows),
        }
    )


def test_basic_pipeline_runs() -> None:
    price_df = _synthetic_index_data()
    factors = calculate_factor_table(price_df)
    scored = calculate_risk_score(
        factors,
        weights={"trend": 0.3, "momentum": 0.2, "volatility": 0.2, "drawdown": 0.2, "liquidity": 0.1},
    )
    signals = apply_position_rules(
        scored,
        position_rules=[
            {"max_score": 30, "position": 1.0},
            {"max_score": 50, "position": 0.7},
            {"max_score": 70, "position": 0.4},
            {"max_score": 100, "position": 0.2},
        ],
    )
    backtest_df, summary = run_backtest(signals)

    assert not backtest_df.empty
    assert {"strategy_equity", "benchmark_equity", "risk_score", "position"}.issubset(backtest_df.columns)
    assert len(summary) == 2
    assert scored["risk_score"].dropna().between(0, 100).all()
