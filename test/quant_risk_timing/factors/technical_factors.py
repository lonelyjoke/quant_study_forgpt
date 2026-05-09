"""Technical and liquidity factor calculations for medium/long-term timing."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_technical_factors(price_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate trend, momentum, volatility, drawdown, and liquidity factors.

    The input must contain ``trade_date``, ``close``, ``high``, and ``amount``.
    Returned columns are aligned to the input rows and preserve the original
    market data for downstream scoring and backtesting.
    """

    _require_columns(price_df, ["trade_date", "close", "high", "amount"])
    df = price_df.sort_values("trade_date").reset_index(drop=True).copy()

    close = df["close"]
    returns = close.pct_change()

    for window in (20, 60, 120):
        ma = close.rolling(window=window, min_periods=window).mean()
        df[f"ma{window}"] = ma
        df[f"close_to_ma{window}"] = close / ma - 1
        df[f"ret_{window}d"] = close.pct_change(window)

    df["ma20_to_ma60"] = df["ma20"] / df["ma60"] - 1
    df["ma60_to_ma120"] = df["ma60"] / df["ma120"] - 1

    df["volatility_20d"] = returns.rolling(20, min_periods=20).std() * np.sqrt(252)
    df["volatility_60d"] = returns.rolling(60, min_periods=60).std() * np.sqrt(252)
    df["max_drawdown"] = _rolling_max_drawdown(close, window=120)
    df["drawdown_from_120d_high"] = close / close.rolling(120, min_periods=120).max() - 1

    df["amount_ma20"] = df["amount"].rolling(20, min_periods=20).mean()
    df["amount_ma60"] = df["amount"].rolling(60, min_periods=60).mean()
    df["amount_amplification"] = df["amount"] / df["amount_ma20"]

    return df


def _rolling_max_drawdown(close: pd.Series, window: int = 120) -> pd.Series:
    """Calculate rolling maximum drawdown as a negative percentage."""

    def calc(values: np.ndarray) -> float:
        cumulative_high = np.maximum.accumulate(values)
        drawdowns = values / cumulative_high - 1
        return float(drawdowns.min())

    return close.rolling(window=window, min_periods=window).apply(calc, raw=True)


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required input columns: {missing}")
