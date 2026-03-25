import pandas as pd

INPUT_CSV = "openap_monthly_ports.csv"
OUTPUT_CSV = "openap_monthly_factors.csv"

START_DATE = pd.Timestamp("1976-07-30")
END_DATE = pd.Timestamp("2024-12-31")

def parse_mixed_date(val):
    if pd.isna(val):
        return pd.NaT
    s = str(val)

    # Case 1: YYYY-MM-DD
    if "-" in s:
        try:
            return pd.to_datetime(s, format="%Y-%m-%d", errors="raise")
        except Exception:
            return pd.to_datetime(s, errors="coerce")

    # Case 2: yyyymmdd
    try:
        return pd.to_datetime(s, format="%Y%m%d", errors="raise")
    except Exception:
        return pd.to_datetime(s, errors="coerce")


def main():
    # load raw
    df_raw = pd.read_csv(INPUT_CSV)

    # required columns check
    required_cols = {"signalname", "port", "date", "ret"}
    missing_cols = required_cols - set(df_raw.columns)
    if missing_cols:
        raise ValueError(f"Input CSV missing required columns: {missing_cols}")

    # keep LS portfolios only
    df = df_raw[df_raw["port"] == "LS"].copy()

    # parse mixed date formats
    df["Date"] = df["date"].map(parse_mixed_date)

    # clip to global date window
    df = df[(df["Date"] >= START_DATE) & (df["Date"] <= END_DATE)].copy()

    # convert percent to decimal
    df["ret_decimal"] = df["ret"] / 100.0

    # collapse duplicate (Date, signalname) rows by averaging
    dup_ct = (
        df.groupby(["Date", "signalname"])
          .size()
          .reset_index(name="n")
    )
    dups = dup_ct[dup_ct["n"] > 1]
    if not dups.empty:
        print("Warning: duplicate Date/signalname rows detected. Collapsing by mean.")
        df = (
            df.groupby(["Date", "signalname"], as_index=False)["ret_decimal"]
              .mean()
        )
    else:
        df = df[["Date", "signalname", "ret_decimal"]].copy()

    # infer canonical last trading day for each (year, month)
    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month

    last_trading_day_by_month = (
        df.groupby(["year", "month"])["Date"]
          .max()
          .reset_index()
          .sort_values(["year", "month"])
    )

    # canonical month-end timeline
    canonical_dates = last_trading_day_by_month["Date"]
    canonical_dates = canonical_dates[
        (canonical_dates >= START_DATE) & (canonical_dates <= END_DATE)
    ].reset_index(drop=True)

    # pivot wide on exact Date
    wide = df.pivot(index="Date", columns="signalname", values="ret_decimal")

    # align all factors to canonical month-end timeline
    wide = wide.reindex(canonical_dates)

    # sanity: canonical_dates should be strictly increasing unique timestamps
    wide.index.name = "Date"

    # compute missing counts per factor
    missing_counts = wide.isna().sum()

    # identify factors that have ANY missing values
    cols_with_any_missing = missing_counts[missing_counts > 0].index.tolist()

    # identify factors that are fully complete (no NaNs at all)
    cols_complete = missing_counts[missing_counts == 0].index.tolist()

    # report dropped factors and how many dates each is missing
    if cols_with_any_missing:
        dropped_report = (
            missing_counts[missing_counts > 0]
            .sort_values(ascending=False)
        )
        print("Dropping factors with at least one missing date:")
        for fac, cnt in dropped_report.items():
            print(f"  {fac}: {cnt} missing rows")

    # now keep only complete columns
    wide = wide[cols_complete]

    # final sanity check after drop
    n_factors = wide.shape[1]
    print(f"Number of factors (columns) in final output after dropping incomplete factors: {n_factors}")

    # confirm there are now zero NaNs
    if wide.isna().any().any():
        print("Internal check failure: still found NaNs after drop")
    else:
        print("NaN check passed: all remaining factors have full history and no missing values.")

    # final formatting: Date -> yyyymmdd string
    out = wide.reset_index()
    out["Date"] = out["Date"].dt.strftime("%Y%m%d")

    # write csv
    out.to_csv(OUTPUT_CSV, index=False)

    return out


if __name__ == "__main__":
    final_df = main()