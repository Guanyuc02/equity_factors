from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ia_shared import _prep_june_funda, build_2x3_factor


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Advertising expense-to-market (adm) factor via 2×3 sorts.

    Characteristic:
        adm = xad / dec_me using fiscal-year xad aligned to June
    Factor sign: WL − WH (advertising intensity low minus high).
    """
    june, crsp3, month_index = _prep_june_funda(
        ctx,
        start=start,
        end=end,
        required_cols=["xad"],
        warm_months=13,
        require_be=True,
    )

    denom = pd.to_numeric(june.get("dec_me"), errors="coerce")
    eps = 1e-6
    valid = denom.abs() > eps
    june["adm_char"] = np.where(valid, june["xad"] / denom, np.nan)
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    factor = build_2x3_factor(
        june,
        crsp3,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="adm_char",
        factor_name="adm",
        orientation="low_minus_high",
    )
    return factor
