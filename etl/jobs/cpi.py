
import argparse, os, csv, sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, required=True)
args = parser.parse_args()

raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw" / "cpi" / str(args.year)
staging_dir = Path(__file__).resolve().parents[2] / "data" / "staging"
raw_dir.mkdir(parents=True, exist_ok=True)
staging_dir.mkdir(parents=True, exist_ok=True)

# This is a stub: write a tiny staged CSV with demo values
out = staging_dir / f"cpi_{args.year}.csv"
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["iso3","year","cpi_score"])
    w.writerow(["SWE", args.year, 83])
    w.writerow(["USA", args.year, 69])
    w.writerow(["BRA", args.year, 38])
    w.writerow(["NGA", args.year, 25])
    w.writerow(["IND", args.year, 40])
print(f"Staged CPI to {out}")
