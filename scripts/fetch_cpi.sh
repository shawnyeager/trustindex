#!/usr/bin/env bash
set -euo pipefail
YEAR=${1:-$(date +%Y)}
OUT_DIR="data/raw/cpi/${YEAR}"
mkdir -p "$OUT_DIR"
echo "(stub) Download CPI ${YEAR} to ${OUT_DIR}/cpi.csv"

