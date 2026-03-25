from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from ..calendar import month_index_from_crsp
from ..factors_core import (
    FactorContext,
    nyse_size_median,
    nyse_quantiles,
    assign_2x3,
)


@dataclass(frozen=True)
class Prepared:
    # Last trading day per month over requested window
    month_index: pd.Series
    # Monthly time-series slice used for VW returns with portfolio labels
    ccm_monthly_with_ports: pd.DataFrame
    # June-only assignment frame with breakpoints (for debugging/inspection)
    june_assignments: pd.DataFrame


def positive_book_equity_mask(
    funda: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    warm_months: int,
) -> pd.DataFrame:
    """Return permno×month pairs (plus SIC when available) with strictly positive book equity."""
    if funda is None:
        raise ValueError("ccm_linked_funda is required to screen on book equity")
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=warm_months)

    d = funda.copy()
    if "jdate_ltrd" in d.columns:
        d["jdate"] = pd.to_datetime(d["jdate_ltrd"], errors="coerce")
    elif "jdate" in d.columns:
        d["jdate"] = pd.to_datetime(d["jdate"], errors="coerce")
    else:
        raise ValueError("ccm_linked_funda is missing jdate/jdate_ltrd field")
    if "datadate" in d.columns:
        d["datadate"] = pd.to_datetime(d["datadate"], errors="coerce")
    d = d[(d["jdate"] >= s_warm) & (d["jdate"] <= e)]

    if "ym" in d.columns:
        d["ym"] = pd.to_datetime(d["ym"], errors="coerce").dt.to_period("M")
    else:
        d["ym"] = d["jdate"].dt.to_period("M")

    if "be" not in d.columns:
        raise ValueError("ccm_linked_funda is missing 'be' column required for book equity screens")
    d["be"] = pd.to_numeric(d["be"], errors="coerce")
    d = d[d["be"].gt(0)]

    sort_cols = ["permno", "ym", "jdate"]
    if "datadate" in d.columns:
        sort_cols.append("datadate")
    d = (
        d.sort_values(sort_cols)
         .dropna(subset=["permno", "ym"])
         .drop_duplicates(subset=["permno", "ym"], keep="last")
    )

    cols = ["permno", "ym"]
    if "sic" in d.columns:
        cols.append("sic")
    mask = d[cols].copy()
    return mask


