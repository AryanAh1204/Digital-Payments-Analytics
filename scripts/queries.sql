-- Digital Payments Transaction Analytics — Phase 1 SQL
-- Run against transactions view (see scripts/run_sql_queries.py). DuckDB dialect.

-- Q1: daily_volume_by_type
SELECT
    type,
    CEIL(step / 24.0) AS day,
    COUNT(*) AS txn_count,
    SUM(amount) AS txn_value
FROM transactions
GROUP BY type, day
ORDER BY day, type;

-- Q2: fraud_rate_by_type
SELECT
    type,
    COUNT(*) AS total_txns,
    SUM(isFraud) AS fraud_txns,
    ROUND(100.0 * SUM(isFraud) / COUNT(*), 4) AS fraud_rate_pct
FROM transactions
GROUP BY type
ORDER BY fraud_rate_pct DESC;

-- Q3: top_senders
SELECT nameOrig, COUNT(*) AS txn_count, SUM(amount) AS total_sent
FROM transactions
GROUP BY nameOrig
ORDER BY total_sent DESC
LIMIT 20;

-- Q4: fraud_chains (TRANSFER -> CASH_OUT mule pattern)
SELECT
    t.nameOrig AS transfer_from,
    t.nameDest AS mule_account,
    t.amount AS transfer_amount,
    t.step AS transfer_step,
    c.amount AS cashout_amount,
    c.step AS cashout_step,
    (c.step - t.step) AS step_gap
FROM transactions t
JOIN transactions c
  ON t.nameDest = c.nameOrig
  AND t.type = 'TRANSFER'
  AND c.type = 'CASH_OUT'
  AND c.step BETWEEN t.step AND t.step + 3
  AND ABS(c.amount - t.amount) / t.amount < 0.05
ORDER BY step_gap ASC
LIMIT 1000;

-- Q5: balance_check
SELECT COUNT(*) AS mismatched_rows,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions), 2) AS pct_of_total
FROM transactions
WHERE ABS(newbalanceOrig - (oldbalanceOrg - amount)) > 0.01;
