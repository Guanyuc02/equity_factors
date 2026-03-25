# fzr

`fzr` is a CLI-first toolkit for caching WRDS source tables and rebuilding the factor zoo out of band. Install it locally, point it at your WRDS credentials, and the commands below will materialize the factor CSVs shipped in this repo. Progress is updated in this file: https://docs.google.com/spreadsheets/d/16vmPKsEz4hg8uUuwWUB2suoRTkD1QYwdtej-NO5qihI/edit?gid=1619954194#gid=1619954194

## Quick Start
1. Create a virtualenv: `python3 -m venv .venv && source .venv/bin/activate`. Note that this step is essential as some of the previous packages in the exisiting environments might influence the initialization of fzr.
2. Install the project: `pip install -e .`
3. Cache core data:
   - CRSP monthly returns: `fzr pull --table crsp.msf_v2 --start 1975-01-01 --end 2024-12-31 --cols mthcaldt permno permco mthret mthretx shrout mthprc shrcd exchcd primaryexch --ttl 0 --chunk-years 0`
   - CCM-linked Compustat fundamentals: `fzr pull --table ccm_linked_funda --start 1975-01-01 --end 2024-12-31 --date-col jdate_ltrd --cols permno,permco,jdate_ltrd,ym,cal_mend,gvkey,datadate,sic,be,currat,act,invt,sale,cogs,che,rect,dp,ppent,lct,oancf,xidoc,dltt,dcvt,dlc,emp,xad,xrd,txt,ib,at,mthret,mthretx,shrout,mthprc --ttl 0 --chunk-years 0`
   - CCM-linked Compustat quarterly: `fzr pull --table ccm_linked_fundq --start 1975-01-01 --end 2024-12-31 --date-col jdate_ltrd --cols permno,permco,jdate_ltrd,ym,gvkey,datadate,rdq,ltq,ibq,dpq,ppentq,sic --ttl 0 --chunk-years 0`
4. Build all factors: `fzr build --factor all_factors --start 1976-07-01 --end 2024-12-31 --out out_factors/wrds_factors.csv --require-cache`. Afterwards, open `fzr/replication_test.ipynb` in Jupyter (or execute it headlessly with `jupyter nbconvert --to notebook --execute fzr/replication_test.ipynb`) to sanity-check the freshly created `wrds_factors.csv` against the reference outputs.

Requirements: Python 3.10+, `pandas>=2.1`, `SQLAlchemy>=2.0`, `psycopg2-binary>=2.9`. If you see `AttributeError: 'Engine' object has no attribute 'cursor'`, upgrade SQLAlchemy: `pip install -U "sqlalchemy>=2.0"`.

## Configuration & Data
- **WRDS credentials**: the CLI prompts via `wrds.Connection()`. For unattended jobs, store credentials in `.pgpass` or WRDS-supported environment variables.
- **Data root**: defaults to `fzr/data`. Override with `export FZR_DATA_ROOT=/absolute/path`.
- **Artifacts**: raw partitions under `data/raw/<table>/year=YYYY`, manifests in `data/manifest/`, fingerprints in `data/manifest/fingerprints/`, and factor exports in `out_<factor>/`.

## CLI Overview
- `fzr pull`: cache WRDS tables within a date window (`--table`, `--start`, `--end`, `--cols`, optional `--date-col`, `--ttl`). The `--ttl` flag sets how many days a cached partition remains fresh; use `--ttl 0` to force a re-download when you know the upstream data changed. Pass `--chunk-years N` to download `N` contiguous years per WRDS query (default 1, use `0` for the entire window); `fzr` still splits and fingerprints the results per year after each chunk completes.
- `fzr build`: recompute a factor or bundle and write a CSV (`--out` creates directories as needed).
  - Bundle: `all_factors` (merges all registered time-series factors into a single CSV; new factors are picked up automatically).
  - Individual factors: `smb_ff93`, `hml_ff93`, `currat_2x3`, `quick_2x3`, `pchcurrat`, `pchquick`, `pchsaleinv`, `pchgm_pchsale`, `pchdepr`, `saleinv`, `salecash`, `salerec`, `acc`, `lev_2x3`, `pps`, `cashdebt`, `depr`.
- `fzr fingerprint`: hash a cached partition to confirm integrity.
- `fzr show manifest`: inspect cached table metadata (JSON lines stored in `data/manifest/manifest.jsonl`) to verify row counts, byte sizes, and when each partition was written.

## Cache TTL & Metadata
- Cache TTLs: each `fzr pull` writes per-year partitions plus a fingerprint JSON (`data/manifest/fingerprints/<table>/<year>.json`). `--ttl N` tells the CLI to reuse that partition until the fingerprint is older than `N` days; `--ttl 0` forces a fresh download, while larger TTLs (e.g., `--ttl 30`) keep stable tables from re-pulling unnecessarily.
- Manifest JSON: every partition write appends a record to `data/manifest/manifest.jsonl` capturing table, year, row counts, byte size, and the spec hash. Use `fzr show manifest --table crsp.msf_v2` (or pipe through `jq`/`rg`) to audit what was cached, when, and with which columns.
- Fingerprints-on-demand: `fzr fingerprint --table ... --year ...` regenerates the JSON metadata for a partition after manual edits. Doing so both documents the schema and effectively “touches” the fingerprint so subsequent pulls respect the TTL window you’ve configured.

