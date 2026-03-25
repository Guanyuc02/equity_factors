from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ia_shared import _industry_adjust, _prep_june_funda, build_2x3_factor


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Industry-adjusted size (mve_ia) factor via 2×3 sorts.

    Characteristic:
        log_me = ln(June market equity)
        mve_ia = log_me − industry_median(log_me) using 2-digit SIC

    Factor sign: WL − WH (small relative to industry minus big).
    """
    june, crsp3, month_index = _prep_june_funda(
        ctx,
        start=start,
        end=end,
        required_cols=[],
        warm_months=13,
        require_be=True,
    )

    june["log_me"] = np.log(pd.to_numeric(june.get("me"), errors="coerce"))
    june.replace([np.inf, -np.inf], np.nan, inplace=True)
    june["mve_ia"] = _industry_adjust(june, "log_me")

    factor = build_2x3_factor(
        june,
        crsp3,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="mve_ia",
        factor_name="mve_ia",
        orientation="low_minus_high",
    )
    return factor
