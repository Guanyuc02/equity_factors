from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ia_shared import _prep_june_funda, build_2x3_factor


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Change in tax expense (chtx) factor via 2×3 sorts.

    Characteristic:
        chtx = (txt − txt_{t−1}) / at_{t−1}
    Factor sign: WH − WL.
    """
    june, crsp3, month_index = _prep_june_funda(
        ctx,
        start=start,
        end=end,
        required_cols=["txt", "at"],
        warm_months=25,
        require_be=True,
    )

    june["txt_lag"] = june.groupby("permno", group_keys=False)["txt"].shift(1)
    june["at_lag"] = june.groupby("permno", group_keys=False)["at"].shift(1)
    denom = june["at_lag"].where(june["at_lag"].abs() > 0)
    june["chtx"] = np.where(denom.notna(), (june["txt"] - june["txt_lag"]) / denom, np.nan)
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    factor = build_2x3_factor(
        june,
        crsp3,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="chtx",
        factor_name="chtx",
        orientation="high_minus_low",
    )
    return factor
