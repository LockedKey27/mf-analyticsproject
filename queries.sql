-- Day 2: Analytical SQL Queries
-- Run against bluestock_mf.db

-- ============================================================
-- 1. Top 5 funds by AUM
-- ============================================================
SELECT f.scheme_name, f.fund_house, p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- ============================================================
-- 2. Average NAV per month, per scheme
-- ============================================================
SELECT f.scheme_name, d.year, d.month, ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON d.date_id = n.date_id
JOIN dim_fund f ON f.amfi_code = n.amfi_code
GROUP BY f.scheme_name, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month;

-- ============================================================
-- 3. SIP YoY growth (from monthly_sip_inflows.csv — load separately
--    or via a supplementary table if not part of the star schema)
--    Placeholder using fact_transactions as a proxy: monthly SIP volume
-- ============================================================
SELECT d.year, d.month, SUM(t.amount_inr) AS total_sip_inr
FROM fact_transactions t
JOIN dim_date d ON d.date_id = t.date_id
WHERE t.transaction_type = 'SIP'
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- ============================================================
-- 4. Transactions by state
-- ============================================================
SELECT state, COUNT(*) AS transaction_count, SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- ============================================================
-- 5. Funds with expense_ratio < 1%
-- ============================================================
SELECT scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- ============================================================
-- 6. Best performing funds by 3-year return
-- ============================================================
SELECT f.scheme_name, f.fund_house, p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.return_3yr_pct DESC
LIMIT 10;

-- ============================================================
-- 7. Fund count by category and sub-category
-- ============================================================
SELECT category, sub_category, COUNT(*) AS fund_count
FROM dim_fund
GROUP BY category, sub_category
ORDER BY fund_count DESC;

-- ============================================================
-- 8. Investor demographics: transaction volume by age_group and gender
-- ============================================================
SELECT age_group, gender, COUNT(*) AS transaction_count, SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY total_amount_inr DESC;

-- ============================================================
-- 9. Funds with highest Sharpe ratio (risk-adjusted return)
-- ============================================================
SELECT f.scheme_name, f.fund_house, p.sharpe_ratio, p.risk_grade
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- ============================================================
-- 10. Monthly transaction volume trend (all transaction types)
-- ============================================================
SELECT d.year, d.month, t.transaction_type, COUNT(*) AS txn_count, SUM(t.amount_inr) AS total_amount_inr
FROM fact_transactions t
JOIN dim_date d ON d.date_id = t.date_id
GROUP BY d.year, d.month, t.transaction_type
ORDER BY d.year, d.month, t.transaction_type;
