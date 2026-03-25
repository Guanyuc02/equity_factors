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
    """Ou–Penman cash-flow-to-debt factor from 2×3 sorts (size × cashdebt).

    Characteristic:
    cashdebt = (TTM₄(IBQ) + TTM₄(DPQ)) / ((LTQ + LTQ_{t-4}) / 2)
      - Numerator: trailing 4-quarter sum of income before extraordinary items plus depreciation.
      - Denominator: average of current and 4-quarters-prior total liabilities.

    Alignment:
    - Use CCM-linked Compustat quarterly fundamentals (fundq) aligned as-of each CRSP month.
    - NYSE breakpoints on size median and cashdebt 30/70 quantiles.
    - Factor = WH − WL (high cashdebt minus low cashdebt).

    Returns DataFrame with columns: date, cashdebt
    """
    crsp_m = ctx.base.get("crsp_monthly")
    fundq = ctx.base.get("ccm_linked_fundq")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or fundq is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly', 'ccm_linked_fundq', and 'ccm_linked_funda'")

    # Restrict window with warm-up to ensure valid June assignments
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=13)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)]

    # CRSP mechanics and month index
    crsp3, crsp_jun, month_index = _prep_crsp(cm)

    # Prepare Compustat quarterly anchors (as-of alignment via CCM linked fundq)
    q = fundq.copy()
    if "jdate_ltrd" in q.columns:
        q["jdate"] = pd.to_datetime(q["jdate_ltrd"], errors="coerce")
    elif "jdate" in q.columns:
        q["jdate"] = pd.to_datetime(q["jdate"], errors="coerce")
    else:
        raise ValueError("ccm_linked_fundq is missing jdate/jdate_ltrd field")
    q["rdq"] = pd.to_datetime(q["rdq"], errors="coerce")
    q["datadate"] = pd.to_datetime(q["datadate"], errors="coerce")
    if "ym" in q.columns:
        q["ym"] = pd.to_datetime(q["ym"], errors="coerce").dt.to_period("M")

    required_cols = {"ltq", "ibq", "dpq"}
    missing = sorted(required_cols - set(q.columns))
    if missing:
        raise ValueError(f"ccm_linked_fundq missing required columns for cashdebt: {missing}")

    # Compute trailing-four-quarter numerators and LTQ lag on unique quarter observations
    quarter_obs = (
        q.dropna(subset=["datadate"])
         .sort_values(["permno", "datadate", "rdq"])
         .drop_duplicates(subset=["permno", "datadate"], keep="last")
         .copy()
    )
    for col in ("ltq", "ibq", "dpq"):
        quarter_obs[col] = pd.to_numeric(quarter_obs[col], errors="coerce")

    rolling_ibq = (
        quarter_obs.groupby("permno", group_keys=False)["ibq"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    rolling_dpq = (
        quarter_obs.groupby("permno", group_keys=False)["dpq"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    quarter_obs["ttm_ibq"] = rolling_ibq
    quarter_obs["ttm_dpq"] = rolling_dpq
    quarter_obs["ltq_l4"] = (
        quarter_obs.groupby("permno", group_keys=False)["ltq"]
        .shift(4)
    )

    q = q.merge(
        quarter_obs[["permno", "datadate", "ttm_ibq", "ttm_dpq", "ltq_l4"]],
        on=["permno", "datadate"],
        how="left",
    )

    # Merge Compustat June anchors to CRSP June snapshot via month key
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

    # Exclude financials if SIC available
    if "sic" not in june.columns and "sic_be" in june.columns:
        june = june.rename(columns={"sic_be": "sic"})
    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    # Compute cashdebt characteristic
    for col in ("ltq", "ibq", "dpq", "ttm_ibq", "ttm_dpq", "ltq_l4"):
        if col in june.columns:
            june[col] = pd.to_numeric(june[col], errors="coerce")
    num = june["ttm_ibq"] + june["ttm_dpq"]
    denom = (june["ltq"] + june["ltq_l4"]) / 2.0
    # Ensure numerical division uses NumPy float dtype to avoid pandas nullable Float64
    # assigning into a float64 column (FutureWarning in recent pandas).
    valid = denom.notna() & (denom != 0.0)
    june["cashdebt"] = np.nan
    # Cast operands to float64 and assign NumPy array to keep dtype consistent.
    ratio = (num.loc[valid].astype("float64") / denom.loc[valid].astype("float64")).to_numpy()
    june.loc[valid, "cashdebt"] = ratio
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    # NYSE breakpoints on size median and cashdebt 30/70
    sz_bp = nyse_size_median(june, date_col="jdate", exch_col="primaryexch", me_col="me")
    cd_bp = nyse_quantiles(
        june,
        value_col="cashdebt", date_col="jdate", exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june["cashdebt"].notna()),
    ).rename(columns={"cashdebt30": "cashdebt30", "cashdebt70": "cashdebt70"})

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(cd_bp, on="jdate", how="left")

    # Assign 2×3 portfolios: size (S/B) × cashdebt (L/M/H)
    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="cashdebt",
        size_bp_col="sizemedn",
        char_q30_col="cashdebt30",
        char_q70_col="cashdebt70",
        out_size="szport",
        out_char="cdport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["cashdebt"].notna()),
    )

    # Bring June labels into the monthly panel for VW returns
    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "cdport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    d = monthly_labeled[(monthly_labeled["wt"] > 0) & monthly_labeled[["szport", "cdport"]].ne("").all(axis=1)]
    wide = value_weighted_returns(
        d,
        date_col="jdate", ret_col="mthret", weight_col="wt",
        size_bucket_col="szport", char_bucket_col="cdport",
    )
    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                cashdebt=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
            )[["jdate", "cashdebt"]]
            .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )
    return factor
