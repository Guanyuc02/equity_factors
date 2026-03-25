from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import pandas as pd
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pathlib import Path
import contextlib
import threading

from .store import Store
from .types import RequestSpec

def _env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(disabled_extensions=("sql",)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

def choose_template(spec: RequestSpec, templates_dir: Path) -> str:
    if spec.table == "crsp.msf_v2":
        return "queries/crsp/msf_v2.sql.j2"
    if spec.table == "ccm_linked_funda":
        if spec.join_policy not in (None, "ccm_link_L_CP"):
            raise ValueError(f"Unsupported join_policy for {spec.table}: {spec.join_policy}")
        return "queries/crsp/ccm_linked_funda.sql.j2"
    if spec.table == "ccm_linked_fundq":
        if spec.join_policy not in (None, "ccm_link_L_CP"):
            raise ValueError(f"Unsupported join_policy for {spec.table}: {spec.join_policy}")
        return "queries/crsp/ccm_linked_fundq.sql.j2"
    raise ValueError(f"No template for table {spec.table}")

def render_sql(spec: RequestSpec, templates_dir: Path) -> str:
    tmpl_path = choose_template(spec, templates_dir)
    env = _env(templates_dir)
    tmpl = env.get_template(tmpl_path)
    start, end = spec.date_range
    return tmpl.render(
        table=spec.table,
        columns=spec.columns,
        date_col=spec.date_col,
        start_date=start,
        end_date=end,
        filters=spec.filters,
    )

_LOCAL = threading.local()

@contextlib.contextmanager
def wrds_session():
    """Context-manage a single WRDS connection for reuse within the block.

    - Reuses an already-active session if nested.
    - Ensures the underlying SSH tunnel and DB engine close on exit.
    """
    active = getattr(_LOCAL, "wrds_conn", None)
    if active is not None:
        # Nested usage: just yield the active one
        yield active
        return

    import wrds
    with wrds.Connection() as conn:
        _LOCAL.wrds_conn = conn
        try:
            yield conn
        finally:
            # conn.__exit__ already closed/cleaned; clear our thread-local
            _LOCAL.wrds_conn = None

def _active_wrds_conn() -> Optional[object]:
    return getattr(_LOCAL, "wrds_conn", None)

def _execute_with_conn(sql: str, conn) -> pd.DataFrame:
    import warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"wrds\.sql")

    date_cols = ["mthcaldt"] if "mthcaldt" in sql else None

    # Path 1: WRDS-native. Most stable.
    try:
        return conn.raw_sql(sql, date_cols=date_cols)
    except Exception:
        pass

    # Path 2: Pandas on a SQLAlchemy connection with a plain string query.
    from sqlalchemy import exc as sa_exc

    try:
        return pd.read_sql_query(sql, conn.engine, parse_dates=date_cols)
    except (sa_exc.SQLAlchemyError, TypeError, AttributeError, ValueError):
        # Path 3: Manual fetch via SQLAlchemy driver
        with conn.engine.connect() as econn:
            result = econn.exec_driver_sql(sql)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if date_cols:
            for dc in date_cols:
                if dc in df.columns:
                    df[dc] = pd.to_datetime(df[dc], errors="coerce")
        return df

def execute_sql(sql: str) -> pd.DataFrame:
    """Execute SQL against WRDS, reusing a scoped session when available.

    If called inside a `wrds_session()` block, reuses that single connection
    for all calls; otherwise, creates a short-lived session that is closed
    immediately after the query.
    """
    conn = _active_wrds_conn()
    if conn is not None:
        return _execute_with_conn(sql, conn)
    # Fallback: open a one-off session for this call only.
    with wrds_session() as tmp_conn:
        return _execute_with_conn(sql, tmp_conn)

def spec_to_years(spec: RequestSpec) -> List[int]:
    start, end = map(pd.Timestamp, spec.date_range)
    return list(range(start.year, end.year + 1))

def normalize_spec(spec: RequestSpec) -> RequestSpec:
    cols = sorted(set(spec.columns))
    return RequestSpec(
        table=spec.table,
        columns=cols,
        date_col=spec.date_col,
        date_range=spec.date_range,
        filters=dict(sorted(spec.filters.items())),
        join_policy=spec.join_policy,
        asof_policy=spec.asof_policy,
        version=spec.version,
    )

