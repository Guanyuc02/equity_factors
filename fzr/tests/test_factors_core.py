import numpy as np
import pandas as pd
from fzr.factors_core import value_weighted_returns


def test_value_weighted_returns_shape_and_values():
    # Build a single-month fixture with 6 portfolios and trivial weights
    date = pd.Timestamp("2020-06-30")
    rows = []
    # Define returns for SL, SM, SH, BL, BM, BH
    port_rets = {
        ("S", "L"): 0.01,
        ("S", "M"): 0.02,
        ("S", "H"): -0.01,
        ("B", "L"): 0.005,
        ("B", "M"): 0.004,
        ("B", "H"): 0.003,
    }
    for (sz, ch), r in port_rets.items():
        # 3 firms per bucket with equal weights so VW = mean
        for i in range(3):
            rows.append(
                {
                    "jdate": date,
                    "mthret": r,
                    "wt": 1.0,
                    "szport": sz,
                    "bmport": ch,
                }
            )
    d = pd.DataFrame(rows)
    wide = value_weighted_returns(d)
    assert list(wide.columns) == ["jdate", "SL", "SM", "SH", "BL", "BM", "BH"]
    got = wide.iloc[0].to_dict()
    assert np.isclose(got["SL"], 0.01)
    assert np.isclose(got["SM"], 0.02)
    assert np.isclose(got["SH"], -0.01)
    assert np.isclose(got["BL"], 0.005)
    assert np.isclose(got["BM"], 0.004)
    assert np.isclose(got["BH"], 0.003)

