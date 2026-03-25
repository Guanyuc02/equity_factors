from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import (
    FactorContext,
    apply_orientation,
    assign_2x3,
    nyse_quantiles,
    nyse_size_median,
    value_weighted_returns,
)
from .ff_shared import _prep_crsp


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    crsp_m = ctx.base.get("crsp_monthly")
    if crsp_m is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly'")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=40)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)]

    crsp3, crsp_jun, month_index = _prep_crsp(cm)

    crsp = crsp3.copy()
    crsp = crsp.sort_values(["permno", "mthcaldt"])
    crsp["ret1p"] = 1.0 + crsp["mthret"].fillna(0.0)

    roll = (
        crsp.groupby("permno")["ret1p"]
        .rolling(35, min_periods=35)
        .apply(np.prod, raw=True)
        .reset_index(level=0, drop=True)
    )
    crsp["mom36m_signal"] = roll.shift(2) - 1.0
    crsp = crsp.dropna(subset=["mom36m_signal", "me", "mthret", "wt"])

    if "primaryexch" not in crsp.columns and "exchcd" in crsp.columns:
        crsp = crsp.copy()
        crsp["primaryexch"] = crsp["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    sz_bp = nyse_size_median(
        crsp,
        date_col="jdate",
        exch_col="primaryexch",
        me_col="me",
    )
    mom_bp = nyse_quantiles(
        crsp,
        value_col="mom36m_signal",
        date_col="jdate",
        exch_col="primaryexch",
        sample_filter=(crsp["me"].gt(0) & crsp["mom36m_signal"].notna()),
    )

    crsp_bp = crsp.merge(sz_bp, on="jdate", how="left").merge(mom_bp, on="jdate", how="left")

    crsp_ports = assign_2x3(
        crsp_bp,
        date_col="jdate",
        size_col="me",
        char_col="mom36m_signal",
        size_bp_col="sizemedn",
        char_q30_col="mom36m_signal30",
        char_q70_col="mom36m_signal70",
        out_size="szport",
        out_char="mom36port",
        valid_mask=(crsp_bp["me"].gt(0) & crsp_bp["mom36m_signal"].notna()),
    )

    d = crsp_ports[
        (crsp_ports["wt"] > 0)
        & crsp_ports[["szport", "mom36port"]].ne("").all(axis=1)
    ]
    wide = value_weighted_returns(
        d,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="mom36port",
    )

    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
        .assign(
            WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
            WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
            mom36m=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
        )[["jdate", "mom36m"]]
        .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
        .reindex(month_index[(month_index >= s) & (month_index <= e)])
        .rename_axis("date")
        .reset_index()
    )
    return factor
