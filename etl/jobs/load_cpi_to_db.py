from __future__ import annotations
import argparse
import csv
import os
from io import StringIO
from pathlib import Path
from typing import List, Tuple

try:
    import psycopg2
except ImportError as e:  # pragma: no cover
    psycopg2 = None


def load_cpi_csv_to_db(csv_path: Path, year: int, dsn: str) -> Tuple[int, int]:
    # Read input and prepare COPY buffer
    buf = StringIO()
    reader = csv.DictReader(open(csv_path, newline="", encoding="utf-8"))
    rows = 0
    for row in reader:
        if int(row["year"]) != year:
            continue
        iso3 = row["iso3"].upper()
        score = float(row["score_0_100"]) if "score_0_100" in row else float(row.get("cpi") or row.get("score"))
        source_url = row.get("source_url") or "https://www.transparency.org/en/cpi"
        # Columns: iso3, year, source, trust_type, raw_value, raw_unit, score_0_100, sample_n, method_notes, source_url
        line = [
            iso3,
            str(year),
            "CPI",
            "cpi",
            "\\N",
            "\\N",
            f"{score}",
            "\\N",
            "\\N",
            source_url,
        ]
        buf.write(",".join(line) + "\n")
        rows += 1

    if rows == 0:
        return 0, 0

    buf.seek(0)
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    try:
        # Upsert behavior: delete existing CPI rows for the year, then copy
        cur.execute("delete from observations where trust_type = 'cpi' and year = %s", (year,))
        cur.copy_expert(
            """
            COPY observations (iso3, year, source, trust_type, raw_value, raw_unit, score_0_100, sample_n, method_notes, source_url)
            FROM STDIN WITH (FORMAT csv)
            """,
            buf,
        )
        conn.commit()
        return rows, cur.rowcount or rows
    finally:
        cur.close()
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True, help="Path to normalized CPI CSV (from etl/jobs/cpi.py)")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--dsn", type=str, default=os.environ.get("POSTGRES_URL"))
    args = ap.parse_args()

    if psycopg2 is None:
        raise SystemExit("psycopg2-binary is not installed. Install etl/requirements.txt.")
    if not args.dsn:
        raise SystemExit("POSTGRES_URL is not set and --dsn not provided.")
    if not args.csv.exists():
        raise SystemExit(f"CSV not found: {args.csv}")

    inserted, _ = load_cpi_csv_to_db(args.csv, args.year, args.dsn)
    print(f"Inserted {inserted} CPI rows for {args.year} into observations.")


if __name__ == "__main__":
    main()

