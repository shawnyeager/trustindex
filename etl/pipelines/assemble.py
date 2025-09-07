from __future__ import annotations
import argparse
import csv
from pathlib import Path


def assemble_governance_only(year: int, cpi_path: Path, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(cpi_path, newline="", encoding="utf-8") as f_in, open(out_path, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=["iso3", "year", "GOV", "GTI", "confidence_tier", "sources_used"])
        writer.writeheader()
        for row in reader:
            if int(row["year"]) != year:
                continue
            gov = float(row["score_0_100"])
            writer.writerow({
                "iso3": row["iso3"],
                "year": year,
                "GOV": gov,
                "GTI": gov,
                "confidence_tier": "C",
                "sources_used": '{"CPI": %d}' % year,
            })
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--sources", nargs="*", default=["CPI"])  # placeholder
    ap.add_argument("--cpi", type=Path, required=True, help="Path to normalized CPI CSV (from jobs/cpi.py)")
    ap.add_argument("--out", type=Path, default=Path("data/staging/country_year.csv"))
    args = ap.parse_args()

    n = assemble_governance_only(args.year, args.cpi, args.out)
    print(f"Assembled {n} country_year rows → {args.out}")


if __name__ == "__main__":
    main()

