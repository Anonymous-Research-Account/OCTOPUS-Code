# Post-Processing Data Analysis

This folder contains the data-analysis artifacts for the study "OCTOPUS: Observing Communication Traffic Of Pre-installed User Software on Re-Hosted Android Mobile Devices". It provides the Jupyter notebooks (Level B) and the scripts that compute all numbers of the paper (`paper_results/`, Level A).

**Where to put the data.** Download the files from [https://zenodo.org/records/24012262](https://zenodo.org/records/24012262) into the folder `data/` in the **repository root** (not into this folder). Then:

* Level A: `cd paper_results && ./run_all.sh ../../data`
* Level B (notebooks): `./link_data.sh ../data` in this folder. The script links the files into the layout the notebooks read (`DataAnalysis/data/02_octopus/...`, including the rename `coverage.csv` → `coverage_summary.csv`). Start Jupyter in this folder.

See [`../REPRODUCE.md`](../REPRODUCE.md), sections 1–3, for the file list, checksums and the full layout.
