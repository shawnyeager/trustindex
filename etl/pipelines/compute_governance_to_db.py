from __future__ import annotations
import argparse
import os
from io import StringIO

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def compute_and_load(year: int, dsn: str) -> int:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    try:
        # Select CPI and WGI by iso3 for year and compute GOV
        cur.execute(
            """
            with cpi as (
              select iso3, score_0_100 as cpi from observations where year = %s and trust_type = 'cpi'
            ), wgi as (
              select iso3, score_0_100 as wgi from observations where year = %s and trust_type = 'wgi'
            ), joined as (
              select coalesce(cpi.iso3, wgi.iso3) as iso3,
                     cpi.cpi, wgi.wgi,
                     case when cpi.cpi is not null and wgi.wgi is not null then 0.5*cpi.cpi + 0.5*wgi.wgi
                          else coalesce(cpi.cpi, wgi.wgi) end as gov
                from cpi full outer join wgi on wgi.iso3 = cpi.iso3
            )
            select iso3, %s as year, gov from joined where gov is not null order by iso3
            """,
            (year, year, year),
        )
        rows = cur.fetchall()
        if not rows:
            return 0

        # Prepare COPY buffer
        buf = StringIO()
        for iso3, y, gov in rows:
            line = [
                iso3,
                str(y),
                "GOV",
                "governance",
                "\\N",
                "\\N",
                f"{float(gov):.6f}",
                "\\N",
                "Derived: GOV = 0.5*CPI + 0.5*WGI when both present; else passthrough",
                "https://www.transparency.org/en/cpi;https://info.worldbank.org/governance/wgi/",
            ]
            buf.write(",".join(line) + "\n")
        buf.seek(0)

        # Replace existing governance rows for year
        cur.execute("delete from observations where trust_type = 'governance' and year = %s", (year,))
        cur.copy_expert(
            """
            COPY observations (iso3, year, source, trust_type, raw_value, raw_unit, score_0_100, sample_n, method_notes, source_url)
            FROM STDIN WITH (FORMAT csv)
            """,
            buf,
        )
        conn.commit()
        return len(rows)
    finally:
        cur.close()
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--dsn", type=str, default=os.environ.get("POSTGRES_URL"))
    args = ap.parse_args()

    if psycopg2 is None:
        raise SystemExit("psycopg2-binary not installed. Install etl/requirements.txt.")
    if not args.dsn:
        raise SystemExit("POSTGRES_URL not set and --dsn not provided.")

    n = compute_and_load(args.year, args.dsn)
    print(f"Computed and inserted {n} governance rows for {args.year}.")


if __name__ == "__main__":
    main()

