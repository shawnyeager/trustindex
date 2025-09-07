from __future__ import annotations
import argparse
import csv
from pathlib import Path
from typing import Optional


def rescale_wgi(x: Optional[float]) -> Optional[float]:
    if x is None:
        return None
    return ((x + 2.5) / 5.0) * 100.0


def normalize_wgi_csv(in_path: Path, out_path: Path, year: int) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(in_path, newline="", encoding="utf-8") as f_in, open(out_path, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(
            f_out,
            fieldnames=["iso3", "year", "source", "trust_type", "score_0_100", "source_url"],
        )
        writer.writeheader()
        for row in reader:
            iso3 = (row.get("iso3") or row.get("ISO3") or "").upper()
            y = int(row.get("year") or year)
            if y != year:
                continue
            rol = row.get("rule_of_law")
            ge = row.get("government_effectiveness")
            if rol is None or ge is None:
                continue
            rol = float(rol)
            ge = float(ge)
            avg = (rol + ge) / 2.0
            score = rescale_wgi(avg)
            writer.writerow(
                {
                    "iso3": iso3,
                    "year": year,
                    "source": "WGI",
                    "trust_type": "wgi",
                    "score_0_100": round(score, 2) if score is not None else None,
                    "source_url": "https://info.worldbank.org/governance/wgi/",
                }
            )
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--input", type=Path, required=True, help="CSV with iso3,year,rule_of_law,government_effectiveness")
    ap.add_argument("--out", type=Path, default=Path("data/staging"))
    args = ap.parse_args()

    out_file = args.out / f"wgi_{args.year}.csv"
    n = normalize_wgi_csv(args.input, out_file, args.year)
    print(f"Wrote {n} WGI rows → {out_file}")


if __name__ == "__main__":
    main()

