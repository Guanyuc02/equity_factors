from __future__ import annotations

import pandas as pd

from ..factors_core import FactorContext
from .liquidity_shared import build_liquidity_factor, prep_liquidity_base


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Volatility of liquidity (share turnover) factor via 2×3 sorts.

    Characteristic:
        std_turn_char = trailing 12-month std dev of monthly turnover, lagged one month.
    Factor sign: WH − WL.
    """
    crsp_m = ctx.base.get("crsp_monthly")
    if crsp_m is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly'")

    d, month_index = prep_liquidity_base(crsp_m, start, end)
    d["std_turn"] = (
        d.groupby("permno", group_keys=False)["turn_m"]
        .rolling(window=12, min_periods=9)
        .std()
        .reset_index(level=0, drop=True)
    )
    d["std_turn_char"] = d.groupby("permno", group_keys=False)["std_turn"].shift(1)
    d = d.dropna(subset=["std_turn_char"])

    factor = build_liquidity_factor(
        d,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="std_turn_char",
        factor_name="std_turn",
        orientation="high_minus_low",
    )
    return factor
