"""Run Phase 1 SQL queries against the Postgres `transactions` table, save each to outputs/.
Connects via standard libpq env vars (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)."""
import os
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

host = os.environ.get("PGHOST", "localhost")
port = os.environ.get("PGPORT", "5432")
dbname = os.environ.get("PGDATABASE", "digital_payments")
user = os.environ.get("PGUSER", "postgres")
password = os.environ.get("PGPASSWORD", "")
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")

sql_text = (ROOT / "scripts" / "queries.sql").read_text()
blocks = re.split(r"--\s*Q\d+:\s*(\w+)[^\n]*\n", sql_text)[1:]  # drop header text before Q1

for name, query in zip(blocks[0::2], blocks[1::2]):
    query = query.strip().rstrip(";")
    result = pd.read_sql_query(query, engine)
    out_path = OUT / f"{name}.csv"
    result.to_csv(out_path, index=False)
    print(f"{name}: {len(result)} rows -> {out_path.name}")

with engine.connect() as conn:
    total_rows = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
print(f"\nsource row count: {total_rows}")
assert total_rows == 6_362_620, f"expected 6,362,620 rows, got {total_rows}"

daily_sum = pd.read_sql_query(
    "SELECT SUM(txn_count) AS s FROM "
    "(SELECT COUNT(*) AS txn_count FROM transactions GROUP BY type, CEIL(step / 24.0)) t",
    engine,
)["s"][0]
assert daily_sum == total_rows, f"daily_volume_by_type sum {daily_sum} != source {total_rows}"
print("sanity check passed: daily_volume_by_type sums to source row count")
