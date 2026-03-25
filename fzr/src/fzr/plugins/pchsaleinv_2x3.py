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
    """Percent change in sales-to-inventory ratio (pchsaleinv) from 2×3 sorts.

    Characteristic (Ou–Penman):
        saleinv = sale / invt
        pchsaleinv = (saleinv_t − saleinv_{t−1}) / saleinv_{t−1}
                   = saleinv_t / saleinv_{t−1} − 1

    Construction notes:
    - Use CCM-linked Compustat annual fundamentals aligned to each CRSP June.
    - Compute saleinv and its lag at the Compustat anchor level to avoid gaps from CRSP coverage.
    - NYSE breakpoints on size (median) and pchsaleinv (30/70 quantiles).
    - Factor sign follows currat/pchcurrat convention: WL − WH.
    """
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    # Need two June anchors => include ~24 months of history (mirror pchcurrat/pchquick)
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

    required_cols = {"sale", "invt"}
    missing = sorted(required_cols - set(a.columns))
    if missing:
        raise ValueError(f"ccm_linked_funda missing required columns for pchsaleinv: {missing}")

    a = (
        a.sort_values(["permno", "ym", "datadate"])
         .drop_duplicates(subset=["permno", "ym"], keep="last")
         .copy()
    )
    for col in ("sale", "invt"):
        a[col] = pd.to_numeric(a[col], errors="coerce")

    a["saleinv"] = np.nan
    denom = a["invt"].astype("float64")
    num = a["sale"].astype("float64")
    valid = denom.notna() & (denom != 0.0)
    a.loc[valid, "saleinv"] = (num.loc[valid] / denom.loc[valid]).to_numpy()

    a["saleinv_lag1"] = a.groupby("permno", group_keys=False)["saleinv"].shift(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        a["pchsaleinv"] = a["saleinv"] / a["saleinv_lag1"] - 1.0
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

    sz_bp = nyse_size_median(june, date_col="jdate", exch_col="primaryexch", me_col="me")
    si_bp = nyse_quantiles(
        june,
        value_col="pchsaleinv",
        date_col="jdate",
        exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june["pchsaleinv"].notna()),
    )
    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(si_bp, on="jdate", how="left")

    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="pchsaleinv",
        size_bp_col="sizemedn",
        char_q30_col="pchsaleinv30",
        char_q70_col="pchsaleinv70",
        out_size="szport",
        out_char="siport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["pchsaleinv"].notna()),
    )

    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "siport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    d = monthly_labeled[(monthly_labeled["wt"] > 0) & monthly_labeled[["szport", "siport"]].ne("").all(axis=1)]
    wide = value_weighted_returns(
        d,
        date_col="jdate",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="siport",
    )

    factor = (
        wide[["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]]
        .assign(
            WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
            WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
            pchsaleinv=lambda x: apply_orientation(x["WH"], x["WL"], "low_minus_high"),
        )[["jdate", "pchsaleinv"]]
            .rename(columns={"jdate": "date"})
    )

    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )
    return factor
