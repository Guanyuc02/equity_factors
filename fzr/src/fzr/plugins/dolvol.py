from __future__ import annotations

import pandas as pd

from ..factors_core import FactorContext
from .liquidity_shared import build_liquidity_factor, prep_liquidity_base


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Dollar trading volume (dolvol) factor via 2×3 sorts.

    Characteristic:
        dolvol_char = trailing 12-month mean of log dollar volume, lagged one month.
    Factor sign: WL − WH (illiquidity premium: low volume minus high).
    """
    crsp_m = ctx.base.get("crsp_monthly")
    if crsp_m is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly'")

    d, month_index = prep_liquidity_base(crsp_m, start, end)
    d["ldolvol_mean12"] = (
        d.groupby("permno", group_keys=False)["ldolvol"]
        .rolling(window=12, min_periods=9)
        .mean()
        .reset_index(level=0, drop=True)
    )
    d["dolvol_char"] = d.groupby("permno", group_keys=False)["ldolvol_mean12"].shift(1)

    d = d.dropna(subset=["dolvol_char"])

    factor = build_liquidity_factor(
        d,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="dolvol_char",
        factor_name="dolvol",
        orientation="low_minus_high",
    )
    return factor
