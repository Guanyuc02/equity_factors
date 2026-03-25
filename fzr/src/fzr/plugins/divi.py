from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ff_shared import _prep_crsp


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    crsp_m = ctx.base.get("crsp_monthly")
    funda = ctx.base.get("ccm_linked_funda")
    if crsp_m is None or funda is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly' and 'ccm_linked_funda'")

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

    crsp3, _, month_index = _prep_crsp(cm)
    d = crsp3.copy()

    required_crsp = ["permno", "mthcaldt", "mthret", "wt", "ffyear"]
    missing_crsp = [c for c in required_crsp if c not in d.columns]
    if missing_crsp:
        raise ValueError(f"'crsp_monthly' (after _prep_crsp) must contain columns: {missing_crsp}")

    d["mthcaldt"] = pd.to_datetime(d["mthcaldt"], errors="coerce")
    d = d.dropna(subset=["permno", "mthcaldt", "mthret", "wt"])

    f = funda.copy()
    for col in ["datadate", "ym"]:
        if col not in f.columns:
            raise ValueError(f"'ccm_linked_funda' must contain '{col}'")
    if "dvt" not in f.columns:
        raise ValueError("'ccm_linked_funda' must contain 'dvt'")
    f["datadate"] = pd.to_datetime(f["datadate"], errors="coerce")
    f["ym"] = pd.to_datetime(f["ym"], errors="coerce")
    f = f[(f["datadate"] >= s_warm - pd.offsets.DateOffset(years=3)) & (f["datadate"] <= e)].copy()
    f = f.dropna(subset=["permno", "datadate"])

    f = f.sort_values(["permno", "datadate"])
    f["pay_div"] = np.where(f["dvt"].notna() & (f["dvt"] > 0), 1, 0)
    f["pay_div_lag"] = f.groupby("permno")["pay_div"].shift(1)
    f["is_event"] = (f["pay_div"] == 1) & (f["pay_div_lag"] == 0)

    char = (
        f.groupby(["permno", "ym"], as_index=False)["is_event"]
        .max()
        .rename(columns={"is_event": "divi_char"})
    )
    char["divi_char"] = char["divi_char"].astype(float)
    char["ffyear"] = pd.to_datetime(char["ym"]).dt.year

    char = char[["permno", "ffyear", "divi_char"]]
    d = d.merge(char, on=["permno", "ffyear"], how="left")
    d["divi_char"] = d["divi_char"].fillna(0.0)

    mask = (d["wt"] > 0) & d["mthret"].notna()
    panel = d.loc[mask, ["mthcaldt", "mthret", "wt", "divi_char"]].copy()

    def _spread(g: pd.DataFrame) -> float:
        if g.empty:
            return np.nan
        g1 = g[g["divi_char"] > 0]
        g0 = g[g["divi_char"] <= 0]
        if g1.empty or g0.empty:
            return np.nan
        w1 = g1["wt"].astype(float).clip(lower=0.0)
        w0 = g0["wt"].astype(float).clip(lower=0.0)
        if w1.sum() <= 0 or w0.sum() <= 0:
            return np.nan
        r1 = float((w1 * g1["mthret"]).sum() / w1.sum())
        r0 = float((w0 * g0["mthret"]).sum() / w0.sum())
        return r1 - r0

    factor = (
        panel.groupby("mthcaldt", group_keys=False)
        .apply(_spread)
        .to_frame("divi")
        .reset_index()
        .rename(columns={"mthcaldt": "date"})
    )

    factor["date"] = pd.to_datetime(factor["date"])
    factor = factor[(factor["date"] >= s) & (factor["date"] <= e)]
    factor = (
        factor.set_index("date")
        .reindex(month_index[(month_index >= s) & (month_index <= e)])
        .rename_axis("date")
        .reset_index()
    )
    return factor
