"""Backtest performance metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def annualized_return(equity: pd.Series, annual_trading_days: int = 252) -> float:
    """Calculate annualized return from an equity curve."""

    valid = equity.dropna()
    if len(valid) < 2 or valid.iloc[0] <= 0:
        return np.nan
    years = len(valid) / annual_trading_days
    return float((valid.iloc[-1] / valid.iloc[0]) ** (1 / years) - 1)


def annualized_volatility(returns: pd.Series, annual_trading_days: int = 252) -> float:
    """Calculate annualized return volatility."""

    return float(returns.dropna().std() * np.sqrt(annual_trading_days))


def sharpe_ratio(returns: pd.Series, annual_trading_days: int = 252, risk_free_rate: float = 0.0) -> float:
    """Calculate annualized Sharpe ratio."""

    valid = returns.dropna()
    if valid.std() == 0 or valid.empty:
        return np.nan
    daily_rf = risk_free_rate / annual_trading_days
    return float((valid.mean() - daily_rf) / valid.std() * np.sqrt(annual_trading_days))


def max_drawdown(equity: pd.Series) -> float:
    """Calculate the maximum drawdown of an equity curve."""

    valid = equity.dropna()
    if valid.empty:
        return np.nan
    drawdown = valid / valid.cummax() - 1
    return float(drawdown.min())


def win_rate(returns: pd.Series) -> float:
    """Calculate the proportion of positive return days."""

    valid = returns.dropna()
    if valid.empty:
        return np.nan
    return float((valid > 0).mean())


def summarize_performance(
    returns: pd.Series,
    equity: pd.Series,
    annual_trading_days: int = 252,
) -> dict:
    """Return a dictionary of common performance metrics."""

    return {
        "annualized_return": annualized_return(equity, annual_trading_days),
        "max_drawdown": max_drawdown(equity),
        "sharpe_ratio": sharpe_ratio(returns, annual_trading_days),
        "volatility": annualized_volatility(returns, annual_trading_days),
        "win_rate": win_rate(returns),
    }
