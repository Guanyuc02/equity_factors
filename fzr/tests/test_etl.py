import pandas as pd
from pathlib import Path
from typing import List
from fzr.types import RequestSpec
from fzr.etl import pull, render_sql
from fzr.store import Store
import fzr.etl as etl

def fake_execute_sql(sql: str) -> pd.DataFrame:
    d = pd.DataFrame({
        "permno": [1,1,1,2,2,2],
        "permco": [10,10,10,20,20,20],
        "mthcaldt": pd.to_datetime(["2020-12-31","2021-01-29","2021-02-26",
                                    "2020-12-31","2021-01-29","2021-02-26"]),
        "mthret": [0.0,0.01,0.02, 0.0, -0.01, 0.03],
        "mthretx": [0.0,0.01,0.02, 0.0, -0.01, 0.03],
        "shrout": [1000,1000,1000, 2000,2000,2000],
        "mthprc": [10,10.1,10.2, 20, 19.8, 20.2],
    })
    import re
    m = re.findall(r"DATE '([0-9\-]+)'", sql)
    if len(m) >= 2:
        start, end = pd.to_datetime(m[0]), pd.to_datetime(m[1])
        d = d[(d['mthcaldt'] >= start) & (d['mthcaldt'] <= end)]
    return d.reset_index(drop=True)

def test_render_sql_contains_window_and_columns(tmp_path: Path):
    spec = RequestSpec(
        table="crsp.msf_v2",
        columns=["permno","permco","mthcaldt","mthret","mthretx","shrout","mthprc","exchcd","shrcd"],
        date_col="mthcaldt",
        date_range=("2020-12-01","2021-02-28"),
    )
    tmpl_dir = Path(__file__).resolve().parents[1] / "src" / "fzr" / "templates"
    sql = render_sql(spec, tmpl_dir)
    assert "crsp.msenames" in sql
    assert "2020-12-01" in sql and "2021-02-28" in sql

def test_pull_with_incremental_sync(tmp_path: Path, monkeypatch):
    store = Store(root=tmp_path / "data")
    tmpl_dir = Path(__file__).resolve().parents[1] / "src" / "fzr" / "templates"
    monkeypatch.setattr(etl, "execute_sql", fake_execute_sql)

    spec = RequestSpec(
        table="crsp.msf_v2",
        columns=["permno","permco","mthcaldt","mthret","mthretx","shrout","mthprc"],
        date_col="mthcaldt",
        date_range=("2020-12-01","2021-02-28"),
    )
    pulled = pull(spec, ttl_days=1, store=store, templates_dir=tmpl_dir)
    assert set(pulled.keys()) == {2020, 2021}
    assert len(pulled[2020]) == 2
    assert pulled[2021]['mthcaldt'].max() == pd.Timestamp("2021-02-26")

    pulled2 = pull(spec, ttl_days=999, store=store, templates_dir=tmpl_dir)
    for y in pulled:
        assert len(pulled2[y]) == len(pulled[y])

def test_pull_with_multi_year_chunk(tmp_path: Path, monkeypatch):
    store = Store(root=tmp_path / "data")
    tmpl_dir = Path(__file__).resolve().parents[1] / "src" / "fzr" / "templates"
    calls: List[str] = []

    def tracked_execute_sql(sql: str) -> pd.DataFrame:
        calls.append(sql)
        return fake_execute_sql(sql)

    monkeypatch.setattr(etl, "execute_sql", tracked_execute_sql)

    spec = RequestSpec(
        table="crsp.msf_v2",
        columns=["permno","permco","mthcaldt","mthret","mthretx","shrout","mthprc"],
        date_col="mthcaldt",
        date_range=("2020-01-01","2021-12-31"),
    )
    pulled = pull(
        spec,
        ttl_days=0,
        store=store,
        templates_dir=tmpl_dir,
        max_chunk_years=0,
    )

    assert len(calls) == 1
    assert set(pulled.keys()) == {2020, 2021}
    assert pulled[2020]["mthcaldt"].min() == pd.Timestamp("2020-12-31")
    assert pulled[2021]["mthcaldt"].max() == pd.Timestamp("2021-02-26")
