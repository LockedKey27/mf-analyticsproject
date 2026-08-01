-- Day 2: SQLite Star Schema for Mutual Fund Analytics
-- dim_fund, dim_date, fact_nav, fact_transactions, fact_performance, fact_aum

PRAGMA foreign_keys = ON;

-- ============================================================
-- DIMENSION: dim_fund
-- One row per scheme, sourced from fund_master.csv
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ============================================================
-- DIMENSION: dim_date
-- One row per calendar date referenced anywhere in the data
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_date (
    date_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    full_date   TEXT NOT NULL UNIQUE,   -- ISO 'YYYY-MM-DD'
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    day         INTEGER NOT NULL,
    day_of_week TEXT NOT NULL
);

-- ============================================================
-- FACT: fact_nav
-- Daily NAV per scheme, sourced from nav_history.csv
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL,
    date_id     INTEGER NOT NULL,
    nav         REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    UNIQUE (amfi_code, date_id)
);

-- ============================================================
-- FACT: fact_transactions
-- One row per investor transaction, sourced from investor_transactions.csv
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id          TEXT NOT NULL,
    amfi_code            INTEGER NOT NULL,
    date_id              INTEGER NOT NULL,
    transaction_type     TEXT NOT NULL,      -- SIP / Lumpsum / Redemption
    amount_inr           INTEGER NOT NULL,
    state                TEXT,
    city                 TEXT,
    city_tier             TEXT,
    age_group             TEXT,
    gender                TEXT,
    annual_income_lakh    REAL,
    payment_mode          TEXT,
    kyc_status            TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- ============================================================
-- FACT: fact_performance
-- One row per scheme snapshot, sourced from scheme_performance.csv
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_performance (
    performance_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    expense_ratio_flag  TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ============================================================
-- FACT: fact_aum
-- AUM by fund house over time, sourced from aum_by_fund_house.csv
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id          INTEGER NOT NULL,
    fund_house       TEXT NOT NULL,
    aum_lakh_crore   REAL,
    aum_crore        INTEGER,
    num_schemes      INTEGER,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- Helpful indexes for common analytical joins
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi_date ON fact_nav (amfi_code, date_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi ON fact_transactions (amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions (date_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_state ON fact_transactions (state);
CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi ON fact_performance (amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_aum_house ON fact_aum (fund_house);
