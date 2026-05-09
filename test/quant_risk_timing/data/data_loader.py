"""Tushare data loading and local cache management."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd


REQUIRED_INDEX_DAILY_COLUMNS = [
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "vol",
    "amount",
]


class DataLoaderError(RuntimeError):
    """Raised when market data cannot be loaded or validated."""


class TushareIndexDataLoader:
    """Load index daily data from Tushare with a CSV cache fallback."""

    def __init__(self, cache_dir: str | Path = "data/cache", token_env: str = "TUSHARE_TOKEN") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token_env = token_env

    def get_index_daily(
        self,
        ts_code: str,
        start_date: str = "20150101",
        end_date: Optional[str] = None,
        refresh: bool = False,
    ) -> pd.DataFrame:
        """Return validated daily index data for one Tushare index code.

        Cached data is used first unless ``refresh`` is true. If the cache
        cannot satisfy the requested date range, the method calls Tushare and
        then rewrites the local cache.
        """

        start_date = _normalize_tushare_date(start_date)
        end_date = _normalize_tushare_date(end_date) if end_date else datetime.today().strftime("%Y%m%d")
        cache_path = self._cache_path(ts_code)

        if cache_path.exists() and not refresh:
            cached = self._read_cache(cache_path, ts_code, start_date, end_date)
            if not cached.empty:
                return cached

        fetched = self._fetch_index_daily(ts_code, start_date, end_date)
        self._write_cache(cache_path, fetched)
        return self._filter_by_date(fetched, start_date, end_date)

    def load_indices(
        self,
        index_codes: Iterable[str],
        start_date: str = "20150101",
        end_date: Optional[str] = None,
        refresh: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Load a dictionary of index data keyed by Tushare code."""

        return {
            ts_code: self.get_index_daily(ts_code, start_date=start_date, end_date=end_date, refresh=refresh)
            for ts_code in index_codes
        }

    def _cache_path(self, ts_code: str) -> Path:
        safe_code = ts_code.replace(".", "_")
        return self.cache_dir / f"{safe_code}_index_daily.csv"

    def _read_cache(self, cache_path: Path, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(cache_path)
            df = _standardize_index_daily(df, ts_code)
            df = self._filter_by_date(df, start_date, end_date)
            if df.empty:
                return pd.DataFrame()
            return df
        except Exception as exc:  # pragma: no cover - defensive cache recovery
            raise DataLoaderError(f"Failed to read cache {cache_path}: {exc}") from exc

    def _fetch_index_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        token = os.getenv(self.token_env)
        if not token:
            raise DataLoaderError(
                f"Environment variable {self.token_env} is not set and no usable cache was found."
            )

        try:
            import tushare as ts
        except ImportError as exc:
            raise DataLoaderError("Package 'tushare' is not installed. Run pip install -r requirements.txt.") from exc

        try:
            ts.set_token(token)
            pro = ts.pro_api()
            fields = "ts_code,trade_date,open,high,low,close,vol,amount"
            df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, fields=fields)
        except Exception as exc:
            raise DataLoaderError(f"Tushare index_daily call failed for {ts_code}: {exc}") from exc

        return _standardize_index_daily(df, ts_code)

    @staticmethod
    def _filter_by_date(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date)
        mask = (df["trade_date"] >= start_ts) & (df["trade_date"] <= end_ts)
        return df.loc[mask].sort_values("trade_date").reset_index(drop=True)

    @staticmethod
    def _write_cache(cache_path: Path, df: pd.DataFrame) -> None:
        output = df.copy()
        output["trade_date"] = output["trade_date"].dt.strftime("%Y-%m-%d")
        output.to_csv(cache_path, index=False, encoding="utf-8-sig")


def _standardize_index_daily(df: pd.DataFrame, ts_code: str) -> pd.DataFrame:
    """Validate and standardize raw Tushare index daily data."""

    if df is None or df.empty:
        raise DataLoaderError(f"No index_daily data returned for {ts_code}.")

    missing = [col for col in REQUIRED_INDEX_DAILY_COLUMNS if col not in df.columns]
    if missing:
        raise DataLoaderError(f"Missing required columns for {ts_code}: {missing}")

    output = df.copy()
    if "ts_code" not in output.columns:
        output["ts_code"] = ts_code
    output["trade_date"] = pd.to_datetime(output["trade_date"].astype(str), errors="coerce")
    if output["trade_date"].isna().any():
        raise DataLoaderError(f"Invalid trade_date values found for {ts_code}.")

    numeric_cols = ["open", "high", "low", "close", "vol", "amount"]
    for col in numeric_cols:
        output[col] = pd.to_numeric(output[col], errors="coerce")
    if output[numeric_cols].isna().any().any():
        bad_cols = output[numeric_cols].columns[output[numeric_cols].isna().any()].tolist()
        raise DataLoaderError(f"Non-numeric or missing market fields for {ts_code}: {bad_cols}")

    columns = ["ts_code"] + REQUIRED_INDEX_DAILY_COLUMNS
    return output[columns].sort_values("trade_date").drop_duplicates("trade_date").reset_index(drop=True)


def _normalize_tushare_date(value: str) -> str:
    """Normalize common date inputs into Tushare's YYYYMMDD string format."""

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise DataLoaderError(f"Invalid date value: {value}")
    return parsed.strftime("%Y%m%d")
