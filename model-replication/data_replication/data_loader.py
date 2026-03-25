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
DEFAULT_WRDS_FACTORS = REPO_ROOT / "fzr" / "out_factors" / "wrds_factors.csv"
END_DATE = "2017-12-29"


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


def merge_all(
    input_dir: Path,
    output_csv: Path,
    pattern: str = "*_aligned*.csv",
    wrds_path: Path | None = DEFAULT_WRDS_FACTORS,
    end_date: str | None = None, 
) -> pd.DataFrame:
    files = sorted(input_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching '{pattern}' found in {input_dir}")

    merged: pd.DataFrame | None = None
    print("Merging the following files from cleaned_public:\n")
    for f in files:
        df = read_aligned_csv(f)
        factor_cols = [c for c in df.columns if c != "Date"]
        print(f"  - {f.name}: {', '.join(factor_cols) if factor_cols else '(no factor columns)'}")
        merged = df if merged is None else merged.merge(df, on="Date", how="outer")

    merged = merged.sort_values("Date").reset_index(drop=True)

    # --- bring in WRDS factors, keep WRDS when there are duplicates ---
    if wrds_path is not None:
        if wrds_path.exists():
            print(f"\nAlso merging WRDS factors from: {wrds_path}")
            wrds_df = read_aligned_csv(wrds_path)
            wrds_factor_cols = [c for c in wrds_df.columns if c != "Date"]
            print(f"  WRDS columns: {', '.join(wrds_factor_cols)}")

            # Use WRDS as primary: where both have values, keep WRDS
            merged_idx = merged.set_index("Date")
            wrds_idx = wrds_df.set_index("Date")
            merged = wrds_idx.combine_first(merged_idx).reset_index()
        else:
            print(f"\n[warning] WRDS factors file not found at {wrds_path}, skipping.")

    merged = merged.sort_values("Date").reset_index(drop=True)
    
    if end_date is not None:
        cutoff = pd.to_datetime(end_date)
        merged = merged[merged["Date"] <= cutoff]
        print(f"Applying end-date cutoff at {cutoff.date()} -> {len(merged)} rows left.")
    
    factor_cols = [c for c in merged.columns if c != "Date"]
    merged = merged.dropna(how="all", subset=factor_cols)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_csv, index=False)

    print(f"\nInput dir : {input_dir}")
    if wrds_path is not None:
        print(f"WRDS file : {wrds_path} (exists: {wrds_path.exists()})")
    print(f"Output    : {output_csv}")
    print(f"Rows × Col: {len(merged)} × {len(factor_cols)} (factors only)\n")
    return merged


def main():
    ap = argparse.ArgumentParser(
        description="Merge aligned factor CSVs and WRDS factors into factors.csv"
    )
    ap.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory of *_aligned*.csv (default: {DEFAULT_INPUT_DIR})",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV (default: {DEFAULT_OUTPUT})",
    )
    ap.add_argument(
        "--pattern",
        default="*_aligned*.csv",
        help="Glob pattern to select input files (default: *_aligned*.csv)",
    )
    ap.add_argument(
        "--wrds-path",
        type=Path,
        default=DEFAULT_WRDS_FACTORS,
        help=f"Path to wrds_factors.csv (default: {DEFAULT_WRDS_FACTORS})",
    )
    ap.add_argument(
        "--end-date",
        type=str,
        default=END_DATE,
        help="Cutoff date in YYYY-MM-DD format; rows after this date will be dropped",
    ) 
    args = ap.parse_args()

    # Sanity logs
    print("Using defaults wired to your repo layout unless overridden.\n")
    merge_all(args.input_dir, args.output, pattern=args.pattern, wrds_path=args.wrds_path, end_date=args.end_date,)


if __name__ == "__main__":
    main()
