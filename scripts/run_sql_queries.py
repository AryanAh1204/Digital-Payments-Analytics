"""Run Phase 1 SQL queries against the transaction CSV via DuckDB, save each to outputs/."""
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "PS_20174392719_1491204439457_log.csv"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW transactions AS SELECT * FROM read_csv_auto('{DATA}')")

sql_text = (ROOT / "scripts" / "queries.sql").read_text()
# split on "-- Q<n>: <name>" markers, name becomes <name>.csv
blocks = re.split(r"--\s*Q\d+:\s*(\w+)[^\n]*\n", sql_text)[1:]  # drop header text before Q1

for name, query in zip(blocks[0::2], blocks[1::2]):
    query = query.strip().rstrip(";")
    result = con.execute(query).fetchdf()
    out_path = OUT / f"{name}.csv"
    result.to_csv(out_path, index=False)
    print(f"{name}: {len(result)} rows -> {out_path.name}")

total_rows = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f"\nsource row count: {total_rows}")
assert total_rows == 6_362_620, f"expected 6,362,620 rows, got {total_rows}"

daily_sum = con.execute(
    "SELECT SUM(txn_count) FROM (SELECT COUNT(*) AS txn_count FROM transactions GROUP BY type, CEIL(step/24.0))"
).fetchone()[0]
assert daily_sum == total_rows, f"daily_volume_by_type sum {daily_sum} != source {total_rows}"
print("sanity check passed: daily_volume_by_type sums to source row count")
