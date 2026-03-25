import pandas as pd
from fzr.calendar import month_index_from_crsp

def test_month_index_from_crsp():
    d = pd.to_datetime(["2020-01-30","2020-01-31","2020-02-28","2020-02-27","2020-03-31"])
    idx = month_index_from_crsp(pd.DataFrame({"mthcaldt": d}), "mthcaldt")
    assert list(idx) == [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-28"), pd.Timestamp("2020-03-31")]
