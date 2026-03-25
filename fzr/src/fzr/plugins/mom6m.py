from __future__ import annotations

import numpy as np
import pandas as pd

from ..factors_core import FactorContext
from .ff_shared import _prep_crsp


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    crsp_m = ctx.base.get("crsp_monthly")
    if crsp_m is None:
        raise ValueError("FactorContext.base must include 'crsp_monthly'")

    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s_warm = s - pd.offsets.DateOffset(months=12)

    cm = crsp_m.copy()
    if "mthcaldt" not in cm.columns:
        raise ValueError("crsp_monthly must contain 'mthcaldt'")
    if "mthret" not in cm.columns and "ret" in cm.columns:
        cm = cm.rename(columns={"ret": "mthret"})
    if "mthret" not in cm.columns:
        raise ValueError("crsp_monthly must contain 'mthret' or 'ret'")

    cm["mthcaldt"] = pd.to_datetime(cm["mthcaldt"], errors="coerce")
    cm = cm[(cm["mthcaldt"] >= s_warm) & (cm["mthcaldt"] <= e)].copy()

    crsp3, _, month_index = _prep_crsp(cm)

    d = crsp3.sort_values(["permno", "mthcaldt"]).copy()
    d["ret1p"] = 1.0 + d["mthret"].fillna(0.0)
    d["log_ret1p"] = np.log(d["ret1p"].clip(lower=1e-6))

    d["mom6m_log"] = (
        d.groupby("permno")["log_ret1p"]
        .rolling(window=6, min_periods=6)
        .sum()
        .reset_index(level=0, drop=True)
    )
    d["mom6m_char"] = np.exp(d["mom6m_log"]) - 1.0
    d.replace([np.inf, -np.inf], np.nan, inplace=True)

    base_mask = d["wt"].gt(0) & d["mom6m_char"].notna()
    samp = d.loc[base_mask, ["mthcaldt", "mom6m_char"]].copy()

    def _q(series: pd.Series, q: float) -> float:
        try:
            return series.quantile(q, method="nearest")
        except TypeError:
            return series.quantile(q, interpolation="nearest")

    bp = (
        samp.groupby("mthcaldt")["mom6m_char"]
        .agg(
            mom30=lambda s_: _q(s_, 0.3),
            mom70=lambda s_: _q(s_, 0.7),
        )
        .reset_index()
        .sort_values("mthcaldt")
    )

    d = d.merge(bp, on="mthcaldt", how="left")

    port_mask = (
        d["wt"].gt(0)
        & d["mom6m_char"].notna()
        & d[["mom30", "mom70"]].notna().all(axis=1)
    )

    d["momport"] = ""
    v = d.loc[port_mask, "mom6m_char"]
    q30 = d.loc[port_mask, "mom30"]
    q70 = d.loc[port_mask, "mom70"]

    d.loc[port_mask, "momport"] = np.select(
        [v <= q30, v >= q70],
        ["L", "H"],
        default="",
    )

    panel = d[d["momport"].isin(["L", "H"])].copy()
    panel = panel[(panel["wt"] > 0) & panel["mthret"].notna()]

    panel["wx"] = panel["mthret"] * panel["wt"]

    cohort = (
        panel.groupby(["mthcaldt", "momport"], as_index=False)
        .agg(wx_sum=("wx", "sum"), w_sum=("wt", "sum"))
    )
    cohort["vwret"] = np.where(
        cohort["w_sum"] > 0,
        cohort["wx_sum"] / cohort["w_sum"],
        np.nan,
    )

    wide = cohort.pivot(
        index="mthcaldt",
        columns="momport",
        values="vwret",
    )

    for c in ["L", "H"]:
        if c not in wide.columns:
            wide[c] = np.nan
    wide = wide[["L", "H"]]

    wide["spread"] = wide["H"] - wide["L"]

    factor = (
        wide["spread"]
        .to_frame("mom6m")
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
