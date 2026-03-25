from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ia_shared import _industry_adjust, _prep_june_funda, build_2x3_factor


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Industry-adjusted cash flow-to-price (cfp_ia) factor via 2×3 sorts.

    Characteristic:
        cash_flow = oancf when available, else ib + dp
        cfp = cash_flow / dec_me (December market equity from CRSP)
        cfp_ia = cfp − industry_median(cfp) using 2-digit SIC each June

    Construction:
        - Align Compustat fiscal-year data to CRSP June (t) using CCM links.
        - NYSE size median and NYSE 30/70 breakpoints on cfp_ia.
        - Factor = WH − WL (high cash-flow yield minus low).
    """
    june, crsp3, month_index = _prep_june_funda(
        ctx,
        start=start,
        end=end,
        required_cols=["ib", "dp", "oancf"],
        warm_months=25,
        require_be=True,
    )

    cash_flow = pd.to_numeric(june.get("oancf"), errors="coerce")
    fallback = pd.to_numeric(june.get("ib"), errors="coerce") + pd.to_numeric(june.get("dp"), errors="coerce")
    june["cash_flow"] = cash_flow.where(cash_flow.notna(), fallback)

    denom = pd.to_numeric(june.get("dec_me"), errors="coerce")
    eps = 1e-6
    valid = denom.abs() > eps
    june["cfp_raw"] = np.where(valid, june["cash_flow"] / denom, np.nan)
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    june["cfp_ia"] = _industry_adjust(june, "cfp_raw")

    factor = build_2x3_factor(
        june,
        crsp3,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="cfp_ia",
        factor_name="cfp_ia",
        orientation="high_minus_low",
    )
    return factor