def _postprocess(df: pd.DataFrame, spec: RequestSpec) -> pd.DataFrame:
    if spec.table == "crsp.msf_v2":
        for c in ("permno","permco"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        for c in ("shrcd","exchcd"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        # WRDS returns returns/prices as Decimal; coerce to floats to mirror wrds_factors.py
        for c in ("mthret", "mthretx", "shrout", "mthprc"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "mthcaldt" in df:
            df["mthcaldt"] = pd.to_datetime(df["mthcaldt"], errors="coerce")
    if spec.table == "ccm_linked_funda":
        for c in ("permno","permco"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        # Coerce common numeric fields that may arrive as Decimal/object to floats
        for c in (
            "be",
            "currat",
            "act",
            "invt",
            "sale",
            "cogs",
            "che",
            "rect",
            "dp",
            "ppent",
            "ib",
            "at",
            "lct",
            "oancf",
            "xidoc",
            "dltt",
            "dlc",
            "emp",
            "xad",
            "xrd",
            "txt",
            "mthret",
            "mthretx",
            "shrout",
            "mthprc",
        ):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "sic" in df:
            df["sic"] = pd.to_numeric(df["sic"], errors="coerce").astype("Int64")
        for dc in ("jdate_ltrd", "datadate", "cal_mend", "ym"):
            if dc in df:
                df[dc] = pd.to_datetime(df[dc], errors="coerce")
    if spec.table == "ccm_linked_fundq":
        for c in ("permno","permco"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        # Key ratio inputs arrive as Decimal/object; coerce to floats
        for c in ("ltq", "ibq", "dpq", "ppentq"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "sic" in df:
            df["sic"] = pd.to_numeric(df["sic"], errors="coerce").astype("Int64")
        for dc in ("jdate_ltrd", "datadate", "rdq", "ym"):
            if dc in df:
                df[dc] = pd.to_datetime(df[dc], errors="coerce")
    return df

def _dedupe(df: pd.DataFrame, date_col: str, key_cols: List[str]) -> pd.DataFrame:
    if not key_cols:
        return df.drop_duplicates()
    return df.sort_values([date_col] + key_cols).drop_duplicates([date_col] + key_cols, keep="last")

def partial_fill_plan(store: Store, spec: RequestSpec, year: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
    start, end = map(pd.Timestamp, spec.date_range)
    cached = store.read_partitions(spec.table, [year]).get(year)
    if cached is None or cached.empty or spec.date_col not in cached:
        return (pd.Timestamp(f"{year}-01-01"), min(end, pd.Timestamp(f"{year}-12-31")))
    dates = pd.to_datetime(cached[spec.date_col], errors="coerce").dropna()
    if dates.empty:
        return (pd.Timestamp(f"{year}-01-01"), min(end, pd.Timestamp(f"{year}-12-31")))
    max_date = dates.max()
    start_next = max_date + pd.Timedelta(days=1)
    stop = min(end, pd.Timestamp(f"{year}-12-31"))
    if start_next > stop:
        return (stop, stop)
    return (start_next, stop)

def pull(
    spec: RequestSpec,
    ttl_days: int = 1,
    store: Store | None = None,
    templates_dir: Path | None = None,
    max_chunk_years: int | None = 1,
) -> Dict[int, pd.DataFrame]:
    store = store or Store()
    templates_dir = templates_dir or (Path(__file__).resolve().parent / "templates")

    spec = normalize_spec(spec)
    years = spec_to_years(spec)
    out: Dict[int, pd.DataFrame] = {}
    cached = store.read_partitions(spec.table, years)

    for y in years:
        if y in cached and not store.need_refresh(spec.table, y, ttl_days):
            out[y] = cached[y].copy()

    start_ts, end_ts = map(pd.Timestamp, spec.date_range)

    pull_plan: List[Tuple[int, pd.Timestamp, pd.Timestamp]] = []

    for y in years:
        if y in out and y != years[-1]:
            continue

        year_start = max(start_ts, pd.Timestamp(f"{y}-01-01"))
        year_end = min(end_ts, pd.Timestamp(f"{y}-12-31"))

        if y == years[-1] and ttl_days > 0:
            y_start, y_end = partial_fill_plan(store, spec, y)
            y_start = max(y_start, year_start)
            y_end = min(y_end, year_end)
        else:
            y_start, y_end = (year_start, year_end)

        if y_start > y_end:
            continue

        pull_plan.append((y, y_start, y_end))

    if not pull_plan:
        return out

    chunk_limit = max_chunk_years if max_chunk_years and max_chunk_years > 0 else None

    def process_chunk(entries: List[Tuple[int, pd.Timestamp, pd.Timestamp]]) -> None:
        if not entries:
            return
        chunk_start = entries[0][1]
        chunk_end = entries[-1][2]
        chunk_spec = RequestSpec(
            table=spec.table,
            columns=spec.columns,
            date_col=spec.date_col,
            date_range=(str(chunk_start.date()), str(chunk_end.date())),
            filters=spec.filters,
            join_policy=spec.join_policy,
            asof_policy=spec.asof_policy,
            version=spec.version,
        )
        sql = render_sql(chunk_spec, templates_dir)
        df_chunk = execute_sql(sql)
        df_chunk = _postprocess(df_chunk, chunk_spec)

        if not df_chunk.empty and spec.date_col not in df_chunk.columns:
            raise ValueError(f"Result set missing date column {spec.date_col} for table {spec.table}")

        date_series = df_chunk[spec.date_col] if spec.date_col in df_chunk.columns else None

        for y, y_start, y_end in entries:
            if date_series is not None and not df_chunk.empty:
                mask = (date_series >= y_start) & (date_series <= y_end)
                df_new = df_chunk.loc[mask].copy()
            else:
                df_new = df_chunk.copy()

            if y in cached:
                base = cached[y]
                frames = []
                if base is not None and not base.empty and not base.isna().all().all():
                    frames.append(base)
                if df_new is not None and not df_new.empty and not df_new.isna().all().all():
                    frames.append(df_new)
                if frames:
                    df_all = pd.concat(frames, ignore_index=True)
                else:
                    df_all = df_new if df_new is not None else base
            else:
                df_all = df_new

            key_cols = [c for c in ("permno","permco") if c in df_all.columns]
            df_all = _dedupe(df_all, spec.date_col, key_cols)
            df_all = _postprocess(df_all, spec)

            meta = {"spec_key": spec.key(), "start": str(y_start.date()), "end": str(y_end.date())}
            store.write_partition(df_all, spec.table, y, meta)
            store.compute_fingerprint(df_all, spec.table, y, spec.date_col)
            out[y] = df_all

    chunk: List[Tuple[int, pd.Timestamp, pd.Timestamp]] = []
    for entry in pull_plan:
        if not chunk:
            chunk = [entry]
            continue
        prev_year = chunk[-1][0]
        within_limit = chunk_limit is None or len(chunk) < chunk_limit
        if entry[0] == prev_year + 1 and within_limit:
            chunk.append(entry)
        else:
            process_chunk(chunk)
            chunk = [entry]
    if chunk:
        process_chunk(chunk)

    return out

def project_from_cache(spec: RequestSpec, store: Store | None = None) -> pd.DataFrame | None:
    store = store or Store()
    spec = normalize_spec(spec)
    years = spec_to_years(spec)
    cached = store.read_partitions(spec.table, years)
    if len(cached) != len(years):
        return None

    start, end = map(pd.Timestamp, spec.date_range)
    frames: List[pd.DataFrame] = []
    for y in years:
        df = cached.get(y)
        if df is None or df.empty or not set(spec.columns).issubset(df.columns):
            return None
        # Normalize dtypes from cache (old parquet may store Decimal as object)
        df = _postprocess(df.copy(), spec)
        df[spec.date_col] = pd.to_datetime(df[spec.date_col], errors="coerce")
        mask = (df[spec.date_col] >= start) & (df[spec.date_col] <= end)
        if not mask.any():
            continue
        frames.append(df.loc[mask, spec.columns])

    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)
