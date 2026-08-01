"""
Day 2 - Load cleaned data into SQLite star schema (bluestock_mf.db)
Builds dim_date from all dates seen across the data, loads dim_fund,
then loads the fact tables with date_id foreign keys resolved.
Verifies row counts against source CSVs at the end.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

PROCESSED_DIR = Path("data/processed")
DB_PATH = "bluestock_mf.db"
SCHEMA_PATH = Path("schema.sql")

engine = create_engine(f"sqlite:///{DB_PATH}")


def apply_schema():
    with engine.begin() as conn:
        sql_script = SCHEMA_PATH.read_text()
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print(f"Schema applied to {DB_PATH}")


def build_dim_date(all_dates: pd.Series) -> pd.DataFrame:
    dates = pd.to_datetime(all_dates.dropna().unique())
    dim = pd.DataFrame({"full_date": sorted(dates)})
    dim["full_date"] = dim["full_date"].dt.strftime("%Y-%m-%d")
    parsed = pd.to_datetime(dim["full_date"])
    dim["year"] = parsed.dt.year
    dim["quarter"] = parsed.dt.quarter
    dim["month"] = parsed.dt.month
    dim["day"] = parsed.dt.day
    dim["day_of_week"] = parsed.dt.day_name()
    return dim


def load_dim_fund():
    df = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
    cols = [
        "amfi_code", "fund_house", "scheme_name", "category", "sub_category",
        "plan", "launch_date", "benchmark", "expense_ratio_pct", "exit_load_pct",
        "min_sip_amount", "min_lumpsum_amount", "fund_manager", "risk_category",
        "sebi_category_code",
    ]
    df[cols].to_sql("dim_fund", engine, if_exists="append", index=False)
    print(f"  dim_fund: {len(df)} rows loaded")
    return df


def load_dim_date():
    nav = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv")
    txn = pd.read_csv(PROCESSED_DIR / "08_investor_transactions.csv")
    aum = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv")

    all_dates = pd.concat([
        pd.to_datetime(nav["date"], errors="coerce"),
        pd.to_datetime(txn["transaction_date"], errors="coerce"),
        pd.to_datetime(aum["date"], errors="coerce"),
    ])
    dim_date = build_dim_date(all_dates)
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"  dim_date: {len(dim_date)} rows loaded")

    date_lookup = pd.read_sql("SELECT date_id, full_date FROM dim_date", engine)
    return date_lookup


def load_fact_nav(date_lookup: pd.DataFrame):
    df = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.merge(date_lookup, left_on="date", right_on="full_date", how="left")
    df = df[["amfi_code", "date_id", "nav"]].dropna()
    df.to_sql("fact_nav", engine, if_exists="append", index=False)
    print(f"  fact_nav: {len(df)} rows loaded")


def load_fact_transactions(date_lookup: pd.DataFrame):
    df = pd.read_csv(PROCESSED_DIR / "08_investor_transactions.csv")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.merge(date_lookup, left_on="transaction_date", right_on="full_date", how="left")
    cols = [
        "investor_id", "amfi_code", "date_id", "transaction_type", "amount_inr",
        "state", "city", "city_tier", "age_group", "gender", "annual_income_lakh",
        "payment_mode", "kyc_status",
    ]
    df = df[cols].dropna(subset=["date_id"])
    df.to_sql("fact_transactions", engine, if_exists="append", index=False)
    print(f"  fact_transactions: {len(df)} rows loaded")


def load_fact_performance():
    df = pd.read_csv(PROCESSED_DIR / "07_scheme_performance.csv")
    cols = [
        "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade", "expense_ratio_flag",
    ]
    df[cols].to_sql("fact_performance", engine, if_exists="append", index=False)
    print(f"  fact_performance: {len(df)} rows loaded")


def load_fact_aum(date_lookup: pd.DataFrame):
    df = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.merge(date_lookup, left_on="date", right_on="full_date", how="left")
    cols = ["date_id", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"]
    df = df[cols].dropna(subset=["date_id"])
    df.to_sql("fact_aum", engine, if_exists="append", index=False)
    print(f"  fact_aum: {len(df)} rows loaded")


def verify_row_counts():
    print("\nRow count verification (source CSV vs loaded table):")
    checks = [
        ("01_fund_master.csv", "dim_fund"),
        ("02_nav_history.csv", "fact_nav"),
        ("08_investor_transactions.csv", "fact_transactions"),
        ("07_scheme_performance.csv", "fact_performance"),
        ("03_aum_by_fund_house.csv", "fact_aum"),
    ]
    for csv_name, table in checks:
        src_count = len(pd.read_csv(PROCESSED_DIR / csv_name))
        db_count = pd.read_sql(f"SELECT COUNT(*) AS n FROM {table}", engine)["n"].iloc[0]
        status = "OK" if src_count == db_count else "MISMATCH"
        print(f"  {table}: source={src_count}, db={db_count}  [{status}]")


if __name__ == "__main__":
    apply_schema()
    load_dim_fund()
    date_lookup = load_dim_date()
    load_fact_nav(date_lookup)
    load_fact_transactions(date_lookup)
    load_fact_performance()
    load_fact_aum(date_lookup)
    verify_row_counts()
    print(f"\nDone. Database written to {DB_PATH}")