def _universe_filters(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    # Keep common shares (shrcd 10,11) and primary exchanges N/A/Q when available
    cols = set(d.columns)
    if {"shrcd"}.issubset(cols):
        d = d[d["shrcd"].isin([10, 11])]
    # Prefer numeric exchcd if present; otherwise fallback to CRSP primaryexch letters
    if "exchcd" in cols:
        d = d[d["exchcd"].isin([1, 2, 3])]
    elif "primaryexch" in cols:
        d = d[d["primaryexch"].isin(["N", "A", "Q"])]
    return d


def _prep_crsp(crsp_m: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Compute market equity collapse by permco, baseline weights, December ME, and June panel.

    Returns (crsp3, crsp_jun, month_index)
    """
    d = crsp_m.copy()
    d["mthcaldt"] = pd.to_datetime(d["mthcaldt"])
    d = _universe_filters(d)

    # Month index on last trading day
    month_index = month_index_from_crsp(d, "mthcaldt")

    # jdate aligned to last trading day we observed
    d["jdate"] = d["mthcaldt"]
    # Returns and ME inputs
    d["mthret"] = d["mthret"].fillna(0.0)
    d["mthretx"] = d["mthretx"].fillna(0.0)
    d["me"] = d["mthprc"].abs() * d["shrout"]
    d = d.drop(columns=[c for c in ["mthprc", "shrout"] if c in d.columns])
    d = d.sort_values(["jdate", "permco", "me"])  # stable for tie-breaks

    # Collapse to permco by summing ME and selecting max permno representative
    crsp_summe = d.groupby(["jdate", "permco"], as_index=False)["me"].sum().rename(columns={"me": "me_sum"})
    # Keep the 'me' column name to allow joining on (jdate, permco, me) like wrds_factors.py
    crsp_maxme = d.groupby(["jdate", "permco"], as_index=False)["me"].max()
    crsp1 = d.merge(crsp_maxme, how="inner", on=["jdate", "permco", "me"])  # representative permno rows
    crsp2 = crsp1.drop(columns=["me"]).merge(crsp_summe, how="inner", on=["jdate", "permco"]).rename(columns={"me_sum": "me"})
    crsp2 = crsp2.sort_values(["permno", "jdate"]).drop_duplicates()

    # Month/year helpers
    crsp2["year"] = crsp2["jdate"].dt.year
    crsp2["month"] = crsp2["jdate"].dt.month

    # December ME (for BE/ME denominator; year switches to next year for June assignment)
    decme = crsp2[crsp2["month"] == 12][["permno", "jdate", "me", "year"]].rename(columns={"me": "dec_me"})
    decme["year"] = decme["year"] + 1
    decme = decme[["permno", "year", "dec_me"]]

    # July-June FF calendar mechanics
    crsp2["ffdate"] = crsp2["jdate"] + pd.offsets.MonthEnd(-6)
    crsp2["ffyear"] = crsp2["ffdate"].dt.year
    crsp2["ffmonth"] = crsp2["ffdate"].dt.month
    crsp2["one_plus_retx"] = 1.0 + crsp2["mthretx"]
    crsp2 = crsp2.sort_values(["permno", "mthcaldt"])  # use mthcaldt for cumprod ordering
    crsp2["cumretx"] = crsp2.groupby(["permno", "ffyear"], group_keys=False)["one_plus_retx"].cumprod()
    crsp2["lcumretx"] = crsp2.groupby(["permno"], group_keys=False)["cumretx"].shift(1)
    crsp2["lme"] = crsp2.groupby(["permno"], group_keys=False)["me"].shift(1)

    # Seed first observation lme using me/(1+retx)
    crsp2["count"] = crsp2.groupby(["permno"]).cumcount()
    crsp2.loc[crsp2["count"] == 0, "lme"] = crsp2.loc[crsp2["count"] == 0, "me"] / crsp2.loc[crsp2["count"] == 0, "one_plus_retx"]

    # Baseline ME for weights
    mebase = crsp2[crsp2["ffmonth"] == 1][["permno", "ffyear", "lme"]].rename(columns={"lme": "mebase"})
    crsp3 = crsp2.merge(mebase, how="left", on=["permno", "ffyear"]).copy()
    crsp3["wt"] = np.where(crsp3["ffmonth"] == 1, crsp3["lme"], crsp3["mebase"] * crsp3["lcumretx"])

    # Info as of June (month==6), keep CRSP last-trading-day date, build month key for joins
    crsp3_jun = crsp3[crsp3["month"] == 6].copy()
    crsp_jun = crsp3_jun.merge(decme, how="inner", on=["permno", "year"])  # ensures positive dec_me later
    crsp_jun = crsp_jun.rename(columns={"jdate": "jdate"})
    crsp_jun["ym"] = crsp_jun["jdate"].dt.to_period("M")
    crsp_jun = crsp_jun.sort_values(["permno", "jdate"]).drop_duplicates()

    return crsp3, crsp_jun, month_index


def prepare_base(ctx: FactorContext, *, start: str, end: str) -> Prepared:
    """Prepare merged CRSP × Compustat base with 2×3 portfolio labels.

    - Computes NYSE breakpoints (size median; 30/70 quantiles for BM and currat)
    - Produces a June assignment snapshot and a monthly panel with portfolio labels
    """
    crsp_m = ctx.base.get("crsp_monthly")
    ccm = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or ccm is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")
    ccm_raw = ccm

    # Restrict to requested window
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    # Include a pre-start buffer so that the first months in [start, end]
    # have valid June portfolio assignments and December ME denominators.
    # 13 months ensures we capture the prior June and prior December.
    s_warm = s - pd.offsets.DateOffset(months=13)
    crsp_m = crsp_m.copy()
    crsp_m["mthcaldt"] = pd.to_datetime(crsp_m["mthcaldt"])  # ensure dtype
    crsp_m = crsp_m[(crsp_m["mthcaldt"] >= s_warm) & (crsp_m["mthcaldt"] <= e)]

    ccm = ccm.copy()
    # jdate_ltrd field is CRSP last-trading-day date; keep name continuity as 'jdate'
    if "jdate_ltrd" in ccm.columns:
        ccm["jdate"] = pd.to_datetime(ccm["jdate_ltrd"])  # keep original too
    elif "jdate" in ccm.columns:
        ccm["jdate"] = pd.to_datetime(ccm["jdate"])  # fallback
    else:
        raise ValueError("ccm_linked_funda is missing jdate/jdate_ltrd field")
    ccm = ccm[(ccm["jdate"] >= s_warm) & (ccm["jdate"] <= e)]

    # CRSP mechanics and month index
    crsp3, crsp_jun, month_index = _prep_crsp(crsp_m)

    # Merge Compustat anchors (one row per permno×ym; template already deduped)
    # Normalize month keys to the same dtype to avoid silent mismatches (Period vs Timestamp)
    if "ym" in ccm.columns:
        ccm["ym"] = pd.to_datetime(ccm["ym"], errors="coerce").dt.to_period("M")
    crsp_jun = crsp_jun.copy()
    crsp_jun["ym"] = crsp_jun["ym"].astype("period[M]")
    # Keep CRSP's last trading day date from crsp_jun
    ccm_jun = crsp_jun.merge(
        ccm.rename(columns={"ym": "ym_ccm"}),  # keep ym for robustness
        left_on=["permno", "ym"], right_on=["permno", "ym_ccm"], how="inner",
        suffixes=("", "_ccm"),
    )
    be_mask = positive_book_equity_mask(ccm_raw, start=s, end=e, warm_months=13)
    if not be_mask.empty:
        ccm_jun = ccm_jun.merge(
            be_mask.rename(columns={"ym": "ym_ccm"})[["permno", "ym_ccm"]],
            on=["permno", "ym_ccm"],
            how="inner",
        )
    if "be" not in ccm_jun.columns:
        raise ValueError("ccm_linked_funda merge is missing 'be' after alignment")
    ccm_jun["be"] = pd.to_numeric(ccm_jun["be"], errors="coerce")
    ccm_jun = ccm_jun[ccm_jun["be"].gt(0)]
    # Exclude financials
    if "sic" in ccm_jun.columns:
        ccm_jun = ccm_jun[~((ccm_jun["sic"] >= 6000) & (ccm_jun["sic"] <= 6999))]

    # Compute BE/ME using December ME denominator (dec_me in thousands consistent with BE * 1000)
    if "be" not in ccm_jun.columns:
        raise ValueError("ccm_linked_funda missing 'be' column")
    ccm_jun["beme"] = (ccm_jun["be"] * 1000.0) / ccm_jun["dec_me"]
    ccm_jun.replace([np.inf, -np.inf], np.nan, inplace=True)
    ccm_jun = ccm_jun.dropna(subset=["beme"])  # enforce positive defined BE/ME later

    # NYSE breakpoints
    sz_bp = nyse_size_median(
        ccm_jun.rename(columns={"jdate": "jdate"}),
        date_col="jdate", exch_col="primaryexch", me_col="me",
    )
    bm_bp = nyse_quantiles(
        ccm_jun,
        value_col="beme", date_col="jdate", exch_col="primaryexch",
        sample_filter=(ccm_jun["beme"] > 0) & (ccm_jun["dec_me"] > 0),
    ).rename(columns={"beme30": "bm30", "beme70": "bm70"})

    # currat breakpoints (optional; callers may not need them)
    cr_bp = None
    if "currat" in ccm_jun.columns:
        cr_bp = nyse_quantiles(
            ccm_jun,
            value_col="currat", date_col="jdate", exch_col="primaryexch",
            sample_filter=(ccm_jun["dec_me"] > 0) & (ccm_jun["currat"].notna()),
        ).rename(columns={"currat30": "cr30", "currat70": "cr70"})

    # Attach breakpoints to June snapshot
    june = ccm_jun.merge(sz_bp, on="jdate", how="left").merge(bm_bp, on="jdate", how="left")
    if cr_bp is not None:
        june = june.merge(cr_bp, on="jdate", how="left")

    # Assign size and BM portfolios for June (validity mask for HML computation)
    june_hml = assign_2x3(
        june,
        date_col="jdate",
        size_col="me",
        char_col="beme",
        size_bp_col="sizemedn",
        char_q30_col="bm30",
        char_q70_col="bm70",
        out_size="szport",
        out_char="bmport",
        valid_mask=(june["beme"].gt(0) & june["me"].gt(0) & june["dec_me"].gt(0)),
    )

    # Optionally, assign current ratio buckets for June if present
    if {"currat", "cr30", "cr70"}.issubset(set(june_hml.columns)):
        june_hml = assign_2x3(
            june_hml,
            date_col="jdate",
            size_col="me",
            char_col="currat",
            size_bp_col="sizemedn",
            char_q30_col="cr30",
            char_q70_col="cr70",
            out_size="szport",  # reuse
            out_char="crport",
            valid_mask=(june_hml["me"].gt(0) & june_hml["dec_me"].gt(0) & june_hml["currat"].notna()),
        )

    # Bring June labels into the monthly panel for VW returns
    crsp_monthly = crsp3[[
        "mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"
    ]].copy()
    june_labels = june_hml[["permno", "jdate", "szport", "bmport"]].copy()
    june_labels["ffyear"] = june_labels["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(
        june_labels.drop(columns=["jdate"]),
        on=["permno", "ffyear"], how="left",
    )
    # If currat assignments exist, merge them too (ffyear keyed)
    if "crport" in june_hml.columns:
        june_cr = june_hml[["permno", "jdate", "crport"]].copy()
        june_cr["ffyear"] = june_cr["jdate"].dt.year
        monthly_labeled = monthly_labeled.merge(
            june_cr.drop(columns=["jdate"]),
            on=["permno", "ffyear"], how="left",
        )

    out = Prepared(
        month_index=month_index[(month_index >= s) & (month_index <= e)],
        ccm_monthly_with_ports=monthly_labeled,
        june_assignments=june_hml,
    )
    return out
