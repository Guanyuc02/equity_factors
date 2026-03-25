from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import (
    FactorContext,
    apply_orientation,
    value_weighted_returns,
)
from .ff_shared import _prep_crsp


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    crsp_m = ctx.base.get("crsp_monthly")
    if crsp_m is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly'")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(years=5)

    cm = crsp_m.copy()
    if "mthcaldt" not in cm.columns:
        raise ValueError("crsp_monthly missing 'mthcaldt'")
    if "mthret" not in cm.columns and "ret" in cm.columns:
        cm = cm.rename(columns={"ret": "mthret"})
    if "mthret" not in cm.columns:
        raise ValueError("crsp_monthly missing 'mthret'")
    if "permno" not in cm.columns:
        raise ValueError("crsp_monthly missing 'permno'")

    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)].copy()

    if "shrcd" in cm.columns:
        cm = cm[cm["shrcd"].isin([10, 11])]
    if "exchcd" in cm.columns:
        cm = cm[cm["exchcd"].isin([1, 2, 3])]

    crsp3, crsp_jun, month_index = _prep_crsp(cm)

    d = crsp3.copy()
    required = ["permno", "mthcaldt", "mthret", "wt", "ffyear"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f"'crsp_monthly' (after _prep_crsp) must contain columns: {missing}")

    d["mthcaldt"] = pd.to_datetime(d["mthcaldt"], errors="coerce")
    d = d.dropna(subset=["permno", "mthcaldt", "mthret", "wt"])

    d_age = d[["permno", "mthcaldt"]].copy()
    d_age["ym_num"] = d_age["mthcaldt"].dt.year * 12 + d_age["mthcaldt"].dt.month
    first_ym = (
        d_age.groupby("permno")["ym_num"]
        .min()
        .rename("first_ym_num")
        .reset_index()
    )

    crsp_jun = crsp_jun.copy()
    crsp_jun["jdate"] = pd.to_datetime(crsp_jun["jdate"], errors="coerce")
    crsp_jun["ym_num"] = crsp_jun["jdate"].dt.year * 12 + crsp_jun["jdate"].dt.month
    june = crsp_jun.merge(first_ym, on="permno", how="left")
    june["age_months"] = june["ym_num"] - june["first_ym_num"]

    june["ipo_dummy"] = (june["age_months"] < 60).astype(int)

    sz_bp = (
        june.groupby("jdate")["me"]
        .median()
        .to_frame("sizemedn")
        .reset_index()
    )
    june = june.merge(sz_bp, on="jdate", how="left")

    june["szport"] = ""
    msz = june["me"].notna() & june["sizemedn"].notna()
    june.loc[msz, "szport"] = np.where(june.loc[msz, "me"] <= june.loc[msz, "sizemedn"], "S", "B")

    june["ipport"] = np.where(june["ipo_dummy"] == 1, "H", "L")

    crsp_monthly = d[["mthcaldt", "permno", "mthret", "wt", "ffyear"]].copy()
    lab = june[["permno", "jdate", "szport", "ipport"]].copy()
    lab["ffyear"] = lab["jdate"].dt.year

    monthly_labeled = crsp_monthly.merge(
        lab.drop(columns=["jdate"]),
        on=["permno", "ffyear"],
        how="left",
    )

    mask = (
        (monthly_labeled["wt"] > 0)
        & monthly_labeled["mthret"].notna()
        & monthly_labeled["szport"].isin(["S", "B"])
        & monthly_labeled["ipport"].isin(["L", "H"])
    )
    d2 = monthly_labeled[mask].copy()

    wide = value_weighted_returns(
        d2,
        date_col="mthcaldt",
        ret_col="mthret",
        weight_col="wt",
        size_bucket_col="szport",
        char_bucket_col="ipport",
    )

    factor = (
        wide[["mthcaldt", "SL", "SH", "BL", "BH"]]
        .assign(
            WH=lambda x: (x["BH"] + x["SH"]) / 2.0,
            WL=lambda x: (x["BL"] + x["SL"]) / 2.0,
            IPO=lambda x: apply_orientation(x["WH"], x["WL"], "high_minus_low"),
        )[["mthcaldt", "IPO"]]
        .rename(columns={"mthcaldt": "date"})
    )

    factor = (
        factor.set_index("date")
        .reindex(month_index[(month_index >= s) & (month_index <= e)])
        .rename_axis("date")
        .reset_index()
    )

    return factor
