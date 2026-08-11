"""Writes a random 100k-row sample of the transactions table to data/sample_transactions.csv
(~8MB, under GitHub's 25MB web-upload cap) so the repo has real data to open without the
493MB full file. Full analysis outputs are computed from the full table, not this sample.
Connects via standard libpq env vars (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)."""
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "sample_transactions.csv"

conn = psycopg2.connect(
    host=os.environ.get("PGHOST", "localhost"),
    port=os.environ.get("PGPORT", "5432"),
    dbname=os.environ.get("PGDATABASE", "digital_payments"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ.get("PGPASSWORD", ""),
)
cur = conn.cursor()
with open(SAMPLE, "w") as f:
    cur.copy_expert(
        "COPY (SELECT * FROM transactions ORDER BY random() LIMIT 100000) "
        "TO STDOUT WITH CSV HEADER",
        f,
    )
cur.close()
conn.close()
print(f"wrote {SAMPLE}")
