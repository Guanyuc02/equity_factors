import pandas as pd
from pathlib import Path
from fzr.store import Store

def test_write_and_read_partition(tmp_path: Path):
    s = Store(root=tmp_path / "data")
    df = pd.DataFrame({
        "mthcaldt": pd.to_datetime(["2020-01-31","2020-02-28"]),
        "permno": [10001,10001],
        "mthret": [0.01, 0.02]
    })
    p = s.write_partition(df, "crsp.msf_v2", 2020, meta={"spec_key":"x"})
    assert p.exists()
    s.compute_fingerprint(df, "crsp.msf_v2", 2020, "mthcaldt")
    cached = s.read_partitions("crsp.msf_v2", [2020])
    assert 2020 in cached and len(cached[2020]) == 2
    assert s.need_refresh("crsp.msf_v2", 2020, ttl_days=999) is False
