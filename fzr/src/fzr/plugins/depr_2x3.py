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
    """Depreciation-to-PP&E (depr) factor from 2×3 sorts (size × depr).

    Characteristic:
        depr = TTM₄(DPQ) / PPENTQ computed from CCM-linked Compustat quarterly data
        aligned to each CRSP June formation date.

    Construction:
        - Filter to firms with positive book equity and non-financial SIC codes.
        - Size breakpoints: NYSE median; characteristic breakpoints: NYSE 30/70 quantiles.
        - Portfolios: size (S/B) × depr (L/M/H).
        - Factor = WH − WL (high depreciation intensity minus low) using value-weighted returns.
    """
    crsp_m = ctx.base.get("crsp_monthly")
    fundq = ctx.base.get("ccm_linked_fundq")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or fundq is None or funda is None:
        raise ValueError(
            "FactorContext.base must include 'crsp_monthly', 'ccm_linked_fundq', and 'ccm_linked_funda'"
        )

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=13)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)]

    crsp3, crsp_jun, month_index = _prep_crsp(cm)

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

    required_cols = {"dpq", "ppentq"}
    missing = sorted(required_cols - set(q.columns))
    if missing:
        raise ValueError(f"ccm_linked_fundq missing required columns for depr: {missing}")

    quarter_obs = (
        q.dropna(subset=["datadate"])
         .sort_values(["permno", "datadate", "rdq"])
         .drop_duplicates(subset=["permno", "datadate"], keep="last")
         .copy()
    )
    for col in ("dpq", "ppentq"):
        quarter_obs[col] = pd.to_numeric(quarter_obs[col], errors="coerce")
    rolling_dpq = (
        quarter_obs.groupby("permno", group_keys=False)["dpq"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    quarter_obs["ttm_dpq"] = rolling_dpq

    q = q.merge(
        quarter_obs[["permno", "datadate", "ttm_dpq"]],
        on=["permno", "datadate"],
        how="left",
    )

    jun = crsp_jun.copy()
    jun["ym"] = jun["ym"].astype("period[M]")
    june = jun.merge(
        q.rename(columns={"ym": "ym_q"}),
        left_on=["permno", "ym"],
        right_on=["permno", "ym_q"],
        how="inner",
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

    if "sic" not in june.columns and "sic_be" in june.columns:
        june = june.rename(columns={"sic_be": "sic"})
    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    if "primaryexch" not in june.columns and "exchcd" in june.columns:
        june = june.copy()
        june["primaryexch"] = june["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    for col in ("ttm_dpq", "ppentq"):
        if col in june.columns:
            june[col] = pd.to_numeric(june[col], errors="coerce")
    june["depr"] = np.nan
    num = june["ttm_dpq"]
    denom = june["ppentq"]
    valid = num.notna() & denom.notna() & denom.ne(0.0)
    ratio = (num.loc[valid].astype("float64") / denom.loc[valid].astype("float64")).to_numpy()
    june.loc[valid, "depr"] = ratio
    june.replace([np.inf, -np.inf], np.nan, inplace=True)

    sz_bp = nyse_size_median(
        june,
        date_col="jdate",
        exch_col="primaryexch",
        me_col="me",
    )
    depr_bp = nyse_quantiles(
        june,
        value_col="depr",
        date_col="jdate",
        exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june["depr"].notna()),
    ).rename(columns={"depr30": "depr30", "depr70": "depr70"})

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(depr_bp, on="jdate", how="left")

    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="depr",
        size_bp_col="sizemedn",
        char_q30_col="depr30",
        char_q70_col="depr70",
        out_size="szport",
        out_char="deprport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["depr"].notna()),
    )

    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "deprport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    d = monthly_labeled[
        (monthly_labeled["wt"] > 0)
        & monthly_labeled[["szport", "deprport"]].ne("").all(axis=1)
    ]
    wide = value_weighted_returns(
        d,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="deprport",
    )

    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                depr=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
            )[["jdate", "depr"]]
            .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )
    return factor
