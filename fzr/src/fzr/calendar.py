from __future__ import annotations

import pandas as pd


def month_index_from_crsp(crsp_like: pd.DataFrame, date_col: str) -> pd.Series:
    """Return the last trading date observed for each month in CRSP-style data."""
    dates = pd.to_datetime(crsp_like[date_col], errors="coerce").dropna()
    if dates.empty:
        return pd.Series(dtype="datetime64[ns]")

    month_last = dates.groupby(dates.dt.to_period("M")).max().sort_index()
    return pd.Series(month_last.to_numpy(), name=date_col)