Tip: Factor outputs align to the CRSP last trading day per month; missing months usually trace back to upstream data gaps.

## Repository Layout
- `src/fzr/cli.py`: entrypoint wiring for the CLI.
- `src/fzr/etl.py`, `store.py`, `utils.py`: shared caching, storage, and helper utilities.
- `src/fzr/plugins/`: factor implementations and shared logic (`ff_shared.py`, `hml_ff93.py`, etc.).
- `src/fzr/templates/`: SQL templates rendered during pulls.
- `tests/`: unit and integration tests for the core package (`pytest fzr/tests -q`).
- `data/`: cached WRDS extracts and factor outputs (ignored by git).
- `pyproject.toml`, `ruff.toml`, `mypy.ini`: tooling and style configuration.

## Developing New Factors
1. Add factor logic in `src/fzr/plugins/`. Start from an existing factor module to reuse the factor grid helpers in `plugins/ff_shared.py`.
2. Register the factor in `src/fzr/factors_core.py` by importing the module inside `_register_builtin_plugins()` and adding a `REGISTRY.setdefault("your_key", module.compute)` entry so discovery works everywhere.
3. Surface the factor key to the CLI by ensuring it’s registered in `src/fzr/factors_core.py`. The `build --factor all_factors` bundle will automatically pick it up.
4. Extend or add tests in `fzr/tests/` covering both the plugin and any SQL generation changes.
5. Document the factor entry point (CLI flags and expected outputs) before shipping it downstream.

**Important:** If a factor needs columns or tables that are not already cached, update both `src/fzr/etl.py` and `src/fzr/cli.py` so the ETL and CLI know how to fetch, cache, and surface that data. Skipping this step means `fzr build` will never pass the required inputs to your plugin.

### Extending the ETL (`src/fzr/etl.py`)
- Add or update a SQL template under `src/fzr/templates/queries/...` that selects the needed columns and respects the `{{ start_date }}`/`{{ end_date }}` window. Reuse the existing Jinja context (`table`, `columns`, `date_col`, `filters`) so `RequestSpec` continues to work.
- Register the template inside `choose_template()` by mapping the WRDS table name to your new `.sql.j2` file and, if necessary, enforcing the expected `join_policy` or `asof_policy`.
- Normalize new columns in `_postprocess()` so downstream code always sees clean dtypes (e.g., coerce WRDS Decimals to floats, parse date columns, and ensure numeric IDs use `Int64`). This keeps factor implementations simple and prevents subtle cache diffs.
- For tables that need bespoke deduplication or caching behavior, extend `_dedupe()` or the logic in `pull()` while keeping the per-year partition contract intact.

### Extending the CLI (`src/fzr/cli.py`)
- Update the warm-start specs in the `build` command. Either append the new columns to an existing `RequestSpec` (e.g., `spec_ccm`) or define a brand-new spec for the table you just wired up in the ETL.
- Make sure `project_or_diagnose()` (or the equivalent cache validation block) runs against the new spec so `--require-cache` surfaces missing partitions/columns early.
- Inside the gap-filling block, add a `pull(spec_new, ...)` call under the shared `wrds_session()` context so the new table is cached alongside CRSP/Compustat when needed.
- Add the resulting DataFrame to `FactorContext(base=...)` with a descriptive key (e.g., `"ccm_linked_fundq"`). Your plugin can then access it via `ctx.base["your_key"]`.
- Test the wiring by running `fzr pull --table <table>` manually and then `fzr build --factor <your_factor>` over a small date range to confirm the CLI exercises the new data path.

### Common example: new CCM columns for a factor
This is the most common “new data” request—adding a fresh field from Compustat to drive a new factor:
1. **Edit the SQL template** (`src/fzr/templates/queries/crsp/ccm_linked_funda.sql.j2` or `.../ccm_linked_fundq.sql.j2`) to select the new Compustat column (cast it to `numeric` and add any helper calculations in the CTEs). Templates already constrain the date window using `{{ start_date }}` / `{{ end_date }}` so you only change the projections.
2. **Update the CLI spec list** in `src/fzr/cli.py` (`ccm_cols` or `fundq_cols`) so the `RequestSpec` knows about the new field. This keeps cache fingerprints and manifests accurate.
3. **Force-refresh the cache** for just the affected years (usually all the years) while iterating: `fzr pull --table ccm_linked_funda --start 1976-07-01 --end 2024-12-31 --date-col jdate_ltrd --cols ... --ttl 0`. Limiting the date window plus `--ttl 0` makes the round-trip fast and ensures you’re testing against the updated SQL.
4. **Verify the metadata** by tailing the manifest or fingerprints: `fzr show manifest --table ccm_linked_funda | tail` or `jq '.schema' data/manifest/fingerprints/ccm_linked_funda/2024.json` to confirm the new column landed.
5. **Run your factor** (`fzr build --factor my_factor --start ... --end ...`) and validate with `fzr/replication_test.ipynb` once satisfied.

## Running Tests
The CI and local checks run `pytest fzr/tests -q`. End-to-end pulls require network access and a WRDS account; the test suite only exercises SQL rendering and local transformations.
