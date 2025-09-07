from __future__ import annotations
import argparse
import csv
import os
from pathlib import Path
from typing import List, Dict


def normalize_cpi_csv(in_path: Path, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(in_path, newline="", encoding="utf-8") as f_in, open(out_path, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=["iso3", "year", "source", "trust_type", "score_0_100", "source_url"])
        writer.writeheader()
        for row in reader:
            iso3 = row.get("iso3") or row.get("ISO3")
            year = row.get("year") or row.get("Year")
            score = row.get("cpi") or row.get("CPI") or row.get("score")
            if not (iso3 and year and score):
                continue
            writer.writerow({
                "iso3": iso3,
                "year": int(year),
                "source": "CPI",
                "trust_type": "cpi",
                "score_0_100": float(score),
                "source_url": "https://www.transparency.org/en/cpi",
            })
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--input", type=Path, help="Path to CPI CSV (must include iso3,year,cpi columns)")
    ap.add_argument("--out", type=Path, default=Path("data/staging"))
    args = ap.parse_args()

    if not args.input:
        raise SystemExit("--input is required in offline init stub")

    out_file = args.out / f"cpi_{args.year}.csv"
    n = normalize_cpi_csv(args.input, out_file)
    print(f"Wrote {n} CPI rows → {out_file}")


if __name__ == "__main__":
    main()

