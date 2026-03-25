#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified data loader for your repo layout. No renaming/mapping — column
names are the final factor names. Default paths are wired to your tree:

Repo root
├─ data-replication/cleaned_public   (inputs: *_aligned*.csv)
└─ model-replication/data            (output: factors.csv here)

What it does
------------
- Scans the input directory for files matching `*_aligned*.csv`
- Reads each file as-is (comma-separated), keeps `Date` + all factor columns
- Outer-joins on `Date`, sorts by `Date`
- Drops rows where all factor columns are NaN
- Writes a unified `factors.csv` into model-replication/data by default

Usage
-----
# With defaults (recommended for your tree):
python model-replication/data/data_loader.py

# Or override if needed:
python model-replication/data/data_loader.py \
  --input-dir path/to/cleaned_public \
  --output path/to/factors.csv \
  [--pattern "*_aligned*.csv"]
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

# --- default paths based on this file's location ---
_THIS = Path(__file__).resolve()
DATA_DIR = _THIS.parent                            # model-replication/data
REPO_ROOT = DATA_DIR.parent.parent                 # repo root
DEFAULT_INPUT_DIR = REPO_ROOT / "data-replication" / "cleaned_public"
DEFAULT_OUTPUT = DATA_DIR / "factors.csv"


def read_aligned_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Date" not in df.columns:
        # If ever encountered, assume first column is the date
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    # Parse dates safely, keep only parsable rows
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    return df


essential_cols = ["Date"]


def merge_all(input_dir: Path, output_csv: Path, pattern: str = "*_aligned*.csv") -> pd.DataFrame:
    files = sorted(input_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching '{pattern}' found in {input_dir}")

    merged = None
    print("Merging the following files:\n")
    for f in files:
        df = read_aligned_csv(f)
        factor_cols = [c for c in df.columns if c != "Date"]
        print(f"  - {f.name}: {', '.join(factor_cols) if factor_cols else '(no factor columns)'}")
        merged = df if merged is None else merged.merge(df, on="Date", how="outer")

    merged = merged.sort_values("Date").reset_index(drop=True)
    factor_cols = [c for c in merged.columns if c != "Date"]
    merged = merged.dropna(how="all", subset=factor_cols)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_csv, index=False)

    print(f"\nInput dir : {input_dir}")
    print(f"Output    : {output_csv}")
    print(f"Rows × Col: {len(merged)} × {len(factor_cols)} (factors only)\n")
    return merged


def main():
    ap = argparse.ArgumentParser(description="Merge aligned factor CSVs into factors.csv (simple version)")
    ap.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR,
                    help=f"Directory of *_aligned*.csv (default: {DEFAULT_INPUT_DIR})")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                    help=f"Output CSV (default: {DEFAULT_OUTPUT})")
    ap.add_argument("--pattern", default="*_aligned*.csv",
                    help="Glob pattern to select input files (default: *_aligned*.csv)")
    args = ap.parse_args()

    # Sanity logs
    print("Using defaults wired to your repo layout unless overridden.\n")
    merge_all(args.input_dir, args.output, pattern=args.pattern)


if __name__ == "__main__":
    main()