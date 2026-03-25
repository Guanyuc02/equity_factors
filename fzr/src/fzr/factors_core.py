from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FactorContext:
    base: Dict[str, pd.DataFrame]


FactorOrientation = Literal["high_minus_low", "low_minus_high"]


def apply_orientation(wh: pd.Series, wl: pd.Series, orientation: FactorOrientation = "high_minus_low") -> pd.Series:
    """Return the long-short spread using a consistent orientation vocabulary."""
    if orientation not in ("high_minus_low", "low_minus_high"):
        raise ValueError(f"Unknown orientation '{orientation}' (expected 'high_minus_low' or 'low_minus_high')")
    return wh - wl if orientation == "high_minus_low" else wl - wh


def nyse_size_median(
    df: pd.DataFrame,
    *,
    date_col: str = "jdate",
    exch_col: str = "primaryexch",
    me_col: str = "me",
) -> pd.DataFrame:
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    samp = d[(d[exch_col] == "N") & (d[me_col] > 0)].copy()
    out = (
        samp.groupby(date_col)[me_col]
        .median()
        .to_frame("sizemedn")
        .reset_index()
        .sort_values(date_col)
    )
    return out


def nyse_quantiles(
    df: pd.DataFrame,
    *,
    value_col: str,
    date_col: str = "jdate",
    exch_col: str = "primaryexch",
    lower_q: float = 0.3,
    upper_q: float = 0.7,
    sample_filter: Optional[pd.Series] = None,
) -> pd.DataFrame:
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    mask = (d[exch_col] == "N")
    if sample_filter is not None:
        mask &= sample_filter.fillna(False)
    samp = d.loc[mask, [date_col, value_col]].dropna()

    def _quantile_nearest(series: pd.Series, q: float) -> float:
        try:
            return series.quantile(q, method="nearest")
        except TypeError:
            return series.quantile(q, interpolation="nearest")

    q = (
        samp.groupby(date_col)[value_col]
        .agg(
            lower=lambda s: _quantile_nearest(s, lower_q),
            upper=lambda s: _quantile_nearest(s, upper_q),
        )
        .rename(columns={"lower": f"{value_col}30", "upper": f"{value_col}70"})
        .reset_index()
        .sort_values(date_col)
    )
    return q


def assign_2x3(
    df: pd.DataFrame,
    *,
    date_col: str = "jdate",
    size_col: str = "me",
    char_col: str = "beme",
    size_bp_col: str = "sizemedn",
    char_q30_col: str = "bm30",
    char_q70_col: str = "bm70",
    out_size: str = "szport",
    out_char: str = "bmport",
    valid_mask: Optional[pd.Series] = None,
) -> pd.DataFrame:
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    if valid_mask is None:
        valid_mask = pd.Series(True, index=d.index)

    d[out_size] = ""
    msz = valid_mask & d[[size_col, size_bp_col]].notna().all(axis=1)
    d.loc[msz, out_size] = np.where(d.loc[msz, size_col] <= d.loc[msz, size_bp_col], "S", "B")

    d[out_char] = ""
    mch = valid_mask & d[[char_col, char_q30_col, char_q70_col]].notna().all(axis=1)
    v = d.loc[mch, char_col]
    q30 = d.loc[mch, char_q30_col]
    q70 = d.loc[mch, char_q70_col]
    d.loc[mch, out_char] = np.select(
        [v <= q30, v <= q70, v > q70], ["L", "M", "H"], default=""
    )
    return d


def value_weighted_returns(
    df: pd.DataFrame,
    *,
    date_col: str = "jdate",
    ret_col: str = "mthret",
    weight_col: str = "wt",
    size_bucket_col: str = "szport",
    char_bucket_col: str = "bmport",
) -> pd.DataFrame:
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    d = d.dropna(subset=[ret_col, weight_col])
    d = d[(d[weight_col] > 0)]
    d = d[d[[size_bucket_col, char_bucket_col]].ne("").all(axis=1)]

    agg = (
        d.assign(wx=d[ret_col] * d[weight_col])
         .groupby([date_col, size_bucket_col, char_bucket_col], as_index=False)
         .agg(wx_sum=("wx", "sum"), w_sum=(weight_col, "sum"))
    )
    agg["vwret"] = np.where(agg["w_sum"] > 0, agg["wx_sum"] / agg["w_sum"], np.nan)
    agg["sbport"] = agg[size_bucket_col] + agg[char_bucket_col]
    wide = agg.pivot(index=date_col, columns="sbport", values="vwret")
    cols = ["SL", "SM", "SH", "BL", "BM", "BH"]
    for c in cols:
        if c not in wide:
            wide[c] = np.nan
    wide = wide[cols]
    return wide.reset_index()


