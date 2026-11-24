# Paper results

Scripts that compute every number and table of Section 5 (RQ1–RQ3) from the released data.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh ../../data [out dir]     # data/ in the repository root, with app_traffic.parquet, static_analysis.parquet, coverage.csv from Zenodo
```

| Script | Computes |
|---|---|
| `01_blocklists_traffic.py` | Blocklist classification of all contacted domains; aggregation to (run, UID group) instances |
| `02_dynamic.py` | RQ2 runtime results, RQ3 stability and coverage |
| `03_static.py` | RQ1 tracker census |
| `compare.py` | Compares the outputs with `expected_results/` (the values in the paper) |

See `../../REPRODUCE.md` (Level A) for the mapping of outputs to tables in the paper.
