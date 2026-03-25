from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ia_shared import _prep_june_funda, build_2x3_factor


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Change in inventory (chinv) factor from 2×3 sorts.

    Characteristic:
        chinv = (invt − invt_{t−1}) / at_{t−1}
    Factor sign: WL − WH (low inventory buildup minus high).
    """
    june, crsp3, month_index = _prep_june_funda(
        ctx,
        start=start,
        end=end,
        required_cols=["invt", "at"],
        warm_months=25,
        require_be=True,
    )

    june["invt_lag"] = june.groupby("permno", group_keys=False)["invt"].shift(1)
    june["at_lag"] = june.groupby("permno", group_keys=False)["at"].shift(1)
    denom = june["at_lag"].where(june["at_lag"].abs() > 0)
    june["chinv"] = np.where(denom.notna(), (june["invt"] - june["invt_lag"]) / denom, np.nan)
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    factor = build_2x3_factor(
        june,
        crsp3,
        month_index,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        char_col="chinv",
        factor_name="chinv",
        orientation="low_minus_high",
    )
    return factor
