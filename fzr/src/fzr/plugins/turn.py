from __future__ import annotations

import pandas as pd

from ..factors_core import (
    FactorContext,
    nyse_size_median,
    nyse_quantiles,
    assign_2x3,
    value_weighted_returns,
)


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    crsp_m = ctx.base.get("crsp_monthly")
    if crsp_m is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly'")

    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=13)

    d = crsp_m.copy()
    d["mthcaldt"] = pd.to_datetime(d["mthcaldt"], errors="coerce")
    d = d[(d["mthcaldt"] >= s_warm) & (d["mthcaldt"] <= e)]

    if "shrcd" in d.columns:
        d = d[d["shrcd"].isin([10, 11])]

    if "vol" not in d.columns:
        raise ValueError("crsp_monthly must include 'vol'")

    d = d.sort_values(["permno", "mthcaldt"])

    d["jdate"] = d["mthcaldt"]

    d["me"] = (d["mthprc"].abs() * d["shrout"]).astype("float")
    d["wt"] = d.groupby("permno")["me"].shift(1)

    d["turn_m"] = d["vol"] / d["shrout"]
    d.loc[d["shrout"] <= 0, "turn_m"] = pd.NA

    if "exchcd" in d.columns:
        mask_nasdaq = d["exchcd"] == 3
        dt1 = pd.Timestamp("2001-02-01")
        dt2 = pd.Timestamp("2002-01-01")
        dt3 = pd.Timestamp("2004-01-01")

        m1 = mask_nasdaq & (d["mthcaldt"] < dt1)
        m2 = mask_nasdaq & (d["mthcaldt"] >= dt1) & (d["mthcaldt"] < dt2)
        m3 = mask_nasdaq & (d["mthcaldt"] >= dt2) & (d["mthcaldt"] < dt3)

        d.loc[m1, "turn_m"] = d.loc[m1, "turn_m"] / 2.0
        d.loc[m2, "turn_m"] = d.loc[m2, "turn_m"] / 1.8
        d.loc[m3, "turn_m"] = d.loc[m3, "turn_m"] / 1.6

    d["turn6"] = (
        d.groupby("permno", group_keys=False)["turn_m"]
        .rolling(window=6, min_periods=3)
        .mean()
        .reset_index(level=0, drop=True)
    )
    d["turn"] = d.groupby("permno")["turn6"].shift(1)

    d = d.dropna(subset=["turn", "mthret", "me", "wt"])

    bp_size = nyse_size_median(
        d, date_col="jdate", exch_col="primaryexch", me_col="me"
    )
    bp_turn = nyse_quantiles(
        d,
        value_col="turn",
        date_col="jdate",
        exch_col="primaryexch",
        lower_q=0.3,
        upper_q=0.7,
    )

    dd = (
        d.merge(bp_size, on="jdate", how="left")
         .merge(bp_turn, on="jdate", how="left")
    )

    dd = assign_2x3(
        dd,
        date_col="jdate",
        size_col="me",
        char_col="turn",
        size_bp_col="sizemedn",
        char_q30_col="turn30",
        char_q70_col="turn70",
        out_size="szport",
        out_char="bmport",
        valid_mask=dd["turn"].notna() & dd["me"].notna(),
    )

    vw = value_weighted_returns(
        dd,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="bmport",
    )

    vw["turn"] = -(
        0.5 * (vw["SL"] + vw["BL"]) - 0.5 * (vw["SH"] + vw["BH"])
    )

    out = vw[["jdate", "turn"]].rename(columns={"jdate": "date"})
    out = out[(out["date"] >= s) & (out["date"] <= e)]
    out = out.sort_values("date").reset_index(drop=True)
    return out
