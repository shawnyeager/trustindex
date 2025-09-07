#!/usr/bin/env python3
import os
import sys
from datetime import datetime

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Install it to run seeding.")
    sys.exit(0)


def main():
    url = os.environ.get("POSTGRES_URL") or f"postgres://{os.environ.get('POSTGRES_USER','trust')}:{os.environ.get('POSTGRES_PASSWORD','trust')}@{os.environ.get('POSTGRES_HOST','localhost')}:{os.environ.get('POSTGRES_PORT','5432')}/{os.environ.get('POSTGRES_DB','trust')}"
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    # Seed countries
    with open(os.path.join("db", "seed", "seed_countries.sql"), "r") as f:
        sql = f.read()
        cur.execute(sql)

    # Mock observations for latest year
    year = datetime.now().year
    rows = [
        ("USA", year, "MOCK", "governance", None, None, 62.0, None, None, None),
        ("SWE", year, "MOCK", "governance", None, None, 75.0, None, None, None),
        ("BRA", year, "MOCK", "governance", None, None, 48.0, None, None, None),
        ("NGA", year, "MOCK", "governance", None, None, 45.0, None, None, None),
        ("IND", year, "MOCK", "governance", None, None, 55.0, None, None, None),
    ]
    cur.executemany(
        """
        insert into observations (iso3, year, source, trust_type, raw_value, raw_unit, score_0_100, sample_n, method_notes, source_url)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        rows,
    )
    print("Seeded countries and mock governance observations.")


if __name__ == "__main__":
    main()

