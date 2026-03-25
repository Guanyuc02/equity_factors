from __future__ import annotations

import pandas as pd

import numpy as np
from ..factors_core import FactorContext
from .ff_shared import prepare_base, Prepared


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Currat factor from 2×3 sorts (size × current ratio).

    Sign convention: WL minus WH.
    Returns DataFrame with columns: date, currat
    """
    prep = prepare_base(ctx, start=start, end=end)
    cr = compute_currat(prep)
    return cr[["date", "currat"]]


def compute_currat(prep: Prepared) -> pd.DataFrame:
    d = prep.ccm_monthly_with_ports.copy()
    if "crport" not in d.columns:
        # No current ratio labels prepared; return empty frame
        return pd.DataFrame({"date": prep.month_index, "currat": np.nan})
    d = d[(d["wt"] > 0) & d[["szport", "crport"]].ne("").all(axis=1)]
    from ..factors_core import apply_orientation, value_weighted_returns  # local import to avoid cycles
    wide = value_weighted_returns(
        d,
        date_col="jdate", ret_col="mthret", weight_col="wt",
        size_bucket_col="szport", char_bucket_col="crport",
    )
    cr = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                currat=lambda x: apply_orientation(x["WH"], x["WL"], "low_minus_high"),  # WL minus WH per spec
            )[["jdate", "currat"]]
            .rename(columns={"jdate": "date"})
    )
    cr = (
        cr.set_index("date")
          .reindex(prep.month_index)
          .rename_axis("date")
          .reset_index()
    )
    return cr
