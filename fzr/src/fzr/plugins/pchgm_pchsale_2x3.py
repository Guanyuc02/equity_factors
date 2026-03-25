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
    """Abarbanell–Bushee ΔGM − ΔSales (pchgm_pchsale) factor via 2×3 sorts.

    Characteristic:
        gross_margin = sale − cogs
        pctchg_gm = gross_margin_t / gross_margin_{t−1} − 1
        pctchg_sale = sale_t / sale_{t−1} − 1
        pchgm_pchsale = pctchg_gm − pctchg_sale

    Construction:
        - Compute pct changes per permno using CCM-linked funda aligned to each June.
        - Filter to positive BE, non-financials.
        - Size breakpoints: NYSE median; char breakpoints: NYSE 30/70 quantiles.
        - Factor = WH − WL (high improvement in GM relative to sales minus low).
    """
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=25)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)]
    crsp3, crsp_jun, month_index = _prep_crsp(cm)

    a = funda.copy()
    if "jdate_ltrd" in a.columns:
        a["jdate"] = pd.to_datetime(a["jdate_ltrd"], errors="coerce")
    elif "jdate" in a.columns:
        a["jdate"] = pd.to_datetime(a["jdate"], errors="coerce")
    else:
        raise ValueError("ccm_linked_funda is missing jdate/jdate_ltrd field")
    a["datadate"] = pd.to_datetime(a["datadate"], errors="coerce")
    if "ym" in a.columns:
        a["ym"] = pd.to_datetime(a["ym"], errors="coerce").dt.to_period("M")
    else:
        a["ym"] = a["jdate"].dt.to_period("M")

    required_cols = {"sale", "cogs"}
    missing = sorted(required_cols - set(a.columns))
    if missing:
        raise ValueError(f"ccm_linked_funda missing required columns for pchgm_pchsale: {missing}")

    sort_cols = ["permno", "ym"]
    if "datadate" in a.columns:
        sort_cols.append("datadate")
    a = (
        a.sort_values(sort_cols)
         .dropna(subset=["permno", "ym"])
         .drop_duplicates(subset=["permno", "ym"], keep="last")
         .copy()
    )
    for col in ("sale", "cogs"):
        a[col] = pd.to_numeric(a[col], errors="coerce")

    a["gross_margin"] = a["sale"] - a["cogs"]
    a["gm_lag1"] = a.groupby("permno", group_keys=False)["gross_margin"].shift(1)
    a["sale_lag1"] = a.groupby("permno", group_keys=False)["sale"].shift(1)
    # Guard against zero / near-zero denominators when forming percentage changes.
    eps = 1e-6
    gm_denom = a["gm_lag1"].where(a["gm_lag1"].abs() > eps)
    sale_denom = a["sale_lag1"].where(a["sale_lag1"].abs() > eps)
    with np.errstate(divide="ignore", invalid="ignore"):
        a["pctchg_gm"] = a["gross_margin"] / gm_denom - 1.0
        a["pctchg_sale"] = a["sale"] / sale_denom - 1.0
    a["pchgm_pchsale"] = a["pctchg_gm"] - a["pctchg_sale"]
    a.replace([np.inf, -np.inf], np.nan, inplace=True)

    jun = crsp_jun.copy()
    jun["ym"] = jun["ym"].astype("period[M]")
    june = jun.merge(
        a.rename(columns={"ym": "ym_a"}),
        left_on=["permno", "ym"],
        right_on=["permno", "ym_a"],
        how="inner",
        suffixes=("", "_a"),
    )

    be_mask = positive_book_equity_mask(
        funda,
        start=s,
        end=e,
        warm_months=25,
    )[["permno", "ym"]]
    june = june.merge(be_mask, on=["permno", "ym"], how="inner")

    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    if "primaryexch" not in june.columns and "exchcd" in june.columns:
        june = june.copy()
        june["primaryexch"] = june["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    sz_bp = nyse_size_median(
        june,
        date_col="jdate",
        exch_col="primaryexch",
        me_col="me",
    )

    base_filter = june["me"].gt(0) & june["pchgm_pchsale"].notna()
    # Primary: NYSE 30/70 breakpoints
    gm_bp_nyse = nyse_quantiles(
        june,
        value_col="pchgm_pchsale",
        date_col="jdate",
        exch_col="primaryexch",
        sample_filter=base_filter,
    )
    # Fallback: if a given date has no NYSE names after BE/character screens,
    # compute breakpoints using the full (all-exchange) sample.
    june_all = june.copy()
    june_all["__all_exch__"] = "N"
    gm_bp_all = nyse_quantiles(
        june_all,
        value_col="pchgm_pchsale",
        date_col="jdate",
        exch_col="__all_exch__",
        sample_filter=base_filter,
    )
    gm_bp = gm_bp_all.merge(
        gm_bp_nyse,
        on="jdate",
        how="left",
        suffixes=("_all", "_nyse"),
    )
    gm_bp["pchgm_pchsale30"] = gm_bp["pchgm_pchsale30_nyse"].fillna(
        gm_bp["pchgm_pchsale30_all"]
    )
    gm_bp["pchgm_pchsale70"] = gm_bp["pchgm_pchsale70_nyse"].fillna(
        gm_bp["pchgm_pchsale70_all"]
    )
    gm_bp = gm_bp[["jdate", "pchgm_pchsale30", "pchgm_pchsale70"]]

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(gm_bp, on="jdate", how="left")

    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="pchgm_pchsale",
        size_bp_col="sizemedn",
        char_q30_col="pchgm_pchsale30",
        char_q70_col="pchgm_pchsale70",
        out_size="szport",
        out_char="gmport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["pchgm_pchsale"].notna()),
    )

    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "gmport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    d = monthly_labeled[
        (monthly_labeled["wt"] > 0)
        & monthly_labeled[["szport", "gmport"]].ne("").all(axis=1)
    ]
    wide = value_weighted_returns(
        d,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="gmport",
    )

    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                pchgm_pchsale=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
            )[["jdate", "pchgm_pchsale"]]
            .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )
    return factor
