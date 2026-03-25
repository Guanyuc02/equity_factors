from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import (
    FactorContext,
    apply_orientation,
    nyse_size_median,
    nyse_quantiles,
    assign_2x3,
    value_weighted_returns,
)
from .ff_shared import _prep_crsp, positive_book_equity_mask


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """Miller–Scholes share price factor (pps) time series from 2×3 sorts.

    Construction:
    - Characteristic: invprc = 1 / |price| using the contemporaneous June price.
    - Exclude penny stocks at formation: |price| < $1 at the June sort date.
    - 2×3 portfolios using NYSE breakpoints: size (median) × invprc (30/70).
    - Factor = WH − WL, where high invprc corresponds to low price.

    Returns DataFrame with columns: date, pps
    """
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")

    # Restrict window with warm-up (ensure valid June assignments)
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=13)

    cm = crsp_m.copy()
    if "mthcaldt" not in cm.columns:
        raise ValueError("crsp_monthly missing 'mthcaldt' column")
    if "mthprc" not in cm.columns:
        raise ValueError("crsp_monthly missing 'mthprc' column")
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)].copy()

    # CRSP prep: weights, FF calendar, June snapshot, month index
    crsp3, crsp_jun, month_index = _prep_crsp(cm)
    crsp_jun = crsp_jun.copy()
    crsp_jun["ym"] = crsp_jun["ym"].astype("period[M]")

    be_mask = positive_book_equity_mask(
        funda,
        start=s,
        end=e,
        warm_months=13,
    )

    # Bring June exchange codes for NYSE breakpoint checks
    cm_jun = cm.copy()
    cm_jun["month"] = cm_jun["mthcaldt"].dt.month
    cm_jun = cm_jun[cm_jun["month"] == 6][["permno", "mthcaldt", "mthprc", "primaryexch"]].rename(
        columns={"mthcaldt": "jdate"}
    )
    june = crsp_jun[["permno", "jdate", "me", "year", "ym"]].merge(
        cm_jun, on=["permno", "jdate"], how="inner"
    )
    june = june.merge(
        be_mask,
        on=["permno", "ym"],
        how="inner",
        suffixes=("", "_be"),
    )
    if "sic" not in june.columns and "sic_be" in june.columns:
        june = june.rename(columns={"sic_be": "sic"})
    if "sic_be" in june.columns:
        june = june.drop(columns=["sic_be"])
    if "sic" in june.columns:
        june = june[~((june["sic"] >= 6000) & (june["sic"] <= 6999))]

    # Universe: keep penny-filtered contemporaneous June prices
    june["prc_abs"] = pd.to_numeric(june["mthprc"], errors="coerce").abs()
    june = june[june["prc_abs"] >= 1.0]
    june["invprc"] = 1.0 / june["prc_abs"]
    june.replace([np.inf, -np.inf], np.nan, inplace=True)
    june = june.dropna(subset=["invprc", "me"])  # ensure valid char and size

    # NYSE breakpoints
    sz_bp = nyse_size_median(june, date_col="jdate", exch_col="primaryexch", me_col="me")
    pr_bp = nyse_quantiles(
        june,
        value_col="invprc", date_col="jdate", exch_col="primaryexch",
        sample_filter=(june["me"].gt(0) & june["invprc"].notna()),
    ).rename(columns={"invprc30": "invprc30", "invprc70": "invprc70"})

    june_bp = june.merge(sz_bp, on="jdate", how="left").merge(pr_bp, on="jdate", how="left")

    # Assign 2×3 portfolios
    june_ports = assign_2x3(
        june_bp,
        date_col="jdate",
        size_col="me",
        char_col="invprc",
        size_bp_col="sizemedn",
        char_q30_col="invprc30",
        char_q70_col="invprc70",
        out_size="szport",
        out_char="prcport",
        valid_mask=(june_bp["me"].gt(0) & june_bp["invprc"].notna()),
    )

    # Bring June labels into monthly panel and compute VW returns
    crsp_monthly = crsp3[["mthcaldt", "permno", "mthret", "wt", "ffyear", "jdate"]].copy()
    lab = june_ports[["permno", "jdate", "szport", "prcport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year
    monthly_labeled = crsp_monthly.merge(lab.drop(columns=["jdate"]), on=["permno", "ffyear"], how="left")

    mask = (
        (monthly_labeled["wt"] > 0)
        & monthly_labeled["szport"].notna()
        & monthly_labeled["prcport"].notna()
    )
    d = monthly_labeled[mask]
    wide = value_weighted_returns(
        d,
        date_col="mthcaldt",  # group by calendar month
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="prcport",
    )

    # WH - WL where high invprc = low price
    factor = (
        wide[["mthcaldt", "SL", "SM", "SH", "BL", "BM", "BH"]]
            .assign(
                WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
                WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
                pps=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
            )[["mthcaldt", "pps"]]
            .rename(columns={"mthcaldt": "date"})
    )
    factor = (
        factor.set_index("date")
              .reindex(month_index[(month_index >= s) & (month_index <= e)])
              .rename_axis("date")
              .reset_index()
    )
    return factor
