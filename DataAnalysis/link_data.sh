#!/usr/bin/env bash
# Links the files downloaded from Zenodo into the folder layout that the notebooks expect.
# Nothing is copied: the notebooks read the files through symbolic links.
#
# Usage (from the DataAnalysis folder):
#   ./link_data.sh [zenodo dir] [--verify]
#     zenodo dir  folder with the downloaded Zenodo files (default: ../data)
#     --verify    also check the MD5 checksums (reads all files, ~13 GB; takes a few minutes)
#
# Result:
#   DataAnalysis/data/02_octopus/static_analysis/  android_firmware.jsonl, android_app.jsonl,
#       apk_scanner_report.jsonl, ApkScannerReport_ExodusReport.jsonl, static_analysis.parquet,
#       trackers.json, FirmwareDroid.android_firmware_v2.json, FirmwareDroid.build_props_v4.json
#   DataAnalysis/data/02_octopus/delta/            app_traffic.parquet, blocked_domains.parquet
#   DataAnalysis/data/02_octopus/coverage/         coverage_summary.csv  (-> coverage.csv on Zenodo)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ARG="${HERE}/../data"; VERIFY=0
for a in "$@"; do case "$a" in --verify) VERIFY=1 ;; *) SRC_ARG="$a" ;; esac; done
[ -d "$SRC_ARG" ] || { echo "Zenodo folder not found: $SRC_ARG (see REPRODUCE.md, step 1)"; exit 1; }
SRC="$(cd "$SRC_ARG" && pwd)"
DST="$HERE/data/02_octopus"
mkdir -p "$DST/static_analysis" "$DST/delta" "$DST/coverage" "$DST/pihole"

# <file on Zenodo> <target folder> <name in target folder> <needed by>
MAP="
android_firmware.jsonl                 static_analysis android_firmware.jsonl                 01
android_app.jsonl                      static_analysis android_app.jsonl                      01
apk_scanner_report.jsonl               static_analysis apk_scanner_report.jsonl               01
ApkScannerReport_ExodusReport.jsonl    static_analysis ApkScannerReport_ExodusReport.jsonl    01(optional)
static_analysis.parquet                static_analysis static_analysis.parquet                01(last_section),05
trackers.json                          static_analysis trackers.json                          01(last_section)
FirmwareDroid.android_firmware_v2.json static_analysis FirmwareDroid.android_firmware_v2.json 00
FirmwareDroid.build_props_v4.json      static_analysis FirmwareDroid.build_props_v4.json      00
app_traffic.parquet                    delta           app_traffic.parquet                    05
blocked_domains.parquet                delta           blocked_domains.parquet                reference
coverage.csv                           coverage        coverage_summary.csv                   04
"
missing=0
while read -r f dir name need; do
  [ -n "$f" ] || continue
  if [ -f "$SRC/$f" ]; then
    ln -sfn "$SRC/$f" "$DST/$dir/$name"; printf '  linked   %-40s -> data/02_octopus/%s/%s\n' "$f" "$dir" "$name"
  else
    printf '  MISSING  %-40s (needed by notebook %s)\n' "$f" "$need"; missing=$((missing+1))
  fi
done <<< "$MAP"
[ "$missing" -eq 0 ] || echo "$missing file(s) missing - the notebooks listed above will fail."

if [ "$VERIFY" -eq 1 ]; then
  echo "verifying MD5 checksums (this reads every file once) ..."
  python3 - "$SRC" "$HERE/../DataSources/DataArtefacts/zenodo_md5.txt" <<'PY'
import hashlib, os, sys
src, sums = sys.argv[1:3]; bad = 0
for line in open(sums):
    if not line.strip() or line.startswith('#'): continue
    want, name = line.split()
    p = os.path.join(src, name)
    if not os.path.exists(p): print(f"  skip     {name} (not downloaded)"); continue
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b''): h.update(chunk)
    ok = h.hexdigest() == want; bad += not ok
    print(f"  {'OK      ' if ok else 'MISMATCH'} {name}")
sys.exit(1 if bad else 0)
PY
fi
