# Data Dictionary — MF Analytics Project

Source: 10 raw CSVs in `data/raw/`, cleaned into `data/processed/`, loaded into
`bluestock_mf.db` (SQLite star schema: `schema.sql`).

---

## 01_fund_master.csv → dim_fund

| Column | Type | Description |
|---|---|---|
| amfi_code | int | AMFI scheme code. Primary key. |
| fund_house | str | Asset management company name. |
| scheme_name | str | Full scheme name including plan type. |
| category | str | High-level category (Equity / Debt). |
| sub_category | str | SEBI sub-category (Large Cap, Small Cap, Gilt, etc.). |
| plan | str | Regular or Direct plan. |
| launch_date | str (date) | Scheme launch date. |
| benchmark | str | Benchmark index the scheme is measured against. |
| expense_ratio_pct | float | Annual expense ratio, percent. |
| exit_load_pct | float | Exit load, percent. |
| min_sip_amount | int | Minimum SIP investment, INR. |
| min_lumpsum_amount | int | Minimum lumpsum investment, INR. |
| fund_manager | str | Name of the fund manager. |
| risk_category | str | Risk category (Low, Moderate, High, Very High). |
| sebi_category_code | str | SEBI-assigned category code. |

## 02_nav_history.csv → fact_nav

| Column | Type | Description |
|---|---|---|
| amfi_code | int | FK to dim_fund. |
| date | date | NAV date. |
| nav | float | Net Asset Value on that date. Forward-filled for missing days during cleaning. |

## 03_aum_by_fund_house.csv → fact_aum

| Column | Type | Description |
|---|---|---|
| date | date | Reporting date (typically quarter-end). |
| fund_house | str | Asset management company. |
| aum_lakh_crore | float | AUM in lakh crore INR. |
| aum_crore | int | AUM in crore INR. |
| num_schemes | int | Number of schemes offered by the fund house. |

## 04_monthly_sip_inflows.csv (reference table, not yet in star schema)

| Column | Type | Description |
|---|---|---|
| month | str | Month, YYYY-MM. |
| sip_inflow_crore | int | Total SIP inflow that month, crore INR. |
| active_sip_accounts_crore | float | Active SIP accounts, crore. |
| new_sip_accounts_lakh | float | New SIP accounts opened that month, lakh. |
| sip_aum_lakh_crore | float | Total SIP AUM, lakh crore INR. |
| yoy_growth_pct | float | Year-on-year growth, percent (null for first 12 months — no prior-year baseline). |

## 05_category_inflows.csv (reference table)

| Column | Type | Description |
|---|---|---|
| month | str | Month, YYYY-MM. |
| category | str | Fund category (Large Cap, Mid Cap, Small Cap, Flexi Cap, etc.). |
| net_inflow_crore | float | Net inflow for the category that month, crore INR. |

## 06_industry_folio_count.csv (reference table)

| Column | Type | Description |
|---|---|---|
| month | str | Month, YYYY-MM. |
| total_folios_crore | float | Total industry folios, crore. |
| equity_folios_crore | float | Equity fund folios, crore. |
| debt_folios_crore | float | Debt fund folios, crore. |
| hybrid_folios_crore | float | Hybrid fund folios, crore. |
| others_folios_crore | float | Other fund type folios, crore. |

## 07_scheme_performance.csv → fact_performance

| Column | Type | Description |
|---|---|---|
| amfi_code | int | FK to dim_fund. |
| scheme_name | str | Scheme name (redundant with dim_fund, kept for source traceability). |
| fund_house | str | Fund house (redundant with dim_fund). |
| category | str | Category (redundant with dim_fund). |
| plan | str | Plan type. |
| return_1yr_pct | float | 1-year trailing return, percent. |
| return_3yr_pct | float | 3-year annualized return, percent. |
| return_5yr_pct | float | 5-year annualized return, percent. |
| benchmark_3yr_pct | float | Benchmark 3-year return, percent. |
| alpha | float | Jensen's alpha. |
| beta | float | Beta vs benchmark. |
| sharpe_ratio | float | Risk-adjusted return (Sharpe ratio). |
| sortino_ratio | float | Downside risk-adjusted return. |
| std_dev_ann_pct | float | Annualized standard deviation, percent. |
| max_drawdown_pct | float | Maximum drawdown, percent. |
| aum_crore | int | AUM at time of snapshot, crore INR. |
| expense_ratio_pct | float | Expense ratio, percent. |
| morningstar_rating | int | Morningstar star rating (1-5). |
| risk_grade | str | Risk grade label. |
| expense_ratio_flag | str | Added during cleaning: `OK` or `OUT_OF_RANGE` (outside 0.1%-2.5%). |

## 08_investor_transactions.csv → fact_transactions

| Column | Type | Description |
|---|---|---|
| investor_id | str | Unique investor identifier. |
| transaction_date | date | Date of transaction. |
| amfi_code | int | FK to dim_fund. |
| transaction_type | str | Standardized to SIP / Lumpsum / Redemption during cleaning. |
| amount_inr | int | Transaction amount, INR. |
| state | str | Investor's state. |
| city | str | Investor's city. |
| city_tier | str | City tier classification (T30, B30, etc.). |
| age_group | str | Investor age bracket. |
| gender | str | Investor gender. |
| annual_income_lakh | float | Self-reported annual income, lakh INR. |
| payment_mode | str | Payment method used. |
| kyc_status | str | KYC status: Verified / Pending / Rejected. |

## 09_portfolio_holdings.csv (reference table)

| Column | Type | Description |
|---|---|---|
| amfi_code | int | Scheme holding the stock. |
| stock_symbol | str | Stock ticker symbol. |
| stock_name | str | Full company name. |
| sector | str | Sector classification. |
| weight_pct | float | Weight of holding in the portfolio, percent. |
| market_value_cr | float | Market value of the holding, crore INR. |
| current_price_inr | float | Current stock price, INR. |
| portfolio_date | date | Date of the portfolio snapshot. |

## 10_benchmark_indices.csv (reference table)

| Column | Type | Description |
|---|---|---|
| date | date | Trading date. |
| index_name | str | Index name (e.g. NIFTY50). |
| close_value | float | Index closing value. |

---

## dim_date (generated during load, not a source file)

| Column | Type | Description |
|---|---|---|
| date_id | int | Surrogate key. |
| full_date | date | ISO date. |
| year | int | Calendar year. |
| quarter | int | Calendar quarter (1-4). |
| month | int | Calendar month (1-12). |
| day | int | Day of month. |
| day_of_week | str | Day name (Monday, Tuesday, ...). |

## Cleaning Notes

- `nav_history`: dates parsed to datetime, sorted by amfi_code + date, missing
  NAV values forward-filled across a full daily calendar per scheme, duplicate
  (amfi_code, date) rows dropped, rows with nav <= 0 dropped.
- `investor_transactions`: transaction_type values standardized to a fixed
  vocabulary (SIP / Lumpsum / Redemption), rows with amount_inr <= 0 dropped,
  kyc_status values checked against {Verified, Pending, Rejected}.
- `scheme_performance`: all return/ratio columns coerced to numeric, rows with
  expense_ratio_pct outside 0.1%-2.5% flagged (not dropped) via a new
  `expense_ratio_flag` column.
- All other datasets: whitespace-trimmed, exact-duplicate rows dropped.
