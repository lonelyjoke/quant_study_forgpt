"""Configurable 0-100 risk scoring rules."""

from __future__ import annotations

import numpy as np
import pandas as pd


RISK_LEVELS = [
    (30, "\u673a\u4f1a\u533a"),
    (50, "\u504f\u673a\u4f1a"),
    (70, "\u4e2d\u6027\u504f\u98ce\u9669"),
    (100, "\u9ad8\u98ce\u9669\u533a"),
]


def calculate_risk_score(factor_df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """Calculate component risks and the weighted total risk score.

    The component scores are intentionally transparent rule-based heuristics.
    Each component is clipped to 0-100, where higher means higher risk.
    """

    required = [
        "close_to_ma20",
        "close_to_ma60",
        "close_to_ma120",
        "ma20_to_ma60",
        "ma60_to_ma120",
        "ret_20d",
        "ret_60d",
        "ret_120d",
        "volatility_20d",
        "volatility_60d",
        "max_drawdown",
        "drawdown_from_120d_high",
        "amount_amplification",
    ]
    _require_columns(factor_df, required)
    _validate_weights(weights)

    df = factor_df.copy()
    df["trend_risk"] = _trend_risk(df)
    df["momentum_risk"] = _momentum_risk(df)
    df["volatility_risk"] = _volatility_risk(df)
    df["drawdown_risk"] = _drawdown_risk(df)
    df["liquidity_risk"] = _liquidity_risk(df)

    df["risk_score"] = (
        weights["trend"] * df["trend_risk"]
        + weights["momentum"] * df["momentum_risk"]
        + weights["volatility"] * df["volatility_risk"]
        + weights["drawdown"] * df["drawdown_risk"]
        + weights["liquidity"] * df["liquidity_risk"]
    ).clip(0, 100)
    df["risk_level"] = df["risk_score"].apply(classify_risk_level)
    return df


def classify_risk_level(score: float) -> str:
    """Map a numeric risk score to a Chinese risk level label."""

    if pd.isna(score):
        return "\u6570\u636e\u4e0d\u8db3"
    for upper, label in RISK_LEVELS:
        if score <= upper:
            return label
    return "\u9ad8\u98ce\u9669\u533a"


def _trend_risk(df: pd.DataFrame) -> pd.Series:
    bullish_votes = (
        (df["close_to_ma20"] > 0).astype(int)
        + (df["close_to_ma60"] > 0).astype(int)
        + (df["close_to_ma120"] > 0).astype(int)
        + (df["ma20_to_ma60"] > 0).astype(int)
        + (df["ma60_to_ma120"] > 0).astype(int)
    )
    return ((5 - bullish_votes) / 5 * 100).astype(float)


def _momentum_risk(df: pd.DataFrame) -> pd.Series:
    momentum = 0.5 * df["ret_20d"] + 0.3 * df["ret_60d"] + 0.2 * df["ret_120d"]
    return _linear_inverse_score(momentum, low=-0.20, high=0.20)


def _volatility_risk(df: pd.DataFrame) -> pd.Series:
    vol = 0.6 * df["volatility_20d"] + 0.4 * df["volatility_60d"]
    return _linear_score(vol, low=0.10, high=0.45)


def _drawdown_risk(df: pd.DataFrame) -> pd.Series:
    drawdown = np.minimum(df["max_drawdown"], df["drawdown_from_120d_high"])
    return _linear_score(drawdown.abs(), low=0.03, high=0.25)


def _liquidity_risk(df: pd.DataFrame) -> pd.Series:
    # Very low turnover is a risk. Strong amount expansion is capped as low risk
    # rather than treated as speculative overheating in this MVP.
    return _linear_inverse_score(df["amount_amplification"], low=0.6, high=1.2)


def _linear_score(series: pd.Series, low: float, high: float) -> pd.Series:
    score = (series - low) / (high - low) * 100
    return score.clip(0, 100)


def _linear_inverse_score(series: pd.Series, low: float, high: float) -> pd.Series:
    score = (high - series) / (high - low) * 100
    return score.clip(0, 100)


def _validate_weights(weights: dict) -> None:
    expected = {"trend", "momentum", "volatility", "drawdown", "liquidity"}
    missing = expected - set(weights)
    if missing:
        raise ValueError(f"Missing risk score weights: {sorted(missing)}")
    total = sum(float(weights[key]) for key in expected)
    if not np.isclose(total, 1.0):
        raise ValueError(f"Risk score weights must sum to 1.0, got {total:.4f}")


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required factor columns: {missing}")
