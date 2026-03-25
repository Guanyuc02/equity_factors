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
    s_warm = s - pd.offsets.DateOffset(years=2)

    cm = crsp_m.copy()
    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)].copy()

    crsp3, _, month_index = _prep_crsp(cm)

    d = crsp3.copy()

    required_crsp = ["permno", "mthcaldt", "mthret", "wt", "ffyear"]
    missing_crsp = [c for c in required_crsp if c not in d.columns]
    if missing_crsp:
        raise ValueError(f"'crsp_monthly' (after _prep_crsp) must contain columns: {missing_crsp}")

    f = funda.copy()
    f["jdate"] = pd.to_datetime(f["jdate_ltrd"], errors="coerce")
    f = f[(f["jdate"] >= s_warm) & (f["jdate"] <= e)].copy()

    required_funda = ["permno", "jdate", "sgr"]
    missing_funda = [c for c in required_funda if c not in f.columns]
    if missing_funda:
        raise ValueError(f"'ccm_linked_funda' must contain columns: {missing_funda}")

    f["ffyear"] = f["jdate"].dt.year
    char = f[["permno", "ffyear", "sgr"]].dropna(subset=["sgr"]).copy()

    d = d.merge(char, on=["permno", "ffyear"], how="left")

    d["mthcaldt"] = pd.to_datetime(d["mthcaldt"], errors="coerce")
    d = d[(d["mthcaldt"] >= s_warm) & (d["mthcaldt"] <= e)].copy()

    d["me"] = d["wt"]
    d["sgr_char"] = d["sgr"]
    d.replace([np.inf, -np.inf], np.nan, inplace=True)

    base_mask = d["me"].gt(0) & d["sgr_char"].notna()
    samp = d.loc[base_mask, ["mthcaldt", "sgr_char"]].copy()

    def _q(series: pd.Series, q: float) -> float:
        try:
            return series.quantile(q, method="nearest")
        except TypeError:
            return series.quantile(q, interpolation="nearest")

    bp = (
        samp.groupby("mthcaldt")["sgr_char"]
        .agg(
            sgr30=lambda s: _q(s, 0.3),
            sgr70=lambda s: _q(s, 0.7),
        )
        .reset_index()
        .sort_values("mthcaldt")
    )

    d = d.merge(bp, on="mthcaldt", how="left")

    port_mask = (
        d["me"].gt(0)
        & d["sgr_char"].notna()
        & d[["sgr30", "sgr70"]].notna().all(axis=1)
    )

    d["sgrport"] = ""
    v = d.loc[port_mask, "sgr_char"]
    q30 = d.loc[port_mask, "sgr30"]
    q70 = d.loc[port_mask, "sgr70"]

    d.loc[port_mask, "sgrport"] = np.select(
        [v <= q30, v >= q70],
        ["L", "H"],
        default="",
    )

    panel = d[d["sgrport"].isin(["L", "H"])].copy()
    panel = panel[(panel["wt"] > 0) & panel["mthret"].notna()]

    panel["wx"] = panel["mthret"] * panel["wt"]

    cohort = (
        panel.groupby(["mthcaldt", "sgrport"], as_index=False)
        .agg(wx_sum=("wx", "sum"), w_sum=("wt", "sum"))
    )
    cohort["vwret"] = np.where(
        cohort["w_sum"] > 0,
        cohort["wx_sum"] / cohort["w_sum"],
        np.nan,
    )

    wide = cohort.pivot(
        index="mthcaldt",
        columns="sgrport",
        values="vwret",
    )

    for c in ["L", "H"]:
        if c not in wide.columns:
            wide[c] = np.nan
    wide = wide[["L", "H"]]

    wide["spread"] = wide["L"] - wide["H"]

    factor = (
        wide["spread"]
        .to_frame("sgr")
        .reset_index()
        .rename(columns={"mthcaldt": "date"})
    )

    factor = (
        factor.set_index("date")
        .reindex(month_index[(month_index >= s) & (month_index <= e)])
        .rename_axis("date")
        .reset_index()
    )

    return factor
