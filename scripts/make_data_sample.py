"""Writes a random 100k-row sample of the raw CSV to data/sample_transactions.csv (~8MB,
under GitHub's 25MB web-upload cap) so the repo has real data to open without the 493MB
full file. Full analysis outputs are computed from the full file, not this sample."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "PS_20174392719_1491204439457_log.csv"
SAMPLE = ROOT / "data" / "sample_transactions.csv"

con = duckdb.connect()
con.execute(f"""
    COPY (
        SELECT * FROM read_csv_auto('{DATA}')
        ORDER BY random()
        LIMIT 100000
    ) TO '{SAMPLE}' (HEADER, DELIMITER ',')
""")
print(f"wrote {SAMPLE}")
