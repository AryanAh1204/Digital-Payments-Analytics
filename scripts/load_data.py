"""Creates the transactions table and bulk-loads the raw CSV into Postgres via COPY.
Connects via standard libpq env vars (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)."""
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "PS_20174392719_1491204439457_log.csv"

DDL = """
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    step INTEGER,
    type TEXT,
    amount DOUBLE PRECISION,
    nameOrig TEXT,
    oldbalanceOrg DOUBLE PRECISION,
    newbalanceOrig DOUBLE PRECISION,
    nameDest TEXT,
    oldbalanceDest DOUBLE PRECISION,
    newbalanceDest DOUBLE PRECISION,
    isFraud SMALLINT,
    isFlaggedFraud SMALLINT
);
"""

conn = psycopg2.connect(
    host=os.environ.get("PGHOST", "localhost"),
    port=os.environ.get("PGPORT", "5432"),
    dbname=os.environ.get("PGDATABASE", "digital_payments"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ.get("PGPASSWORD", ""),
)
cur = conn.cursor()
cur.execute(DDL)

with open(DATA) as f:
    cur.copy_expert("COPY transactions FROM STDIN WITH CSV HEADER", f)

# indexes after the bulk load, not before -- much faster this way
cur.execute("CREATE INDEX ON transactions (type);")
cur.execute("CREATE INDEX ON transactions (nameOrig);")
cur.execute("CREATE INDEX ON transactions (nameDest);")
conn.commit()

cur.execute("SELECT COUNT(*) FROM transactions")
count = cur.fetchone()[0]
print(f"loaded {count:,} rows into transactions")
assert count == 6_362_620, f"expected 6,362,620 rows, got {count}"

cur.close()
conn.close()
