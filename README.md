# Digital Payments Transaction Analytics

Segmentation, fraud patterns, and volume forecasting on 6.36M synthetic mobile payment
transactions. SQL for the questions an ops team would actually ask, quantile segmentation
instead of a clustering pipeline, a linear forecast instead of an overbuilt one. No fraud
classifier here either; the point was analysis a team could act on this week, not a model
that needs a review cycle.

## 90-second pitch

I queried transaction volume and value by type and day, fraud rate by type, top senders by
value, a test of whether TRANSFER and CASH_OUT fraud are linked through a shared "mule"
account, and a balance reconciliation check, all in SQL against the raw 6.36M-row file via
DuckDB.

Fraud sits entirely in TRANSFER (0.77%) and CASH_OUT (0.18%), and it's sharper than the
type-level rate suggests: 96% of fraud TRANSFERs drain the account to about zero in one
step. Account value splits close to evenly between two very different high-value tiers,
frequent regulars and one-off large senders, which together are half the accounts but 94%
of the value. The mule-chain hypothesis, which gets assumed a lot for this kind of data,
doesn't hold here. TRANSFER and CASH_OUT fraud never share an account.

I'd flag near-total balance drains in real time instead of using a blunt per-type rate
threshold, and tier monitoring by RFM segment: light on high-frequency regulars, tight on
high-value transactions from otherwise quiet accounts, which matches every labeled fraud
CASH_OUT in this data.

Full writeup: [`memo.pdf`](memo.pdf).

## Files

| File | What it is |
|---|---|
| `scripts/queries.sql` | 5 SQL queries: daily volume by type, fraud rate by type, top senders, mule-chain hypothesis test, balance reconciliation |
| `scripts/run_sql_queries.py` | Runs `queries.sql` against the CSV via DuckDB, writes each result to `outputs/` |
| `scripts/make_data_sample.py` | Writes `data/sample_transactions.csv`, a 100k-row random sample of the full file |
| `analysis.ipynb` | RFM segmentation (quantile scoring, 5 business tiers) and 7-day volume forecast |
| `scripts/build_dashboard.py` | Builds `dashboard/PhonePe_Digital_Payments_Dashboard.xlsx` (pivot + 3 charts) from `outputs/` |
| `scripts/build_memo.py` | Builds `memo.pdf` from the same computed numbers |
| `outputs/*.csv` | Query and notebook results (`rfm_segments_detail.csv` isn't in git; see below) |
| `dashboard/PhonePe_Digital_Payments_Dashboard.xlsx` | Pivot table plus fraud-rate, forecast, and segment-split charts |
| `memo.pdf` | One-page findings and interventions memo |

## Reproducing

```bash
pip install -r requirements.txt
# place the full raw CSV at data/PS_20174392719_1491204439457_log.csv
# not included in this repo, see Data below (data/sample_transactions.csv is a
# 100k-row sample for a quick look, not enough to reproduce the numbers below)

python scripts/run_sql_queries.py
jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
python scripts/build_dashboard.py
python scripts/build_memo.py
```

## Method notes

Segmentation uses quantile RFM (recency, frequency, monetary, scored into 4-way quantiles
and rolled up into 5 labeled tiers) rather than k-means. It's faster, doesn't need a
training step, and the tier boundaries are readable on their own without a model to
explain.

The forecast is a 7-day linear trend, not ARIMA or Prophet. Full-history daily volume has a
level shift about two-thirds through the window (the early days run 5 to 14 times higher
than the later ones), so fitting on the whole history drags the slope negative. Fitting on
the recent 7-day window instead avoids extrapolating that early high-volume trend into a
negative forecast. The forecast is also floored at zero.

Every aggregation runs as a DuckDB `GROUP BY` directly against the CSV on disk. The full
6.36M-row raw table never gets loaded into pandas; only the small, already-aggregated
results do (per-account RFM aggregates, daily totals). That's what lets this run on an
8GB-RAM laptop without subsampling the data.

## Data caveats

I checked whether TRANSFER and CASH_OUT fraud are connected by a shared account (the
`nameDest` of the transfer matching the `nameOrig` of a later cash-out), since that's a
common assumption about this kind of data. They aren't linked: zero accounts appear on
both sides, and only 3 of 8,213 fraud rows share any account link at all, with no filtering.
Worth reporting since it goes against the usual assumption.

Merchant accounts (`nameOrig` or `nameDest` starting with `M`) carry a zero-balance
placeholder for `oldbalanceDest` and `newbalanceDest`. That's a data artifact, so it's
excluded from balance logic instead of treated as a signal.

The balance reconciliation check (`oldbalanceOrg - amount` versus `newbalanceOrig`)
mismatches on 79.8% of all rows. That's a characteristic of how this dataset was
generated, not a fraud indicator by itself.

`rfm_segments_detail.csv` (one row per account, about 6.35M rows, 337MB) isn't checked
into git because of size; regenerate it via `analysis.ipynb`. `segment_summary.csv`, the
aggregated version, is included.

## Data

Synthetic mobile payment transaction dataset from Kaggle, 6,362,620 rows. The full file
(493MB) isn't in this repo because of size and redistribution terms; download it
separately and place it at `data/PS_20174392719_1491204439457_log.csv` to reproduce.
`data/sample_transactions.csv` is a random 100k-row sample (about 7.4MB, made with
`scripts/make_data_sample.py`) checked into the repo so the data has a shape you can look
at without the download. It's a random sample, not a stratified one, so rare fraud rows
are thin in it; it's for a quick look at the schema, not for reproducing the numbers
above.
