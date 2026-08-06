
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILES = {
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


def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    df = df.sort_values(["amfi_code", "date"])

    # Forward-fill missing NAV per scheme across a full daily calendar
    filled_frames = []
    for code, grp in df.groupby("amfi_code"):
        grp = grp.set_index("date").sort_index()
        full_range = pd.date_range(grp.index.min(), grp.index.max(), freq="D")
        grp = grp.reindex(full_range)
        grp["amfi_code"] = code
        grp["nav"] = grp["nav"].ffill()
        grp.index.name = "date"
        filled_frames.append(grp.reset_index())

    df = pd.concat(filled_frames, ignore_index=True)
    df = df.rename(columns={"index": "date"})

    before = len(df)
    df = df[df["nav"] > 0]
    dropped = before - len(df)
    if dropped:
        print(f"  nav_history: dropped {dropped} rows with nav <= 0 or unfillable")

    return df[["amfi_code", "date", "nav"]]


TXN_TYPE_MAP = {
    "sip": "SIP",
    "lumpsum": "Lumpsum",
    "lump sum": "Lumpsum",
    "redemption": "Redemption",
    "redeem": "Redemption",
}

VALID_KYC = {"Verified", "Pending", "Rejected"}


def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

    df["transaction_type"] = (
        df["transaction_type"].astype(str).str.strip().str.lower().map(TXN_TYPE_MAP)
    )
    unmapped = df["transaction_type"].isna().sum()
    if unmapped:
        print(f"  investor_transactions: {unmapped} rows had unrecognized transaction_type")

    before = len(df)
    df = df[df["amount_inr"] > 0]
    dropped = before - len(df)
    if dropped:
        print(f"  investor_transactions: dropped {dropped} rows with amount_inr <= 0")

    bad_kyc = ~df["kyc_status"].isin(VALID_KYC)
    if bad_kyc.any():
        print(f"  investor_transactions: {bad_kyc.sum()} rows have unexpected kyc_status values: "
              f"{df.loc[bad_kyc, 'kyc_status'].unique().tolist()}")

    df = df.dropna(subset=["transaction_date", "transaction_type"])
    return df


def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
        "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
        "max_drawdown_pct", "expense_ratio_pct",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    non_numeric = df[numeric_cols].isna().sum().sum()
    if non_numeric:
        print(f"  scheme_performance: {non_numeric} non-numeric values coerced to NaN across return/ratio columns")

    out_of_range = ~df["expense_ratio_pct"].between(0.1, 2.5)
    if out_of_range.any():
        print(f"  scheme_performance: {out_of_range.sum()} rows have expense_ratio_pct outside 0.1-2.5% "
              f"(flagged, not dropped)")
    df["expense_ratio_flag"] = np.where(out_of_range, "OUT_OF_RANGE", "OK")

    return df


def clean_generic(df: pd.DataFrame) -> pd.DataFrame:
    """Light standard cleaning for datasets without bespoke rules."""
    df = df.copy()
    df = df.drop_duplicates()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
    return df


CLEANERS = {
    "nav_history": clean_nav_history,
    "investor_transactions": clean_investor_transactions,
    "scheme_performance": clean_scheme_performance,
}


if __name__ == "__main__":
    for name, filename in RAW_FILES.items():
        path = RAW_DIR / filename
        print(f"Cleaning: {name}")
        df = pd.read_csv(path)

        cleaner = CLEANERS.get(name, clean_generic)
        cleaned = cleaner(df)

        out_path = PROCESSED_DIR / filename
        cleaned.to_csv(out_path, index=False)
        print(f"  -> {out_path}  ({len(cleaned)} rows)\n")

    print("All datasets cleaned and saved to data/processed/")