REGISTRY: Dict[str, object] = {}


def _register_builtin_plugins() -> None:
    from .plugins import smb_ff93 as _smb
    from .plugins import hml_ff93 as _hml
    from .plugins import currat_2x3 as _cr
    from .plugins import pchcurrat_2x3 as _pcr
    from .plugins import quick_2x3 as _quick
    from .plugins import pchquick_2x3 as _pq
    from .plugins import pchsaleinv_2x3 as _psi
    from .plugins import pchgm_pchsale_2x3 as _pgm
    from .plugins import saleinv_2x3 as _si
    from .plugins import pchdepr_2x3 as _pd
    from .plugins import salecash_2x3 as _sc
    from .plugins import salerec_2x3 as _sr
    from .plugins import acc_2x3 as _acc
    from .plugins import lev_2x3 as _lev
    from .plugins import pps as _pps
    from .plugins import cashdebt_2x3 as _cashdebt
    from .plugins import depr_2x3 as _depr
    from .plugins import convind_2x3 as _convind
    from .plugins import mom6m as _mom6m
    from .plugins import mom36m as _mom36m
    from .plugins import sgr as _sgr
    from .plugins import IPO as _ipo
    from .plugins import divi as _divi
    from .plugins import divo as _divo
    from .plugins import turn as _turn
    from .plugins import cfp_ia as _cfp_ia
    from .plugins import chempia as _chempia
    from .plugins import mve_ia as _mve_ia
    from .plugins import dolvol as _dolvol
    from .plugins import std_dolvol as _std_dolvol
    from .plugins import std_turn as _std_turn
    from .plugins import adm as _adm
    from .plugins import rdm as _rdm
    from .plugins import rds as _rds
    from .plugins import chinv as _chinv
    from .plugins import chtx as _chtx

    REGISTRY.setdefault("smb_ff93", _smb.compute)
    REGISTRY.setdefault("hml_ff93", _hml.compute)
    REGISTRY.setdefault("currat_2x3", _cr.compute)
    REGISTRY.setdefault("pchcurrat", _pcr.compute)
    REGISTRY.setdefault("quick_2x3", _quick.compute)
    REGISTRY.setdefault("pchquick", _pq.compute)
    REGISTRY.setdefault("pchsaleinv", _psi.compute)
    REGISTRY.setdefault("pchgm_pchsale", _pgm.compute)
    REGISTRY.setdefault("pchdepr", _pd.compute)
    REGISTRY.setdefault("saleinv", _si.compute)
    REGISTRY.setdefault("salecash", _sc.compute)
    REGISTRY.setdefault("salerec", _sr.compute)
    REGISTRY.setdefault("acc", _acc.compute)
    REGISTRY.setdefault("lev_2x3", _lev.compute)
    REGISTRY.setdefault("pps", _pps.compute)
    REGISTRY.setdefault("cashdebt", _cashdebt.compute)
    REGISTRY.setdefault("depr", _depr.compute)
    REGISTRY.setdefault("convind", _convind.compute)
    REGISTRY.setdefault("mom6m", _mom6m.compute)
    REGISTRY.setdefault("mom36m", _mom36m.compute)
    REGISTRY.setdefault("sgr", _sgr.compute)
    REGISTRY.setdefault("IPO", _ipo.compute)
    REGISTRY.setdefault("divi", _divi.compute)
    REGISTRY.setdefault("divo", _divo.compute)
    REGISTRY.setdefault("turn", _turn.compute)
    REGISTRY.setdefault("cfp_ia", _cfp_ia.compute)
    REGISTRY.setdefault("chempia", _chempia.compute)
    REGISTRY.setdefault("mve_ia", _mve_ia.compute)
    REGISTRY.setdefault("dolvol", _dolvol.compute)
    REGISTRY.setdefault("std_dolvol", _std_dolvol.compute)
    REGISTRY.setdefault("std_turn", _std_turn.compute)
    REGISTRY.setdefault("adm", _adm.compute)
    REGISTRY.setdefault("rdm", _rdm.compute)
    REGISTRY.setdefault("rds", _rds.compute)
    REGISTRY.setdefault("chinv", _chinv.compute)
    REGISTRY.setdefault("chtx", _chtx.compute)


_register_builtin_plugins()
