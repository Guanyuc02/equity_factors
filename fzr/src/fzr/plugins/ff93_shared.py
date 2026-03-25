from __future__ import annotations

import pandas as pd

from ..factors_core import apply_orientation, value_weighted_returns
from .ff_shared import Prepared


def compute_smb_hml(prep: Prepared) -> pd.DataFrame:
    d = prep.ccm_monthly_with_ports.copy()
    # Filter to stocks with valid size and BM labels and positive weights
    d = d[(d["wt"] > 0) & d[["szport", "bmport"]].ne("").all(axis=1)]
    wide = value_weighted_returns(
        d,
        date_col="jdate", ret_col="mthret", weight_col="wt",
        size_bucket_col="szport", char_bucket_col="bmport",
    )
    ff = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                HML=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
                WB=lambda x: (x["BL"] + x["BM"] + x["BH"]) / 3.0,
                WS=lambda x: (x["SL"] + x["SM"] + x["SH"]) / 3.0,
                SMB=lambda x: x["WS"] - x["WB"],
            )[["jdate", "SMB", "HML"]]
            .rename(columns={"jdate": "date"})
    )
    # Reindex to CRSP last-trading-month index
    ff = (
        ff.set_index("date")
          .reindex(prep.month_index)
          .rename_axis("date")
          .reset_index()
    )
    return ff
