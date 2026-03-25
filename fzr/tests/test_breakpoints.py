import pandas as pd
from fzr.factors_core import nyse_size_median, nyse_quantiles, assign_2x3


def test_nyse_breakpoints_and_assignment():
    # Two months of toy data
    d = pd.DataFrame(
        {
            "jdate": pd.to_datetime(
                [
                    "2020-06-30",
                    "2020-06-30",
                    "2020-06-30",
                    "2020-06-30",
                    "2020-07-31",
                    "2020-07-31",
                    "2020-07-31",
                    "2020-07-31",
                ]
            ),
            "primaryexch": ["N", "N", "N", "Q", "N", "N", "N", "N"],
            "me": [100.0, 200.0, 300.0, 400.0, 50.0, 80.0, 90.0, 100.0],
            "beme": [0.1, 0.5, 1.0, 0.9, 0.2, 0.4, 0.6, 0.8],
        }
    )

    sz = nyse_size_median(d, date_col="jdate", exch_col="primaryexch", me_col="me")
    # 2020-06-30 NYSE me = [100,200,300] -> median = 200
    # 2020-07-31 NYSE me = [50,80,90,100] -> median = (80+90)/2 = 85
    exp_sz = {
        pd.Timestamp("2020-06-30"): 200.0,
        pd.Timestamp("2020-07-31"): 85.0,
    }
    got = dict(zip(sz["jdate"], sz["sizemedn"]))
    assert got == exp_sz

    q = nyse_quantiles(d, value_col="beme", date_col="jdate", exch_col="primaryexch")
    # 2020-06-30 NYSE beme = [0.1, 0.5, 1.0]
    # nearest quantile(0.3) -> 0.5, quantile(0.7) -> 0.5
    # 2020-07-31 NYSE beme = [0.2, 0.4, 0.6, 0.8]
    # nearest quantile(0.3) -> 0.4, quantile(0.7) -> 0.6
    exp = {
        pd.Timestamp("2020-06-30"): (0.5, 0.5),
        pd.Timestamp("2020-07-31"): (0.4, 0.6),
    }
    got = dict(zip(q["jdate"], zip(q["beme30"], q["beme70"])))
    assert got == exp

    # Merge breakpoints and assign portfolios
    dm = d.merge(sz, on="jdate").merge(
        q.rename(columns={"beme30": "bm30", "beme70": "bm70"}), on="jdate"
    )
    assigned = assign_2x3(
        dm,
        date_col="jdate",
        size_col="me",
        char_col="beme",
        size_bp_col="sizemedn",
        char_q30_col="bm30",
        char_q70_col="bm70",
        out_size="szport",
        out_char="bmport",
    )

    # A couple of spot checks
    r = assigned.sort_values(["jdate", "me"]).reset_index(drop=True)
    # On 2020-06-30, me=100 <= 200 -> S; beme=0.1 <= 0.5 -> L
    assert r.loc[0, ["szport", "bmport"]].tolist() == ["S", "L"]
    # On 2020-07-31, me=100 > 85 -> B; beme=0.8 > 0.6 -> H
    assert r.loc[r["jdate"] == pd.Timestamp("2020-07-31")].iloc[-1][["szport", "bmport"]].tolist() == [
        "B",
        "H",
    ]

