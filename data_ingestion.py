"""
Day 1 - Data Ingestion
Loads all 10 raw CSVs, prints shape/dtypes/head, explores fund_master,
and validates AMFI scheme codes against nav_history.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")

FILES = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum_by_fund_house": "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "industry_folio_count": "06_industry_folio_count.csv",
    "scheme_performance": "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings": "09_portfolio_holdings.csv",
    "benchmark_indices": "10_benchmark_indices.csv",
}


def load_all_datasets():
    """Load every CSV into a dict of DataFrames and print a quick profile of each."""
    dfs = {}
    for name, filename in FILES.items():
        path = RAW_DIR / filename
        print("=" * 80)
        print(f"Loading: {name}  ({filename})")
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"  !! Failed to load {filename}: {e}")
            continue

        dfs[name] = df
        print(f"Shape: {df.shape}")
        print("\nDtypes:")
        print(df.dtypes)
        print("\nHead:")
        print(df.head())

        # quick anomaly checks
        null_cols = df.columns[df.isnull().any()].tolist()
        if null_cols:
            print(f"\n  Columns with nulls: {null_cols}")
        dup_count = df.duplicated().sum()
        if dup_count:
            print(f"  Duplicate rows: {dup_count}")
        print()

    return dfs


def explore_fund_master(fund_master: pd.DataFrame):
    """Print unique fund houses, categories, sub-categories, risk grades."""
    print("=" * 80)
    print("FUND MASTER EXPLORATION")
    print("Columns:", list(fund_master.columns))

    # NOTE: adjust these column names to match your actual fund_master.csv headers
    for col in ["fund_house", "category", "sub_category", "risk_category"]:
        if col in fund_master.columns:
            uniques = fund_master[col].dropna().unique()
            print(f"\n{col} ({len(uniques)} unique):")
            print(sorted(uniques.tolist()))
        else:
            print(f"\n  Column '{col}' not found — check actual column name.")


def validate_amfi_codes(fund_master: pd.DataFrame, nav_history: pd.DataFrame):
    """Confirm every AMFI code in fund_master exists in nav_history. Print a summary."""
    print("=" * 80)
    print("AMFI CODE VALIDATION")

    # NOTE: adjust 'amfi_code' below if your actual column is named differently
    # (e.g. 'scheme_code', 'code')
    candidate_names = ["amfi_code", "scheme_code", "code"]

    fm_col = next((c for c in candidate_names if c in fund_master.columns), None)
    nh_col = next((c for c in candidate_names if c in nav_history.columns), None)

    if not fm_col or not nh_col:
        print("  Could not auto-detect the AMFI code column in one or both files.")
        print(f"  fund_master columns: {list(fund_master.columns)}")
        print(f"  nav_history columns: {list(nav_history.columns)}")
        return

    fm_codes = set(fund_master[fm_col].dropna().unique())
    nh_codes = set(nav_history[nh_col].dropna().unique())

    missing = fm_codes - nh_codes
    print(f"Total codes in fund_master: {len(fm_codes)}")
    print(f"Total codes in nav_history: {len(nh_codes)}")
    print(f"Codes in fund_master missing from nav_history: {len(missing)}")
    if missing:
        print(f"  Missing codes (sample): {list(missing)[:20]}")

    # Data quality summary
    print("\nDATA QUALITY SUMMARY")
    coverage_pct = 100 * (len(fm_codes) - len(missing)) / len(fm_codes) if fm_codes else 0
    print(f"  NAV history coverage of fund_master schemes: {coverage_pct:.2f}%")
    print(f"  {'All fund_master codes have NAV history.' if not missing else 'Some fund_master codes lack NAV history — investigate before joins.'}")


if __name__ == "__main__":
    dfs = load_all_datasets()

    if "fund_master" in dfs:
        explore_fund_master(dfs["fund_master"])

    if "fund_master" in dfs and "nav_history" in dfs:
        validate_amfi_codes(dfs["fund_master"], dfs["nav_history"])
