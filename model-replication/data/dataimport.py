"""
=========================================================================
DATA IMPORT SCRIPT
=========================================================================

DEPENDENCIES:
  - pandas (for reading CSV files)
  - numpy (for numerical operations)
  - Required data files in same directory:
      * factors.csv (factor returns and risk-free rate)
      * port_5x5.csv, port_3x2.csv (portfolio returns)
      * port202.csv (202 test portfolios)
      * summary.csv (factor metadata)
      * port_5x5_id.csv, port_3x2_id.csv (portfolio identifiers)

WHAT THIS FILE DOES:
  This script imports all necessary data files for the Factor Zoo analysis.
  It loads factor returns, risk-free rates, and various sets of test 
  portfolios (3x2 bivariate, 5x5 bivariate, and 202 industry portfolios).
  The script computes excess returns by subtracting the risk-free rate and
  creates filtered portfolio sets (port_3x2b, port_5x5b) that only include
  portfolios with a minimum number of stocks (default: 10 stocks).
  It also loads factor metadata including publication years and descriptions.

=========================================================================
"""

import numpy as np
import pandas as pd
import os

import os
import numpy as np
import pandas as pd


def load_data(data_dir=None):
    """
    Load all data files for Factor Zoo analysis.

    Parameters
    ----------
    data_dir : str, optional
        Directory containing data files. If None, uses current directory.

    Returns
    -------
    dict
        Dictionary containing all loaded data arrays and metadata.
    """
    if data_dir is None:
        data_dir = os.path.dirname(os.path.abspath(__file__))

    # ------------------------------------------------------------
    # 1. Load factors.csv and extract factor names (column names)
    # ------------------------------------------------------------
    allfactors = pd.read_csv(os.path.join(data_dir, "factors.csv"))

    # Assumed structure:
    #   col 0: Date
    #   col 1: RF (risk-free rate)
    #   col 2+: factor returns
    date = allfactors.iloc[:, 0].values
    rf = allfactors.iloc[:, 1].values
    factors = allfactors.iloc[:, 2:].values

    # Factor column names aligned with "factors" array
    factor_cols = list(allfactors.columns[2:])

    L = len(date)
    P = factors.shape[1]

    if P != len(factor_cols):
        print(
            f"[Warning] Number of factor columns ({P}) does not match "
            f"number of factor names ({len(factor_cols)})."
        )

    # Optionally drop RF from factor columns if it accidentally appears there
    if "RF" in factor_cols:
        print("[Info] Dropping 'RF' from factor list (treated as risk-free rate, not a factor).")
        keep_mask = [c != "RF" for c in factor_cols]
        factors = factors[:, keep_mask]
        factor_cols = [c for c in factor_cols if c != "RF"]
        P = factors.shape[1]

    # ------------------------------------------------------------
    # 2. Load test portfolios and compute excess returns
    # ------------------------------------------------------------
    port_5x5 = pd.read_csv(os.path.join(data_dir, "port_5x5.csv"), header=None)
    port_5x5 = port_5x5.iloc[:, 1:].values - rf[:, np.newaxis]

    port_3x2 = pd.read_csv(os.path.join(data_dir, "port_3x2.csv"), header=None)
    port_3x2 = port_3x2.iloc[:, 1:].values - rf[:, np.newaxis]

    port_202 = pd.read_csv(os.path.join(data_dir, "port202.csv"), header=None)
    port_202 = port_202.iloc[:, 1:].values / 100.0 - rf[:, np.newaxis]

    # ------------------------------------------------------------
    # 3. Load summary.csv and align order to factors.csv
    # ------------------------------------------------------------
    summary_raw = pd.read_csv(os.path.join(data_dir, "summary.csv"), index_col=0)

    summary_names = summary_raw.index.tolist()

    # Identify mismatches for debugging
    missing_in_summary = [f for f in factor_cols if f not in summary_names]
    extra_in_summary = [s for s in summary_names if s not in factor_cols]

    if missing_in_summary:
        print("[Warning] The following factors exist in factors.csv but NOT in summary.csv:")
        print(" ", missing_in_summary)

    if extra_in_summary:
        print("[Info] The following entries exist in summary.csv but NOT in factors.csv:")
        print(" ", extra_in_summary)

    # Align summary order with factor column order
    summary = summary_raw.reindex(factor_cols)

    # ------------------------------------------------------------
    # 4. Build metadata arrays: names, descriptions, years
    # ------------------------------------------------------------
    factorname = summary.index.tolist()

    # Choose the description column if available
    if "Descpription" in summary.columns:
        desc_series = summary["Descpription"]
    elif "Description" in summary.columns:
        desc_series = summary["Description"]
    else:
        # No description column: just use the short names
        desc_series = pd.Series(summary.index, index=summary.index)

    # Build full factor names, falling back to short name when description is missing
    factorname_full = []
    for i, short_name in enumerate(factorname):
        desc_val = desc_series.iloc[i] if i < len(desc_series) else np.nan
        if pd.isna(desc_val):
            factorname_full.append(short_name)
        else:
            factorname_full.append(desc_val)

    # Publication years and end years (may contain NaNs)
    year_pub = pd.to_numeric(summary.get("Year"), errors="coerce").values
    year_end = pd.to_numeric(summary.get("Year_end"), errors="coerce").values

    # ------------------------------------------------------------
    # 5. Load portfolio ID files and build filtered 3x2 and 5x5 sets
    # ------------------------------------------------------------
    port_5x5_id = pd.read_csv(os.path.join(data_dir, "port_5x5_id.csv"))
    port_3x2_id = pd.read_csv(os.path.join(data_dir, "port_3x2_id.csv"))

    kk = 10  # minimum number of stocks per portfolio

    # Filter 3x2 portfolios
    include_3x2 = np.where(port_3x2_id["min_stk6"].values >= kk)[0]
    port_3x2b_list = []

    for i in range(P):
        if i in include_3x2:
            start = i * 6
            end = (i + 1) * 6
            port_3x2b_list.append(port_3x2[:, start:end])

    if port_3x2b_list:
        port_3x2b = np.hstack(port_3x2b_list)
    else:
        port_3x2b = np.zeros((L, 0))

    # Filter 5x5 portfolios
    include_5x5 = np.where(port_5x5_id["min_stk"].values >= kk)[0]
    port_5x5b_list = []

    for i in range(P):
        if i in include_5x5:
            start = i * 25
            end = (i + 1) * 25
            port_5x5b_list.append(port_5x5[:, start:end])

    if port_5x5b_list:
        port_5x5b = np.hstack(port_5x5b_list)
    else:
        port_5x5b = np.zeros((L, 0))

    # ------------------------------------------------------------
    # 6. Return everything
    # ------------------------------------------------------------
    return {
        "date": date,
        "rf": rf,
        "factors": factors,
        "L": L,
        "P": P,
        "port_5x5": port_5x5,
        "port_3x2": port_3x2,
        "port_202": port_202,
        "port_5x5b": port_5x5b,
        "port_3x2b": port_3x2b,
        "summary": summary,
        "factorname": factorname,
        "factorname_full": factorname_full,
        "year_pub": year_pub,
        "year_end": year_end,
        "port_5x5_id": port_5x5_id,
        "port_3x2_id": port_3x2_id,
        "include_3x2": include_3x2,
        "include_5x5": include_5x5,
    }


if __name__ == "__main__":
    # Test data loading
    data = load_data()
    print(f"Loaded {data['P']} factors over {data['L']} time periods")
    print(f"port_3x2b shape: {data['port_3x2b'].shape}")
    print(f"port_5x5b shape: {data['port_5x5b'].shape}")

