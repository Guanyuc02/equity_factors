from __future__ import annotations

import pandas as pd

from ..factors_core import FactorContext
from .ff_shared import prepare_base
from .ff93_shared import compute_smb_hml


def compute(ctx: FactorContext, *, start: str, end: str) -> pd.DataFrame:
    """FF93 HML factor series using NYSE breakpoints and CRSP last-trading-day dates.

    Returns DataFrame with columns: date, HML
    """
    prep = prepare_base(ctx, start=start, end=end)
    ff = compute_smb_hml(prep)
    return ff[["date", "HML"]]
