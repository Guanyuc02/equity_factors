from __future__ import annotations

from typing import Iterable, Optional, Tuple

import numpy as np
import pandas as pd

from ..factors_core import (
    FactorContext,
    FactorOrientation,
    apply_orientation,
    assign_2x3,
    nyse_quantiles,
    nyse_size_median,
    value_weighted_returns,
)
from .ff_shared import _prep_crsp, positive_book_equity_mask


def _prep_june_funda(
    ctx: FactorContext,
    *,
    start: str,
    end: str,
    required_cols: Iterable[str],
    warm_months: int = 25,
    require_be: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=warm_months)

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
    a["datadate"] = pd.to_datetime(a.get("datadate"), errors="coerce")
    if "ym" in a.columns:
        a["ym"] = pd.to_datetime(a["ym"], errors="coerce").dt.to_period("M")
    else:
        a["ym"] = a["jdate"].dt.to_period("M")

    missing = sorted(set(required_cols) - set(a.columns))
    if missing:
        raise ValueError(f"ccm_linked_funda missing required columns: {missing}")

    sort_cols = ["permno", "ym", "datadate"]
    a = (
        a.sort_values(sort_cols)
         .dropna(subset=["permno", "ym"])
         .drop_duplicates(subset=["permno", "ym"], keep="last")
         .copy()
    )
    for col in required_cols:
        a[col] = pd.to_numeric(a[col], errors="coerce")
    if "sic" in a.columns:
        a["sic"] = pd.to_numeric(a["sic"], errors="coerce").astype("Int64")
        a["sic2"] = (a["sic"] // 100).astype("Int64")

    jun = crsp_jun.copy()
    jun["ym"] = jun["ym"].astype("period[M]")
    june = jun.merge(
        a.rename(columns={"ym": "ym_a"}),
        left_on=["permno", "ym"],
        right_on=["permno", "ym_a"],
        how="inner",
        suffixes=("", "_a"),
    )

    if require_be:
        be_mask = positive_book_equity_mask(
            funda,
            start=s,
            end=e,
            warm_months=warm_months,
        )[["permno", "ym"]]
        june = june.merge(be_mask, on=["permno", "ym"], how="inner")

    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    if "primaryexch" not in june.columns and "exchcd" in june.columns:
        june = june.copy()
        june["primaryexch"] = june["exchcd"].map({1: "N", 2: "A", 3: "Q"})

    return june, crsp3, month_index[(month_index >= s) & (month_index <= e)]


def _industry_adjust(df: pd.DataFrame, value_col: str, *, sic_col: str = "sic2") -> pd.Series:
    if sic_col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    med = df.groupby(["jdate", sic_col])[value_col].transform("median")
    return df[value_col] - med


def build_2x3_factor(
    june: pd.DataFrame,
    crsp3: pd.DataFrame,
    month_index: pd.Series,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    char_col: str,
    factor_name: str,
    orientation: FactorOrientation = "high_minus_low",
) -> pd.DataFrame:
    if char_col not in june.columns:
        return pd.DataFrame({"date": month_index, factor_name: np.nan})

    sz_bp = nyse_size_median(june, date_col="jdate", exch_col="primaryexch", me_col="me")
    char_bp = nyse_quantiles(
        june,
        value_col=char_col,
        date_col="jdate",
        exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june[char_col].notna()),
    )

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(char_bp, on="jdate", how="left")
    char_q30 = f"{char_col}30"
    char_q70 = f"{char_col}70"
    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col=char_col,
        size_bp_col="sizemedn",
        char_q30_col=char_q30,
        char_q70_col=char_q70,
        out_size="szport",
        out_char=f"{char_col}_port",
        valid_mask=(june_bp["me"].gt(0) & june_bp[char_col].notna()),
    )

    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", f"{char_col}_port"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    mask = (
        (monthly_labeled["wt"] > 0)
        & monthly_labeled["szport"].notna()
        & monthly_labeled[f"{char_col}_port"].notna()
    )
    d = monthly_labeled[mask]
    wide = value_weighted_returns(
        d,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col=f"{char_col}_port",
    )

    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
        .assign(
            WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
            WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
        )
        .assign(
            **{
                factor_name: lambda x: apply_orientation(x["WH"], x["WL"], orientation)
            }
        )[["jdate", factor_name]]
        .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
        .reindex(month_index[(month_index >= start) & (month_index <= end)])
        .rename_axis("date")
        .reset_index()
    )
    return factor
