#!/usr/bin/env bash
# Reproduces all numbers, tables and Figure "tracker share by vendor" of the paper
# from the released Zenodo dataset and the blocklists shipped in DataSources/.
# Usage: ./run_all.sh <data dir with Zenodo files> [out dir]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="$(cd "${1:?usage: run_all.sh <data dir> [out dir]}" && pwd)"
OUT="${2:-$HERE/results}"
BLZIP="$HERE/../../DataSources/Blocklists/Blocklists.zip"
mkdir -p "$OUT"
for f in app_traffic.parquet static_analysis.parquet; do
  [ -f "$DATA/$f" ] || { echo "missing $DATA/$f (download from Zenodo, see REPRODUCE.md)"; exit 1; }
done
[ -f "$DATA/coverage.csv" ] || [ -f "$DATA/coverage_summary.csv" ] || { echo "missing $DATA/coverage.csv (download from Zenodo, see REPRODUCE.md)"; exit 1; }
BL="$OUT/blocklists"
if [ ! -d "$BL" ]; then
  echo "[0/3] unpacking blocklists"; mkdir -p "$BL"; unzip -q "$BLZIP" -d "$BL"; rm -rf "$BL/__MACOSX"
fi
echo "[1/3] blocklist classification + traffic aggregation"; python3 "$HERE/01_blocklists_traffic.py" "$BL" "$DATA" "$OUT" > "$OUT/01.log"
echo "[2/3] dynamic analysis (RQ2, RQ3)";                    python3 "$HERE/02_dynamic.py" "$DATA" "$OUT" > "$OUT/02.log"
echo "[3/3] static analysis (RQ1)";                          python3 "$HERE/03_static.py"  "$DATA" "$OUT" > "$OUT/03.log"
echo "comparing with expected_results/"; python3 "$HERE/compare.py" "$HERE/expected_results" "$OUT"
