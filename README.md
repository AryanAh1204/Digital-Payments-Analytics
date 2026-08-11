# Digital Payments Transaction Analytics

Segmentation, fraud patterns & volume forecasting on 6.36M synthetic mobile payment
transactions. Built as a decision-ready analytics pass — SQL for the questions an ops
team would actually ask, quantile segmentation instead of a clustering pipeline, a linear
forecast instead of a modeling showcase. No fraud classifier: the goal is analysis a team
can act on this week, not a review-cycle model.

## 90-second pitch

**Queried:** transaction volume/value by type and day, fraud rate by type, top senders by
value, a hypothesis test for a TRANSFER→CASH_OUT "mule account" chain, and a balance
reconciliation check — all in SQL against the raw 6.36M-row file via DuckDB.

**Found:** fraud sits entirely in TRANSFER (0.77%) and CASH_OUT (0.18%), and it's sharper
than the type-level rate suggests — 96% of fraud TRANSFERs drain the account to ~0 in one
step. Account value splits 50/50 between two very different high-value tiers (frequent
regulars vs. one-off large senders), which together are half the accounts but 94% of the
value. The "mule chain" hypothesis — commonly assumed for this kind of data — doesn't
hold: TRANSFER and CASH_OUT fraud never share an account in this dataset.

**Would do:** flag near-total balance drains in real time instead of a blunt per-type rate
threshold, and tier monitoring by RFM segment — light on high-frequency regulars, tight on
high-value transactions from otherwise-quiet accounts (the exact profile of every labeled
fraud CASH_OUT here).

Full writeup: [`memo.pdf`](memo.pdf).

## Files

| File | What it is |
|---|---|
| `scripts/queries.sql` | 5 SQL queries: daily volume by type, fraud rate by type, top senders, mule-chain hypothesis test, balance reconciliation |
| `scripts/run_sql_queries.py` | Runs `queries.sql` against the CSV via DuckDB, writes each result to `outputs/` |
| `analysis.ipynb` | RFM segmentation (quantile scoring, 5 business tiers) and 7-day volume forecast |
| `scripts/build_dashboard.py` | Builds `dashboard/PhonePe_Digital_Payments_Dashboard.xlsx` (pivot + 3 charts) from `outputs/` |
| `scripts/build_memo.py` | Builds `memo.pdf` from the same computed numbers |
| `outputs/*.csv` | Query and notebook results (`rfm_segments_detail.csv` excluded from git — see below) |
| `dashboard/PhonePe_Digital_Payments_Dashboard.xlsx` | Pivot table + fraud-rate, forecast, and segment-split charts |
| `memo.pdf` | One-page findings + interventions memo |

## Reproducing

```bash
pip install -r requirements.txt
# place the raw CSV at data/PS_20174392719_1491204439457_log.csv
# (not included in this repo -- 493MB, see Data below)

python scripts/run_sql_queries.py
jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
python scripts/build_dashboard.py
python scripts/build_memo.py
```

## Method notes

- **Segmentation:** quantile RFM (recency/frequency/monetary, 4-way quantile scoring into 5
  labeled tiers), not k-means. Faster, interpretable without a training step, and the tier
  boundaries are business-readable on their own.
- **Forecast:** 7-day linear trend, not ARIMA/Prophet. Full-history daily volume has a level
  shift roughly two-thirds through the window (early days run 5-14x later days) — fitting on
  the recent 7-day window instead of the whole history avoids extrapolating the early
  high-volume trend into a negative forecast. Forecast is floored at 0.
- **Scale:** every aggregation runs as a DuckDB `GROUP BY` directly against the CSV on disk.
  The full 6.36M-row raw table is never loaded into pandas — only the small, already-aggregated
  results are (per-account RFM aggregates, daily totals) — so this runs on an 8GB-RAM laptop
  without subsampling the data.

## Data caveats

- **No mule-chain link.** Checked whether TRANSFER and CASH_OUT fraud are connected by a
  shared account (`nameDest` of the transfer = `nameOrig` of the cash-out, a common assumption
  about this kind of data). They aren't: 0 accounts appear in both, and only 3 of 8,213 fraud
  rows share any account link at all, filtered or not. Reporting the negative result since it
  runs against a common assumption.
- **Merchant accounts** (`nameOrig`/`nameDest` starting `M`) carry a zero-balance placeholder
  for `oldbalanceDest`/`newbalanceDest` — a data artifact, excluded from balance logic rather
  than treated as a signal.
- **Balance reconciliation** (`oldbalanceOrg - amount` vs `newbalanceOrig`) mismatches on
  79.8% of all rows — a characteristic of how this dataset was generated, not a fraud
  indicator on its own.
- **`rfm_segments_detail.csv`** (one row per account, ~6.35M rows / 337MB) is excluded from
  git for size — regenerate it via `analysis.ipynb`. `segment_summary.csv` (the aggregated
  version) is included.

## Data

Synthetic mobile payment transaction dataset (Kaggle), 6,362,620 rows. Not included in this
repo due to size (493MB) and redistribution terms — download it separately and place it at
`data/PS_20174392719_1491204439457_log.csv` to reproduce.
