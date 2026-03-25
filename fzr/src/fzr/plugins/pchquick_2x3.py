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
from .ff_shared import _prep_crsp, positive_book_equity_mask


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Percent change in quick ratio (pchquick) from 2×3 sorts (size × ΔQuick).

    Characteristic definition (quick ratio = (act − invt) / lct):
      pchquick = ( quick_t − quick_{t−1} ) / quick_{t−1}
               = quick_t / quick_{t−1} − 1

    Alignment and construction notes:
    - Use CCM-linked Compustat annual fundamentals (funda) aligned as-of each CRSP June.
    - Compute quick and its lag at the Compustat anchor level per permno over (permno, ym) rows,
      mirroring pchcurrat’s lag handling to avoid dependence on CRSP coverage of prior June.
    - NYSE breakpoints on size median and pchquick 30/70 quantiles.
    - Factor sign follows currat_2x3: WL − WH.

    Returns DataFrame with columns: date, pchquick
    """
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")

    # Restrict window with warm-up so first months have valid June assignments
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    # 25 months warm-up mirrors pchcurrat_2x3 for annual anchor + lag
    s_warm = s - pd.offsets.DateOffset(months=25)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)]

    # CRSP mechanics and FF calendar helpers
    crsp3, crsp_jun, month_index = _prep_crsp(cm)

    # Prepare Compustat annual anchors; use the template's deduped per (permno, ym) rows
    a = funda.copy()
    # Standardize date columns
    if "jdate_ltrd" in a.columns:
        a["jdate"] = pd.to_datetime(a["jdate_ltrd"], errors="coerce")
    elif "jdate" in a.columns:
        a["jdate"] = pd.to_datetime(a["jdate"], errors="coerce")
    else:
        raise ValueError("ccm_linked_funda is missing jdate/jdate_ltrd field")
    a["datadate"] = pd.to_datetime(a["datadate"], errors="coerce")
    if "ym" in a.columns:
        a["ym"] = pd.to_datetime(a["ym"], errors="coerce").dt.to_period("M")

    # Ensure required columns for quick ratio
    required_cols = {"act", "invt", "lct"}
    missing = sorted(required_cols - set(a.columns))
    if missing:
        raise ValueError(f"ccm_linked_funda missing required columns for pchquick: {missing}")

    # Compute quick_t and lagged quick at the Compustat anchor level first
    a = (
        a.sort_values(["permno", "ym", "datadate"])  # ensure stable order per month key
         .drop_duplicates(subset=["permno", "ym"], keep="last")
         .copy()
    )
    for col in ("act", "invt", "lct"):
        a[col] = pd.to_numeric(a[col], errors="coerce")
    # Quick ratio; guard against divide-by-zero and keep float64 dtype
    a["quick"] = np.nan
    denom = a["lct"].astype("float64")
    num = (a["act"].astype("float64") - a["invt"].astype("float64"))
    valid = denom.notna() & (denom != 0.0)
    a.loc[valid, "quick"] = (num.loc[valid] / denom.loc[valid]).to_numpy()

    a["quick_lag1"] = a.groupby("permno", group_keys=False)["quick"].shift(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        a["pchquick"] = a["quick"] / a["quick_lag1"] - 1.0
    a.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Merge Compustat June anchors (with pchquick) to CRSP June snapshot via month key
    jun = crsp_jun.copy()
    jun["ym"] = jun["ym"].astype("period[M]")
    june = jun.merge(
        a.rename(columns={"ym": "ym_a"}),
        left_on=["permno", "ym"], right_on=["permno", "ym_a"], how="inner",
        suffixes=("", "_a"),
    )

    be_mask = positive_book_equity_mask(
        funda,
        start=s,
        end=e,
        warm_months=25,
    )[["permno", "ym"]]
    june = june.merge(be_mask, on=["permno", "ym"], how="inner")

    # Exclude financials if SIC is available
    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    # Ensure NYSE exchange code is available as letters (N/A/Q)
    if "primaryexch" not in june.columns and "exchcd" in june.columns:
        june = june.copy()
        june["primaryexch"] = june["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    # NYSE breakpoints on size median and pchquick 30/70
    sz_bp = nyse_size_median(june, date_col="jdate", exch_col="primaryexch", me_col="me")
    pq_bp = nyse_quantiles(
        june,
        value_col="pchquick", date_col="jdate", exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june["pchquick"].notna()),
    )

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(pq_bp, on="jdate", how="left")

    # Assign 2×3 portfolios: size (S/B) × pchquick (L/M/H)
    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="pchquick",
        size_bp_col="sizemedn",
        # nyse_quantiles returns f"{value_col}30"/f"{value_col}70" columns
        char_q30_col="pchquick30",
        char_q70_col="pchquick70",
        out_size="szport",
        out_char="pqport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["pchquick"].notna()),
    )

    # Bring June labels into the monthly panel for VW returns
    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "pqport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    d = monthly_labeled[(monthly_labeled["wt"] > 0) & monthly_labeled[["szport", "pqport"]].ne("").all(axis=1)]
    wide = value_weighted_returns(
        d,
        date_col="jdate", ret_col="mthret", weight_col="wt",
        size_bucket_col="szport", char_bucket_col="pqport",
    )
    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                pchquick=lambda x: apply_orientation(x["WH"], x["WL"], "low_minus_high"),  # WL minus WH, mirrors currat_2x3
            )[["jdate", "pchquick"]]
            .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )
    return factor
