"""Position sizing rules based on risk score."""

from __future__ import annotations

import pandas as pd


def apply_position_rules(scored_df: pd.DataFrame, position_rules: list[dict], signal_lag_days: int = 1) -> pd.DataFrame:
    """Assign target and executable positions from configured score buckets."""

    if "risk_score" not in scored_df.columns:
        raise ValueError("Input data must contain risk_score.")

    rules = sorted(position_rules, key=lambda item: float(item["max_score"]))
    df = scored_df.sort_values("trade_date").reset_index(drop=True).copy()
    df["target_position"] = df["risk_score"].apply(lambda score: _score_to_position(score, rules))
    df["position"] = df["target_position"].shift(signal_lag_days).fillna(0.0)
    return df


def _score_to_position(score: float, rules: list[dict]) -> float:
    if pd.isna(score):
        return 0.0
    for rule in rules:
        if score <= float(rule["max_score"]):
            return float(rule["position"])
    return float(rules[-1]["position"])
