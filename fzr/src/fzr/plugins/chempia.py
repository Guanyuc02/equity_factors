from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ia_shared import _industry_adjust, _prep_june_funda, build_2x3_factor


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Industry-adjusted change in employees (chempia) from 2×3 sorts.

    Characteristic:
        chemp = emp_t / emp_{t−1} − 1
        chempia = chemp − industry_median(chemp) by 2-digit SIC each June

    Factor sign: WH − WL (higher hiring relative to peers is the "high" leg).
    """
    june, crsp3, month_index = _prep_june_funda(
        ctx,
        start=start,
        end=end,
        required_cols=["emp"],
        warm_months=25,
        require_be=True,
    )

    june["emp_lag"] = june.groupby("permno", group_keys=False)["emp"].shift(1)
    denom = june["emp_lag"].where(june["emp_lag"].abs() > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        june["chemp"] = june["emp"] / denom - 1.0
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    june["chempia"] = _industry_adjust(june, "chemp")

    factor = build_2x3_factor(
        june,
        crsp3,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="chempia",
        factor_name="chempia",
        orientation="low_minus_high",
    )
    return factor
