"""End-to-end factor calculation pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from factors.macro_factors import add_macro_factors
from factors.technical_factors import calculate_technical_factors


def calculate_factor_table(price_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all currently enabled factors for one index."""

    factors = calculate_technical_factors(price_df)
    return add_macro_factors(factors)


def calculate_factors_for_indices(price_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Calculate factor tables for multiple indices."""

    return {ts_code: calculate_factor_table(df) for ts_code, df in price_data.items()}


def save_factor_table(factor_df: pd.DataFrame, output_path: str | Path) -> None:
    """Save a factor table to CSV with stable datetime formatting."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    output = factor_df.copy()
    output["trade_date"] = output["trade_date"].dt.strftime("%Y-%m-%d")
    output.to_csv(path, index=False, encoding="utf-8-sig")


def load_factor_table(path: str | Path) -> pd.DataFrame:
    """Load a saved factor CSV and parse dates."""

    df = pd.read_csv(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df
