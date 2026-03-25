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
    """Leverage factor from 2×3 sorts (size × lev), where lev = ltq / me at June.

    Alignment:
    - Pull Compustat quarterly ltq and rdq, link to CRSP via CCM.
    - As-of alignment uses rdq: for each June, take the latest quarterly record with rdq ≤ CRSP June jdate.
    - Scale ltq to match CRSP ME units (CRSP shrout is in thousands) by multiplying ltq by 1,000 if Compustat units are in millions.

    Returns DataFrame with columns: date, lev
    """
    crsp_m = ctx.base.get("crsp_monthly")
    fundq = ctx.base.get("ccm_linked_fundq")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or fundq is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly', 'ccm_linked_fundq', and 'ccm_linked_funda'")

    # Restrict window with warm-up to ensure valid June assignments
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=13)

    crsp_m = crsp_m.copy()
    crsp_m["mthcaldt"] = pd.to_datetime(crsp_m["mthcaldt"])  # ensure dtype
    crsp_m = crsp_m[(crsp_m["mthcaldt"] >= s_warm) & (crsp_m["mthcaldt"] <= e)]

    # CRSP mechanics and month index
    crsp3, crsp_jun, month_index = _prep_crsp(crsp_m)

    # Prepare Compustat quarterly as-of snapshots keyed by CRSP month key
    q = fundq.copy()
    # Standardize rdq/jdate types
    if "jdate_ltrd" in q.columns:
        q["jdate"] = pd.to_datetime(q["jdate_ltrd"])  # keep original
    elif "jdate" in q.columns:
        q["jdate"] = pd.to_datetime(q["jdate"])  # fallback
    else:
        raise ValueError("ccm_linked_fundq is missing jdate/jdate_ltrd field")
    q["rdq"] = pd.to_datetime(q["rdq"], errors="coerce")
    # Normalize month key dtype to match CRSP Period[M]
    if "ym" in q.columns:
        q["ym"] = pd.to_datetime(q["ym"], errors="coerce").dt.to_period("M")

    # Merge June CRSP rows to as-of quarterly anchors via month key
    jun = crsp_jun.copy()
    jun["ym"] = jun["ym"].astype("period[M]")
    june = jun.merge(
        q.rename(columns={"ym": "ym_q"}),
        left_on=["permno", "ym"], right_on=["permno", "ym_q"], how="inner",
        suffixes=("", "_q"),
    )
    be_mask = positive_book_equity_mask(
        funda,
        start=s,
        end=e,
        warm_months=13,
    )
    mask_cols = ["permno", "ym"]
    if "sic" in be_mask.columns and "sic" not in june.columns:
        mask_cols.append("sic")
    june = june.merge(
        be_mask[mask_cols],
        on=["permno", "ym"],
        how="inner",
        suffixes=("", "_be"),
    )

    # Exclude financials if sic is available
    if "sic" not in june.columns and "sic_be" in june.columns:
        june = june.rename(columns={"sic_be": "sic"})
    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    # Compute leverage characteristic at June using CRSP June ME
    # - ltq is typically in millions in Compustat; scale by 1,000 to match CRSP ME (thousands)
    # - ensure positivity of ME for sensible ratios
    if "ltq" not in june.columns:
        raise ValueError("ccm_linked_fundq missing 'ltq' column")
    june["ltq_scaled"] = pd.to_numeric(june["ltq"], errors="coerce") * 1000.0
    june["lev"] = june["ltq_scaled"] / june["me"]
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    # NYSE breakpoints on size median and lev 30/70 quantiles
    sz_bp = nyse_size_median(june, date_col="jdate", exch_col="primaryexch", me_col="me")
    lev_bp = nyse_quantiles(
        june,
        value_col="lev", date_col="jdate", exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june["lev"].notna()),
    ).rename(columns={"lev30": "lev30", "lev70": "lev70"})

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(lev_bp, on="jdate", how="left")

    # Assign 2×3 portfolios: size (S/B) × leverage (L/M/H)
    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="lev",
        size_bp_col="sizemedn",
        char_q30_col="lev30",
        char_q70_col="lev70",
        out_size="szport",
        out_char="levport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["lev"].notna()),
    )

    # Bring June labels into the monthly panel for VW returns
    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "levport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    # Compute value-weighted returns across 2×3 buckets and assemble factor series
    d = monthly_labeled[(monthly_labeled["wt"] > 0) & monthly_labeled[["szport", "levport"]].ne("").all(axis=1)]
    wide = value_weighted_returns(
        d,
        date_col="jdate", ret_col="mthret", weight_col="wt",
        size_bucket_col="szport", char_bucket_col="levport",
    )
    lev = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                lev=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),  # High minus Low leverage
            )[["jdate", "lev"]]
            .rename(columns={"jdate": "date"})
    )

    lev = (
        lev.set_index("date")
           .reindex(month_index[(month_index >= s) & (month_index <= e)])
           .rename_axis("date")
           .reset_index()
    )
    return lev
