from __future__ import annotations
import numpy as np
import pandas as pd

from ..factors_core import (
    FactorContext,
    apply_orientation,
    nyse_size_median,
    value_weighted_returns,
)
from .ff_shared import _prep_crsp, positive_book_equity_mask


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("Need crsp_monthly and ccm_linked_funda")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    warm = s - pd.offsets.DateOffset(months=25)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"])
    cm = cm[(cm["mthcaldt"] >= warm) & (cm["mthcaldt"] <= e)]
    crsp3, crsp_jun, month_index = _prep_crsp(cm)

    a = funda.copy()
    a["datadate"] = pd.to_datetime(a["datadate"])
    a["jdate_ltrd"] = pd.to_datetime(a["jdate_ltrd"])
    a["ym"] = a["jdate_ltrd"].dt.to_period("M")

    a["dcvt"] = pd.to_numeric(a.get("dcvt"), errors="coerce")
    a["convind_char"] = np.where(a["dcvt"].fillna(0) > 0, 1.0, 0.0)

    a = (
        a.sort_values(["permno", "ym", "datadate"])
         .drop_duplicates(subset=["permno", "ym"], keep="last")
         .copy()
    )

    jun = crsp_jun.copy()
    jun["ym"] = jun["ym"].astype("period[M]")

    june = jun.merge(a, on=["permno", "ym"], how="inner")

    be_mask = positive_book_equity_mask(
        funda, start=s, end=e, warm_months=25
    )[["permno", "ym"]]
    june = june.merge(be_mask, on=["permno", "ym"], how="inner")

    if "sic" in june.columns:
        june = june[~june["sic"].between(6000, 6999)]

    if "primaryexch" not in june.columns and "exchcd" in june.columns:
        june["primaryexch"] = june["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    sz_bp = nyse_size_median(
        june,
        date_col="jdate",
        exch_col="primaryexch",
        me_col="me",
    )

    june_bp = june.merge(sz_bp, on="jdate")

    june_ports = june_bp.copy()
    valid = june_ports["me"].gt(0) & june_ports["convind_char"].notna()

    # Size buckets: S/B via NYSE median size.
    june_ports["szport"] = ""
    msz = valid & june_ports[["me", "sizemedn"]].notna().all(axis=1)
    june_ports.loc[msz, "szport"] = np.where(
        june_ports.loc[msz, "me"] <= june_ports.loc[msz, "sizemedn"],
        "S",
        "B",
    )

    # Binary characteristic: treat convind_char == 1 as High, 0 as Low.
    june_ports["cvport"] = ""
    mch = valid & june_ports["convind_char"].notna()
    june_ports.loc[mch, "cvport"] = np.where(
        june_ports.loc[mch, "convind_char"] >= 0.5,
        "H",
        "L",
    )

    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()

    lab = june_ports[["permno", "jdate", "szport", "cvport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year

    monthly = crsp_monthly.merge(
        lab.drop(columns=["jdate"]),
        on=["permno", "ffyear"],
        how="left",
    )

    d = monthly[
        (monthly["wt"] > 0)
        & monthly[["szport", "cvport"]].ne("").all(axis=1)
    ]

    wide = value_weighted_returns(
        d,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="cvport",
    )

    factor_wide = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
        .assign(
            WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
            WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
        )
    )
    # When there are no High-convertible firms in a given year
    # but Low buckets are populated, treat the spread as zero
    # rather than leaving the factor missing.
    factor_wide["convind"] = apply_orientation(factor_wide["WH"], factor_wide["WL"], "low_minus_high")
    no_high_mask = factor_wide["WH"].isna() & factor_wide["WL"].notna()
    factor_wide.loc[no_high_mask, "convind"] = 0.0

    factor = factor_wide[["jdate", "convind"]].rename(columns={"jdate": "date"})

    factor["date"] = pd.to_datetime(factor["date"])

    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )

    return factor
