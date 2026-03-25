from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from .types import RequestSpec
from .etl import pull, project_from_cache, wrds_session
from .store import Store
from .factors_core import FactorContext, REGISTRY


def main(argv=None):
    p = argparse.ArgumentParser(prog="fzr")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_pull = sub.add_parser("pull", help="Pull a table with caching")
    p_pull.add_argument("--table", required=True)
    p_pull.add_argument("--start", required=True)
    p_pull.add_argument("--end", required=True)
    p_pull.add_argument("--cols", nargs="+", required=True)
    p_pull.add_argument("--date-col", default="mthcaldt")
    p_pull.add_argument("--ttl", type=int, default=1)
    p_pull.add_argument(
        "--chunk-years",
        type=int,
        default=1,
        help="Number of contiguous years to fetch per WRDS query (<=0 disables chunking limits)",
    )
    p_pull.add_argument(
        "--templates-dir",
        default=None,
        help="Optional path to SQL templates directory to override the packaged defaults",
    )

    p_fp = sub.add_parser("fingerprint", help="Compute and store a fingerprint for a cached table/year")
    p_fp.add_argument("--table", required=True)
    p_fp.add_argument("--year", type=int, required=True)
    p_fp.add_argument("--date-col", default="mthcaldt")

    p_build = sub.add_parser("build", help="Build factor outputs")
    available = sorted(list(REGISTRY.keys()))
    p_build.add_argument(
        "--factor",
        required=True,
        choices=["all_factors", *available],
        help="Factor to build. Use 'all_factors' to compute every registered factor and merge them into a single CSV.",
    )
    p_build.add_argument("--start", required=True)
    p_build.add_argument("--end", required=True)
    p_build.add_argument("--version", default="v1")
    p_build.add_argument("--out", required=True)
    p_build.add_argument(
        "--require-cache",
        action="store_true",
        help="Fail fast if cached inputs are incomplete; do not pull",
    )

    p_show = sub.add_parser("show", help="Inspect store metadata")
    sub_show = p_show.add_subparsers(dest="show_cmd", required=True)
    p_show_manifest = sub_show.add_parser("manifest", help="Show manifest records")
    p_show_manifest.add_argument("--table", required=False)

    p_sql = sub.add_parser("render-sql", help="Render the SQL for a pull without executing it")
    p_sql.add_argument("--table", required=True)
    p_sql.add_argument("--start", required=True)
    p_sql.add_argument("--end", required=True)
    p_sql.add_argument("--cols", nargs="+", required=True)
    p_sql.add_argument("--date-col", default="mthcaldt")
    p_sql.add_argument(
        "--templates-dir",
        default=None,
        help="Optional path to SQL templates directory to override the packaged defaults",
    )

    args = p.parse_args(argv)

    if args.cmd == "pull":
        cols = args.cols
        if isinstance(cols, list) and len(cols) == 1 and isinstance(cols[0], str) and "," in cols[0]:
            cols = [c.strip() for c in cols[0].split(",") if c.strip()]
        spec = RequestSpec(
            table=args.table,
            columns=cols,
            date_col=args.date_col,
            date_range=(args.start, args.end),
        )
        store = Store()
        with wrds_session():
            tmpl_dir = None
            if getattr(args, "templates_dir", None):
                tmpl_dir = Path(args.templates_dir)
            pulled = pull(
                spec,
                ttl_days=args.ttl,
                store=store,
                templates_dir=tmpl_dir,
                max_chunk_years=args.chunk_years,
            )
        rows = sum(len(df) for df in pulled.values())
        print(f"pulled_years={sorted(pulled)} rows={rows}")
        return 0

    if args.cmd == "fingerprint":
        store = Store()
        cached = store.read_partitions(args.table, [args.year])
        df = cached.get(args.year)
        if df is None or df.empty:
            print("no_cached_data")
            return 1
        fp = store.compute_fingerprint(df, args.table, args.year, args.date_col)
        print(json.dumps(fp))
        return 0

    if args.cmd == "render-sql":
        cols = args.cols
        if isinstance(cols, list) and len(cols) == 1 and isinstance(cols[0], str) and "," in cols[0]:
            cols = [c.strip() for c in cols[0].split(",") if c.strip()]
        spec = RequestSpec(
            table=args.table,
            columns=cols,
            date_col=args.date_col,
            date_range=(args.start, args.end),
        )
        from .etl import render_sql
        from pathlib import Path as _P
        tmpl_dir = None
        if getattr(args, "templates_dir", None):
            tmpl_dir = _P(args.templates_dir)
        else:
            from .etl import _env, choose_template
            tmpl_dir = _P(__file__).resolve().parent / "templates"
        sql = render_sql(spec, tmpl_dir)
        print(sql)
        return 0

    if args.cmd == "build":
        store = Store()
        crsp_cols = [
            "permno","permco","mthcaldt","mthret","mthretx","shrout","mthprc",
            "shrcd","exchcd","primaryexch","vol",
        ]
        s_req = pd.Timestamp(args.start)
        e_req = pd.Timestamp(args.end)
        s_warm = (s_req - pd.offsets.DateOffset(months=13)).date().isoformat()
        e_str = e_req.date().isoformat()
        spec_crsp = RequestSpec(
            table="crsp.msf_v2",
            columns=crsp_cols,
            date_col="mthcaldt",
            date_range=(s_warm, e_str),
        )
        ccm_cols = [
            "permno","permco","jdate_ltrd","ym","cal_mend","mthret","mthretx","shrout","mthprc",
            "gvkey","datadate","sic","be","currat","act","invt","sale","cogs","che","rect","dp","ppent","lct","oancf","xidoc","dltt","dcvt","dlc","emp","xad","xrd","txt","ib","at",
            "sgr","dvt",
        ]
        spec_ccm = RequestSpec(
            table="ccm_linked_funda",
            columns=ccm_cols,
            date_col="jdate_ltrd",
            date_range=(s_warm, e_str),
            join_policy="ccm_link_L_CP",
        )
        fundq_cols = [
            "permno","permco","jdate_ltrd","ym","gvkey","datadate","rdq","ltq","ibq","dpq","ppentq","sic",
        ]
        spec_fundq = RequestSpec(
            table="ccm_linked_fundq",
            columns=fundq_cols,
            date_col="jdate_ltrd",
            date_range=(s_warm, e_str),
            join_policy="ccm_link_L_CP",
        )

        def project_or_diagnose(spec: RequestSpec) -> pd.DataFrame | None:
            df = project_from_cache(spec, store=store)
            if df is not None and not df.empty:
                return df
            years = list(range(pd.Timestamp(spec.date_range[0]).year, pd.Timestamp(spec.date_range[1]).year + 1))
            cached = store.read_partitions(spec.table, years)
            if len(cached) != len(years):
                missing_years = [y for y in years if y not in cached]
                print(f"cache_missing_years table={spec.table} years={missing_years}")
                return None
            for y, part in cached.items():
                if part is None or part.empty:
                    print(f"cache_empty_year table={spec.table} year={y}")
                    return None
                have = set(part.columns)
                need = set(spec.columns)
                if not need.issubset(have):
                    miss = sorted(need - have)
                    print(f"cache_missing_columns table={spec.table} year={y} missing={miss}")
                    return None
            return project_from_cache(spec, store=store)

        crsp_df = project_or_diagnose(spec_crsp)
        ccm_df = project_or_diagnose(spec_ccm)
        fundq_df = project_or_diagnose(spec_fundq)

        if (crsp_df is None or ccm_df is None or fundq_df is None) and args.require_cache:
            print("cache_validation_failed (require-cache)", file=sys.stderr)
            return 2

        if crsp_df is None or ccm_df is None or fundq_df is None:
            with wrds_session():
                pull(spec_crsp, ttl_days=1, store=store)
                pull(spec_ccm, ttl_days=7, store=store)
                pull(spec_fundq, ttl_days=7, store=store)
            crsp_df = project_from_cache(spec_crsp, store=store)
            ccm_df = project_from_cache(spec_ccm, store=store)
            fundq_df = project_from_cache(spec_fundq, store=store)
            if crsp_df is None or ccm_df is None or fundq_df is None:
                print("cache_miss_or_projection_failed", file=sys.stderr)
                return 2

        ctx = FactorContext(base={
            "crsp_monthly": crsp_df,
            "ccm_linked_funda": ccm_df,
            "ccm_linked_fundq": fundq_df,
        })

        def write_csv(df: pd.DataFrame, out_path: str) -> None:
            p = Path(out_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(p, index=False)
            print(f"wrote={p} rows={len(df)} cols={list(df.columns)}")

        if args.factor == "all_factors":
            merged: pd.DataFrame | None = None
            for key in sorted(REGISTRY.keys()):
                compute = REGISTRY.get(key)
                if compute is None:
                    continue
                try:
                    df = compute(ctx, start=args.start, end=args.end)
                except Exception as ex:
                    print(f"factor_failed key={key} err={ex}")
                    continue
                if df is None or df.empty:
                    continue
                if "date" not in df.columns:
                    print(f"factor_skipped_no_date key={key}")
                    continue
                keep_cols = [c for c in df.columns if c == "date" or c not in ("permno", "permco")]
                df = df[keep_cols]
                merged = df if merged is None else merged.merge(df, on="date", how="outer")
            if merged is None or merged.empty:
                print("no_factors_written")
                return 2
            merged = merged.sort_values("date").reset_index(drop=True)
            out_path = Path(args.out)
            if out_path.suffix.lower() != ".csv":
                out_path.mkdir(parents=True, exist_ok=True)
                out_file = out_path / "all_factors.csv"
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_file = out_path
            merged.to_csv(out_file, index=False)
            print(f"wrote={out_file} rows={len(merged)} cols={list(merged.columns)}")
            return 0
        else:
            compute = REGISTRY.get(args.factor)
            if compute is None:
                print(f"unknown_factor={args.factor}")
                return 2
            out = compute(ctx, start=args.start, end=args.end)
            write_csv(out, args.out)
            return 0

    if args.cmd == "show" and args.show_cmd == "manifest":
        store = Store()
        path = store.manifest
        if not path.exists():
            print("manifest_not_found")
            return 1
        table_filter = getattr(args, "table", None)
        shown = 0
        with open(path) as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if table_filter and rec.get("table") != table_filter:
                    continue
                print(json.dumps(rec))
                shown += 1
        if shown == 0:
            print("no_records")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
