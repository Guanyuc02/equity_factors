import pandas as pd
from pathlib import Path

from fzr.types import RequestSpec
from fzr.etl import render_sql


def test_ccm_template_contains_link_and_dedupe(tmp_path: Path):
    spec = RequestSpec(
        table="ccm_linked_funda",
        columns=[
            "permno",
            "permco",
            "jdate_ltrd",
            "ym",
            "cal_mend",
            "mthret",
            "mthretx",
            "shrout",
            "mthprc",
            "gvkey",
            "datadate",
            "sic",
            "be",
            "currat",
        ],
        date_col="jdate_ltrd",
        date_range=("2020-06-01", "2020-07-31"),
        join_policy="ccm_link_L_CP",
    )
    tmpl_dir = Path(__file__).resolve().parents[1] / "src" / "fzr" / "templates"
    sql = render_sql(spec, tmpl_dir)
    assert "crsp.ccmxpf_linktable" in sql
    assert "SUBSTR(linktype, 1, 1) = 'L'" in sql
    assert "linkprim IN ('C','P')" in sql
    assert "ROW_NUMBER() OVER (PARTITION BY permno, ym ORDER BY datadate DESC)" in sql

    # Limited to SQL rendering validation in this test suite
