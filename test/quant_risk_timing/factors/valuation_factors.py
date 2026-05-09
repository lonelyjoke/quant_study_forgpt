"""Valuation factor interfaces.

Tushare valuation coverage and permissions can differ by account. The MVP
keeps this module isolated so PE/PB data can be enabled without touching the
technical factor or backtest pipeline.
"""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd


VALUATION_COLUMNS = ["ts_code", "trade_date", "pe", "pe_ttm", "pb"]


def fetch_index_valuation(
    ts_code: str,
    start_date: str,
    end_date: Optional[str] = None,
    token_env: str = "TUSHARE_TOKEN",
) -> pd.DataFrame:
    """Fetch index valuation data from Tushare when account access permits it.

    This function currently tries the common ``index_dailybasic`` endpoint.
    If the endpoint is unavailable for the token, callers receive the original
    exception and can decide whether to ignore valuation factors.
    """

    token = os.getenv(token_env)
    if not token:
        raise RuntimeError(f"Environment variable {token_env} is not set.")

    try:
        import tushare as ts
    except ImportError as exc:
        raise RuntimeError("Package 'tushare' is not installed.") from exc

    ts.set_token(token)
    pro = ts.pro_api()
    fields = ",".join(VALUATION_COLUMNS)
    df = pro.index_dailybasic(ts_code=ts_code, start_date=start_date, end_date=end_date, fields=fields)
    if df is None or df.empty:
        return pd.DataFrame(columns=VALUATION_COLUMNS)

    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"].astype(str), errors="coerce")
    for col in ["pe", "pe_ttm", "pb"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[VALUATION_COLUMNS].sort_values("trade_date").reset_index(drop=True)


def merge_valuation_factors(price_factors: pd.DataFrame, valuation_df: pd.DataFrame) -> pd.DataFrame:
    """Merge optional valuation factors onto a factor table."""

    if valuation_df is None or valuation_df.empty:
        return price_factors
    return price_factors.merge(valuation_df, on=["ts_code", "trade_date"], how="left")
