from __future__ import annotations

import numpy as np
import pandas as pd

from ..calendar import month_index_from_crsp
from ..factors_core import (
    FactorOrientation,
    apply_orientation,
    assign_2x3,
    nyse_quantiles,
    nyse_size_median,
    value_weighted_returns,
)
from .ff_shared import _universe_filters


def _nasdaq_volume_adjustments(df: pd.DataFrame, date_col: str = "mthcaldt") -> pd.Series:
    vol_adj = pd.to_numeric(df.get("vol"), errors="coerce")
    if "exchcd" not in df.columns:
        return vol_adj

    mask_nasdaq = df["exchcd"] == 3
    dt1 = pd.Timestamp("2001-02-01")
    dt2 = pd.Timestamp("2002-01-01")
    dt3 = pd.Timestamp("2004-01-01")

    m1 = mask_nasdaq & (df[date_col] < dt1)
    m2 = mask_nasdaq & (df[date_col] >= dt1) & (df[date_col] < dt2)
    m3 = mask_nasdaq & (df[date_col] >= dt2) & (df[date_col] < dt3)

    vol_adj = vol_adj.copy()
    vol_adj.loc[m1] = vol_adj.loc[m1] / 2.0
    vol_adj.loc[m2] = vol_adj.loc[m2] / 1.8
    vol_adj.loc[m3] = vol_adj.loc[m3] / 1.6
    return vol_adj


def prep_liquidity_base(crsp_m: pd.DataFrame, start: str, end: str) -> tuple[pd.DataFrame, pd.Series]:
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=13)

    d = crsp_m.copy()
    d["mthcaldt"] = pd.to_datetime(d["mthcaldt"], errors="coerce")
    d = d[(d["mthcaldt"] >= s_warm) & (d["mthcaldt"] <= e)]
    d = _universe_filters(d)
    d = d.sort_values(["permno", "mthcaldt"])

    d["vol_adj"] = _nasdaq_volume_adjustments(d, date_col="mthcaldt")
    d["mthprc_abs"] = pd.to_numeric(d.get("mthprc"), errors="coerce").abs()
    d["shrout"] = pd.to_numeric(d.get("shrout"), errors="coerce")

    d["me"] = (d["mthprc_abs"] * d["shrout"]).astype("float")
    d["wt"] = d.groupby("permno")["me"].shift(1)

    d["turn_m"] = d["vol_adj"] / d["shrout"]
    d.loc[d["shrout"] <= 0, "turn_m"] = pd.NA

    d["dollar_vol"] = d["vol_adj"] * d["mthprc_abs"]
    d.loc[d["dollar_vol"] <= 0, "dollar_vol"] = pd.NA
    d["ldolvol"] = np.log(d["dollar_vol"])
    d.replace([np.inf, -np.inf], np.nan, inplace=True)

    if "primaryexch" not in d.columns and "exchcd" in d.columns:
        d = d.copy()
        d["primaryexch"] = d["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    month_index = month_index_from_crsp(d, "mthcaldt")
    return d, month_index[(month_index >= s) & (month_index <= e)]


def build_liquidity_factor(
    d: pd.DataFrame,
    month_index: pd.Series,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    char_col: str,
    factor_name: str,
    orientation: FactorOrientation,
) -> pd.DataFrame:
    bp_size = nyse_size_median(d, date_col="mthcaldt", exch_col="primaryexch", me_col="me")
    bp_char = nyse_quantiles(
        d,
        value_col=char_col,
        date_col="mthcaldt",
        exch_col="primaryexch",
        sample_filter=(d["me"].gt(0) & d[char_col].notna()),
    )

    dd = d.merge(bp_size, on="mthcaldt", how="left").merge(bp_char, on="mthcaldt", how="left")
    dd = assign_2x3(
        dd,
        date_col="mthcaldt",
        size_col="me",
        char_col=char_col,
        size_bp_col="sizemedn",
        char_q30_col=f"{char_col}30",
        char_q70_col=f"{char_col}70",
        out_size="szport",
        out_char=f"{char_col}_port",
        valid_mask=(dd["me"].gt(0) & dd[char_col].notna()),
    )

    dd = dd.dropna(subset=["wt", "mthret", "me"])
    dd = dd[dd["wt"] > 0]

    vw = value_weighted_returns(
        dd,
        date_col="mthcaldt",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col=f"{char_col}_port",
    )

    factor = (
        vw[["mthcaldt", "SL", "SM", "SH", "BL", "BM", "BH"]]
        .assign(
            WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
            WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
        )
        .assign(
            **{
                factor_name: lambda x: apply_orientation(x["WH"], x["WL"], orientation)
            }
        )[["mthcaldt", factor_name]]
        .rename(columns={"mthcaldt": "date"})
    )

    factor = (
        factor.set_index("date")
        .reindex(month_index[(month_index >= start) & (month_index <= end)])
        .rename_axis("date")
        .reset_index()
    )
    return factor
