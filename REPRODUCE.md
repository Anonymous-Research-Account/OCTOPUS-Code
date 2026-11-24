# OCTOPUS – Step-by-Step Reproduction Guide

This guide explains how to set up the artifact and reproduce the results of the paper
*"OCTOPUS: Observing Communication Traffic Of Pre-installed User Software on Re-Hosted Android Mobile Devices"*.

The full measurement pipeline processes 1,056 Android firmware images (several TB of input) and needs a
bare-metal ARM64 server with KVM for the runtime stage. Because few reviewers have that infrastructure, the
artifact supports **three levels of reproduction**. Each level starts from the outputs of the previous one,
and we release the intermediate data at every hand-over point.

| Level | What you reproduce | Input | Hardware | Time |
|---|---|---|---|---|
| **A – Paper results** (recommended) | Every number, table and the runtime/static figures in Sections 5 (RQ1–RQ3) | Released data (Zenodo) + `DataSources/Blocklists` | Any laptop, 8 GB RAM, ~1 GB disk | < 5 min (plus download) |
| **B – Analysis notebooks** | Static-analysis dataset and the paper figures (Fig. 2–5) | Released data (Zenodo) | 32 GB RAM recommended, ~15 GB disk | ~1 h |
| **C – Full pipeline** | Firmware extraction, static scan, re-hosting, emulation, traffic capture | Firmware images from `DataSources/AndroidFirmware` | See Appendix A of the paper (Table "Hardware requirements") | Weeks |

If you only have a few hours, do **Level A** and then **Level B**. Level C is documented so that the
pipeline can be re-run and extended, but it cannot be completed within a typical artifact evaluation period.

---

## 0. Repository layout

```text
OCTOPUS-Code/                   (called OCTOPUS-Code-main if you downloaded the ZIP)
├── REPRODUCE.md                ← this guide
├── data/                       ← you create this folder and put ALL Zenodo files here (step 1)
├── DataSources/
│   ├── AndroidFirmware/        FirmwareSources.zip – download URLs of the firmware images (Level C)
│   ├── Blocklists/             Blocklists.zip – frozen copy of all DNS blocklist feeds (Level A)
│   └── DataArtefacts/          description of the released data files, zenodo_md5.txt (checksums)
├── FMD/                        modified FirmwareDroid: import, extraction, Exodus scan, AECS export (Level C, stage 1)
├── ReHoster/                   modified FMD-AECS: AOSP build injection, emulator containers, UI stimulation (Level C, stages 2–3)
└── DataAnalysis/
    ├── paper_results/          scripts that compute all numbers reported in the paper (Level A)
    ├── link_data.sh            links the files in data/ into the layout the notebooks expect (Level B)
    └── 0*_*.ipynb              Jupyter notebooks for dataset statistics and figures (Level B)
```

All commands below are run from the repository root (`OCTOPUS-Code/`) unless a `cd` says otherwise.

---

## 1. Download the released data (needed for Levels A and B)

The data is available at **https://zenodo.org/records/24012262**. Create the folder `data/` in the
repository root and download the files **into this one folder, without renaming or unpacking them**:

```bash
cd OCTOPUS-Code
mkdir -p data
# download the files from Zenodo into ./data
```

| File on Zenodo | Size | MD5 | Needed for |
|---|---:|---|---|
| `app_traffic.parquet` | 85.00 MB | `a51a73bb7ae506412f82af129e928803` | **A**, B (05) |
| `static_analysis.parquet` | 111.96 MB | `d68f849cfb9c3394adbf2ac9a8cf4e97` | **A**, B (01 last section, 05) |
| `coverage.csv` | 640.72 KB | `9927073b54066a8b4303a8a928184978` | **A**, B (04) |
| `blocked_domains.parquet` | 1.45 KB | `f91830b2b9b9394999d5cf8264ca400b` | A (58,167 Pi-hole queries, step A4) |
| `trackers.json` | 571.87 KB | `617a2841afa1f161ca038fa9fd025287` | B (01 last section) |
| `exodus_trackers.zip` | 15.67 KB | `0760d3dabadfa6482dae223e2b021d72` | B (reference copy of the tables of 01, last section) |
| `android_firmware.jsonl` | 7.11 GB | `63c3651ca1f6d5d28b91d36ad4da62cf` | B (01) |
| `android_app.jsonl` | 4.73 GB | `c67d4f0f42b503eef1f8530a46e98af8` | B (01) |
| `apk_scanner_report.jsonl` | 1.28 GB | `190fa5a5f6c958ce7a25703dfc997fef` | B (01) |
| `ApkScannerReport_ExodusReport.jsonl` | 517.63 MB | `3360059da95507da33749ba625fed3a1` | B (01, optional – notebook 01 creates it from `apk_scanner_report.jsonl`) |
| `FirmwareDroid.android_firmware_v2.json` | 2.31 MB | `0505fc6e3efdd736cc8597e667b3d108` | B (00) |
| `FirmwareDroid.build_props_v4.json` | 354.93 MB | `a08da9ed82a2b282e98c765e8f030402` | B (00) |
| `Blocklists.zip` | 65.12 MB | `96119d7d9baf9256f174bcedaaa53950` | not needed – identical to `DataSources/Blocklists/Blocklists.zip` in this repository |

**For Level A you only need the first four files (~200 MB).**

Afterwards `data/` should look like this (Level A files marked with `*`):

```text
data/
├── app_traffic.parquet *
├── static_analysis.parquet *
├── coverage.csv *
├── blocked_domains.parquet *
├── trackers.json
├── exodus_trackers.zip
├── android_firmware.jsonl
├── android_app.jsonl
├── apk_scanner_report.jsonl
├── ApkScannerReport_ExodusReport.jsonl
├── FirmwareDroid.android_firmware_v2.json
└── FirmwareDroid.build_props_v4.json
```

**Integrity check.** The MD5 checksums are the ones shown on the Zenodo record and are also in
`DataSources/DataArtefacts/zenodo_md5.txt`:

```bash
cd data && md5sum -c --ignore-missing ../DataSources/DataArtefacts/zenodo_md5.txt && cd ..   # Linux
md5 -r data/*                                                                                  # macOS: compare by eye
```

---

## 2. Level A – Reproduce the paper results (≈ 5 minutes)

**Requirements:** Linux or macOS, Python ≥ 3.10, `unzip`. **Input:** the first four files of the table
above in `data/`. The blocklists are taken from `DataSources/Blocklists/Blocklists.zip`; nothing else
has to be placed.

### Step A1 – Create a Python environment

```bash
cd DataAnalysis/paper_results
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step A2 – Run the analysis

```bash
./run_all.sh ../../data            # = the data/ folder in the repository root; results go to ./results
```

The script

1. unpacks the frozen blocklists from `DataSources/Blocklists/Blocklists.zip` into `results/blocklists/`,
2. `01_blocklists_traffic.py` – parses the 56 feeds (9,925,928 entries), classifies every contacted domain
   (and its parent domains) as *advertising/tracking* or *security/content*, and aggregates the
   app-attributed traffic to (run, UID group) instances,
3. `02_dynamic.py` – computes the runtime results (RQ2) and the stability/coverage results (RQ3),
4. `03_static.py` – computes the tracker census (RQ1),
5. `compare.py` – compares every output file with the values used in the paper (`expected_results/`).

### Step A3 – Check the result

The last lines of the output should read:

```text
comparing with expected_results/
  OK       blocklist_stats.json
  OK       domain_classification.csv
  OK       dynamic_results.json
  OK       stability.csv
  OK       static_by_vendor.csv
  OK       static_results.json
All results match the paper.
```

On our test machine (4 cores, 8 GB RAM) the run takes about 20 seconds (tested with Python 3.10 and 3.13;
pandas 2.3 and 3.1, pyarrow 26, numpy 2.2 and 2.5, matplotlib 3.11 on Linux).

The number of Pi-hole queries for blocklisted domains (58,167) comes directly from the released file:

```bash
python3 -c "import pandas as pd; print(pd.read_parquet('../../data/blocked_domains.parquet')['Count'].sum())"
```

### Step A4 – Map outputs to the paper

| Paper element | Output file → key |
|---|---|
| RQ1 headline (313,946 apps, 1,056 images, 9.2 % with tracker, median 26 tracker apps per image) | `static_results.json` → `apps`, `images`, `share_with_tracker`, `tr_apps_per_image_median_all` |
| Table "Tracker prevalence per vendor" | `static_by_vendor.csv` (vendors with ≥ 10 images) |
| Prevalence by partition and Android version | `static_results.json` → `by_partition`, `by_version` |
| Trackers in `com.android.*` packages and their permissions | `static_results.json` → `aosp_hosts`, `aosp_hosts_perm_share` |
| Runs with traffic, runs with Internet access per vendor | `dynamic_results.json` → `runs_total`, `images_total`, `runs_by_vendor`, `runs_internet_by_vendor` |
| Table "Static vs. dynamic" (2×2: none / static-only / both / dynamic-only) | `dynamic_results.json` → `instances*`, `cat_counts`, `cat_shared`, `dynamic_only_groups` |
| Table "Tracker-level confirmation" (AdMob, GTM, Firebase, GA, Crashlytics) | `dynamic_results.json` → `tracker_level`, `tracker_level_total` |
| Table "Ad/tracking packets by UID group and owner" | `dynamic_results.json` → `adtrack_pkts_by_grp_owner`, `adtrack_pkts_total`, `adtrack_domains_by_owner` |
| Unexplained endpoints, Gmail → Yahoo/Microsoft | `dynamic_results.json` → `unexplained_pairs`, `unexplained_by_owner_grp`, `gmail_*` |
| Listed domains (10, all by ad/tracking feeds) | `domain_classification.csv` (`listed == True`) |
| Blocklist size (feeds, entries) | `blocklist_stats.json` |
| Pi-hole queries for listed domains (58,167) | Zenodo `blocked_domains.parquet` → sum of `Count` |
| RQ3 cross-image stability (Jaccard) | `stability.csv`, `dynamic_results.json` → `stability*` |
| RQ3 coverage vs. category; carrier software; SSDP/mDNS | `dynamic_results.json` → `coverage_*`, `verizon`, `lan` |
| Supplementary figure: tracker share per vendor | `tracker_share_by_vendor.pdf` |

---

## 3. Level B – Analysis notebooks and figures (≈ 1 hour)

The notebooks in `DataAnalysis/` produce the dataset statistics and the figures of the paper. They do not read
`data/` directly but a fixed folder layout below `DataAnalysis/data/02_octopus/`. Some files also get a
different name there (`coverage.csv` → `coverage_summary.csv`). **Do not copy the files by hand**; run
`link_data.sh`, which creates the layout with symbolic links to the files in `data/`:

### Step B1 – Link the data

```bash
cd DataAnalysis
./link_data.sh ../data             # add --verify to also check the MD5 checksums (reads ~13 GB)
```

Every line should say `linked`; a `MISSING` line names the notebook that will fail without that file.
The resulting layout:

```text
DataAnalysis/data/02_octopus/
├── static_analysis/
│   ├── android_firmware.jsonl                 → data/android_firmware.jsonl
│   ├── android_app.jsonl                      → data/android_app.jsonl
│   ├── apk_scanner_report.jsonl               → data/apk_scanner_report.jsonl
│   ├── ApkScannerReport_ExodusReport.jsonl    → data/ApkScannerReport_ExodusReport.jsonl
│   ├── static_analysis.parquet                → data/static_analysis.parquet
│   ├── trackers.json                          → data/trackers.json
│   ├── FirmwareDroid.android_firmware_v2.json → data/FirmwareDroid.android_firmware_v2.json
│   └── FirmwareDroid.build_props_v4.json      → data/FirmwareDroid.build_props_v4.json
├── delta/
│   ├── app_traffic.parquet                    → data/app_traffic.parquet
│   └── blocked_domains.parquet                → data/blocked_domains.parquet
├── coverage/
│   └── coverage_summary.csv                   → data/coverage.csv
└── pihole/                                    (empty – gravity.db is not released, see "Known limitations")
```

Notebook 01 writes intermediate files (one JSONL per scanner, and `static_analysis.parquet` if you rebuild
it) into `static_analysis/`. Because that folder holds links, the new files are written into
`DataAnalysis/data/02_octopus/static_analysis/` and the downloaded files are not changed.

### Step B2 – Run the notebooks

```bash
python3 -m venv .venv && source .venv/bin/activate          # still in DataAnalysis/
pip install jupyterlab pandas numpy pyarrow fastparquet matplotlib seaborn scipy squarify jinja2 dpkt tldextract
jupyter lab
```

Start Jupyter in `DataAnalysis/` – the notebooks use paths relative to this folder. Run the notebooks top to
bottom (*Run → Run All Cells*). Figures are written to `DataAnalysis/images/`, tables to `DataAnalysis/tables/`.

**Last section of `01_StaticAnalysis.ipynb` only** (permission baseline and Exodus tracker categories): it needs
only `static_analysis.parquet` and `trackers.json` (Exodus tracker registry, export of
`https://reports.exodus-privacy.eu.org/api/trackers`). To run it without the 13 GB JSONL import, run the first
cell and then the section from its heading *Permission baseline and tracker categories* onwards
(*Run Selected Cell and All Below*). Its tables are written to `DataAnalysis/tables/`; `exodus_trackers.zip`
on Zenodo contains our copy of these tables for comparison.

| Notebook | Input (in `DataAnalysis/data/02_octopus/`) | Produces | Paper |
|---|---|---|---|
| `01_StaticAnalysis.ipynb` | `static_analysis/*.jsonl`; last section: `static_analysis/static_analysis.parquet` + `static_analysis/trackers.json` | `static_analysis.parquet`, `vendor_distribution_facets.pdf`, `tracker_frequency_bar.pdf`, `trackers_clusters_heatmap_condensed.pdf`; last section: `tables/perm_baseline_*.{csv,tex}`, `tables/tracker_category_*.{csv,tex}`, `tables/trackers_uncategorised.csv` | Fig. 2, 3, 4; RQ1 |
| `04_CoverageAnalysis.ipynb` | `coverage/coverage_summary.csv` | `coverage_ecdf_filtered.pdf`, `coverage_statistics*.tex` | Fig. 5; RQ3 |
| `05_DeltaAnalysis.ipynb` | `static_analysis/static_analysis.parquet`, `delta/app_traffic.parquet`, `pihole/gravity.db` | exploratory static-vs-dynamic comparison | superseded by Level A |
| `00_DatasetOverview.ipynb` | `static_analysis/FirmwareDroid.android_firmware_v2.json` (import result per partition), `static_analysis/FirmwareDroid.build_props_v4.json` (build properties) | dataset overview figures (import success, SDK versions, brands/manufacturers) | dataset description |
| `02_NetworkTraceAnalysis.ipynb` | raw `emulator_out/` (pcaps, eCapture logs; Level C) | `app_traffic.parquet` | creates the released traffic data |
| `03_DNSAnalysis.ipynb` | Pi-hole `pihole-FTL.db`, `gravity.db` (Level C) | `blocked_domains.parquet` | creates the released DNS data |

Notebook 01 reads ~13 GB of JSONL; we recommend at least 32 GB RAM. Notebooks 02 and 03 document how
the released `app_traffic.parquet` and `blocked_domains.parquet` were created from the raw captures; their
inputs are produced by Level C and are not released (see section 6). Notebook 05 needs `gravity.db`, which is
not released; its results are computed by Level A.

---

## 4. Level C – Full pipeline

The pipeline has three stages. Each stage hands over identifiers or files to the next one:

```text
Firmware images ──► FMD (import, extraction, Exodus scan) ──► firmware ids + AECS ids
                                                               │
                         ReHoster (AOSP build injection) ◄─────┘
                                   │  re-hosted images in Nexus
                                   ▼
                 ReHoster runtime (emulator containers, UI stimulation, capture)
                                   │  emulator_out/<image>/
                                   ▼
                 DataAnalysis notebooks 02/03/04 ──► released data ──► Level A
```

### 4.1 Hardware and software

| Stage | Used in the study | Minimum |
|---|---|---|
| Extraction & static analysis (FMD) | 1 server, 64 vCPUs, 252 GB RAM, ~20 TB storage | x86-64 or ARM64, Docker |
| Re-hosting / image build (ReHoster) | 7 servers, 64 vCPUs, 64 GB RAM, 4 TB each | x86-64 or ARM64, ~500 GB per AOSP checkout |
| Runtime testing | Bare-metal ARM64 (Ampere Altra), 128 cores, 502 GB RAM, 6 TB | ARM64 host with `/dev/kvm`, 8 cores + 8 GB RAM per concurrent emulator |
| Image registry | Nexus Repository Manager, ~32 TB | depends on number of images |

All hosts: Ubuntu 22.04 LTS, Docker Engine with the Compose plugin, Python 3.10+, `git`, `repo`.

### 4.2 Stage 1 – Obtain the firmware images

```bash
cd OCTOPUS-Code/DataSources/AndroidFirmware
unzip FirmwareSources.zip -x '__MACOSX/*'
wc -l *.txt          # one download URL per line, grouped by source
```

Download the images (e.g. `aria2c -i google_links.txt -j 8`). The per-image hashes (MD5, SHA-256), original
file names and sizes are in `android_firmware.jsonl` on Zenodo; use them to verify the downloads. Some community
mirrors may have removed images since our download. We do not redistribute firmware.

### 4.3 Stage 2 – Extraction and static analysis with FirmwareDroid (`FMD/`)

1. **Build and configure FirmwareDroid** (build locally – the public `ghcr.io` images do *not* contain our modifications):
   ```bash
   cd OCTOPUS-Code/FMD
   python3 -m pip install jinja2
   python3 setup.py               # interactive; creates .env, env/ and blob_storage/ (default domain fmd.localhost)
   ./docker/build_images.sh
   docker compose up -d
   ```
   Open `https://fmd.localhost/` and log in with the credentials configured during `setup.py` (see `.env`).
2. **Import the firmware.** Copy the downloaded archives to
   `FMD/blob_storage/00_file_storage/<id>/firmware_import/` and start the importer in the GraphQL console
   (`https://fmd.localhost/graphql`):
   ```graphql
   mutation { createFirmwareExtractorJob(createFuzzyHashes: false, storageIndex: 0, keepFilesOnDisk: false) { jobId } }
   ```
   Progress: `https://fmd.localhost/django-rq/`. Importing ~1,000 images takes several days.
3. **List the firmware ids:**
   ```graphql
   query { android_firmware_list { id versionDetected } }
   ```
4. **Run the Exodus scan** on all pre-installed apps:
   ```graphql
   mutation { createApkScanJob(moduleName: "EXODUS", firmwareIdList: ["<id1>", "<id2>"]) { jobIdList } }
   ```
5. **Export the results** to JSONL (these are the files released on Zenodo):
   ```bash
   pip install pymongo python-dotenv pandas pyarrow
   python3 source/tools/db_export.py --env-file .env --host localhost --username mongodbroot \
       --password <db_password> --format jsonl --output-dir ./fmd_export
   ```
   Continue with notebook `01_StaticAnalysis.ipynb` (Level B).
6. **Create the re-hosting packages (AECS):**
   ```graphql
   mutation { createAecsBuildFilesJob(formatName: "BP", firmwareIdList: ["<id1>", "..."], skipFileExport: false) { jobIdList } }
   ```
   Then create **one AECS job per Android version** (do not mix versions) and note the returned ids:
   ```graphql
   mutation { updateOrCreateAecsJob(arch: "arm64", firmwareIdList: ["<ids of one Android version>"], queueName: "extractor") { jobId } }
   query { aecs_job_list { id pk } }
   ```

See `FMD/README.md` for details.

### 4.4 Stage 3 – Re-hosting (`ReHoster/`)

1. **Nexus registry.** Deploy Nexus Repository Manager (see `ReHoster/nexus/README.md`), create a raw
   repository `emulator-images` and a Docker repository `docker-emulator-images`, and a user that may upload.
2. **AOSP checkout** (example Android 12, ~500 GB):
   ```bash
   mkdir aosp12_r9 && cd aosp12_r9
   repo init --partial-clone -b android-12.0.0_r9 -u https://android.googlesource.com/a/platform/manifest
   repo sync -j 32
   ```
3. **Python environment:**
   ```bash
   cd OCTOPUS-Code/ReHoster
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Credentials.** Edit `run_script_to_file()` in
   `device_configs/development/12/r9/build_image.py`: set the script and venv paths to your checkout and
   `FMD_USERNAME`, `FMD_PASSWORD`, `DOCKER_REPO_URL`, `DOCKER_REPO_USERNAME`, `DOCKER_REPO_PASSWORD`.
5. **Patch AOSP:**
   ```bash
   python3 aosp_setup.py -V 12 -p <path>/aosp12_r9/ -b <path>/ReHoster/device_configs/development/12/r9/build_image.py
   ```
6. **Build the re-hosted images** for one AECS id:
   ```bash
   export FMD_PASSWORD=<fmd_password> DOCKER_REPO_PASSWORD=<nexus_password>
   export BUILD_BROKEN_SRC_DIR_RW_ALLOWLIST=<path>/ReHoster/out/
   python3 aosp_build_injector.py -t r9_dev -p <aecs_id> -f https://<fmd_host> -u fmd-admin \
       -s <path>/aosp12_r9 -e 12 -a arm64 \
       -r https://<nexus>:8443/repository/emulator-images/ -d <nexus_user> \
       --pre_injector_config  ./device_configs/development/12/r9/pre_injector_config_v1.json \
       --post_injector_config ./device_configs/development/12/r9/post_injector_config_v1.json
   ```
   Success message: `Successfully built N of the following firmware ids: ...`. The uploaded image names
   are listed in `out/uploaded_artefacts.txt`.

See `ReHoster/README.md` for details.

### 4.5 Stage 4 – Runtime testing (ARM64 + KVM host)

1. **Base emulator image:**
   ```bash
   cd OCTOPUS-Code/ReHoster
   ./docker_base_build.sh                       # builds fmd-emulator_arm64
   ```
2. **Network and environment.** The orchestrator attaches each emulator to the Docker networks
   `project_frontend` and `project_android` (subnet containing `172.31.250.0/24`) and reads container
   variables from `ReHoster/env/.env`. The DNS resolver (Pi-hole with the feeds from
   `DataSources/Blocklists`) and the capture services run on these networks. Create `env/` (secrets,
   TLS certificates, Pi-hole, TURN, mitmproxy and nginx configuration) from the template:
   ```bash
   ./env.example/init_env.sh <your host name>     # creates env/ and docker-compose.yaml; see env.example/README.md
   docker compose up -d                           # Pi-hole, mitmproxy, envoy, nginx, coturn + networks
   docker compose ps
   ```
3. **Orchestrator.** Set `MAX_CONCURRENT_EMULATORS` in `consumer.py` (20 on 128 cores / 502 GB; budget
   8 cores and 8 GB RAM per emulator – overcommitting leads to frozen emulators and biased results) and run it
   as a systemd service (unit file in `ReHoster/README.md`) or directly: `python3 consumer.py`.
4. **Pull images and start testing.** Put the image names (comma-separated, one line) into
   `uploaded_artefacts.txt` and run:
   ```bash
   export DOCKER_REPO_PASSWORD=<nexus_password>
   python3 create_docker_emulator_images.py -w 10 --skip-push --aria2-connections 4 --download-workers 5 \
       -r "https://<nexus>:8443/service/rest/v1/assets?repository=emulator-images" \
       -d "https://<nexus>:8083/nexus3/repository/docker-emulator-images/" -u <nexus_user> \
       --input-dir <path>/emulator_images --file-list-file uploaded_artefacts.txt
   docker ps        # android_emulator_<n> containers should be running
   ```
   Each application is exercised for 20 minutes; one image takes 4–24 hours.
5. **Collect results.** Per image, results are written to `ReHoster/emulator/emulator_out/<image>/`
   (`pcaps/`, `ecapture/`, `package_uids_emulator-5556.json`, coverage files). Generate coverage reports with
   `ReHoster/emulator/acvtool-report/` (see its README; its merged CSV is the released `coverage.csv`), then
   copy `emulator_out/` to `DataAnalysis/data/02_octopus/emulator_out/` and the Pi-hole databases
   (`pihole-FTL.db`, `gravity.db`) to `DataAnalysis/data/02_octopus/pihole/`, and run notebooks 02 and 03 to
   obtain `app_traffic.parquet` and `blocked_domains.parquet`. Put these files and `coverage.csv` into `data/`
   in the repository root and continue with Level A.

---

## 5. Expected deviations when re-running Level C

* **Network endpoints change over time.** Re-running the emulators today contacts different servers and
  receives different responses; the released traffic captures are the reference for the paper.
* **Firmware availability.** Community mirrors may no longer serve every image.
* **Blocklists change daily.** Always use the frozen copy in `DataSources/Blocklists/Blocklists.zip`.
* **UI exploration is randomized**; per-run domain sets vary (the paper quantifies this as cross-image
  stability, median Jaccard 0.50).

## 6. Known limitations of the artifact

* **Pi-hole database not released.** The Pi-hole query database (`pihole-FTL.db`) is the unfiltered DNS log
  of the whole measurement network. Besides the queries of the emulated devices, it contains client
  addresses, timestamps and queries of the measurement infrastructure that are unrelated to the experiments.
  It cannot be anonymized without losing its structure, so we do not publish it. The analysis does not need
  it, because the released data already contains the relevant information:
  * `app_traffic.parquet`: one record per captured packet with time, firmware run, UID and package name,
    source/destination address and port, protocol, length, and the resolved destination domain
    (`real_domain`). This is the input of all traffic results (RQ2, RQ3) and of the blocklist
    classification in Level A.
  * `blocked_domains.parquet`: the Pi-hole query counts per blocklisted domain, exported from
    `pihole-FTL.db` by notebook 03 (sum = 58,167 queries reported in the paper).
  * `DataSources/Blocklists/Blocklists.zip`: the frozen blocklist feeds. They replace the Pi-hole blocklist
    database (`gravity.db`), which only contains these feeds.
* **Raw packet captures not released.** For the same reason, the raw captures (`emulator_out/`: pcaps,
  eCapture logs) are not released; `app_traffic.parquet` is the packet metadata extracted from them by
  notebook 02.
* Consequently, notebooks 02 and 03, which create these two files from the raw data, can only be run after a
  Level C measurement, and notebook 05 is replaced by Level A.
* Proprietary firmware images are not redistributed; only their download URLs and hashes are provided.

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `run_all.sh: missing data/...` | Pass the folder that contains the Zenodo files as the first argument (`../../data` when run from `DataAnalysis/paper_results`). |
| Notebook: `FileNotFoundError: ./data/02_octopus/...` | Run `./link_data.sh ../data` in `DataAnalysis/` (step B1) and start Jupyter in `DataAnalysis/`. |
| Notebook: file exists but cannot be opened | The links point to the old location after moving `data/`; run `./link_data.sh` again. |
| `ModuleNotFoundError: pyarrow` | Activate the virtual environment (`source .venv/bin/activate`). |
| Notebook 00/01 is killed | Not enough RAM; use a machine with ≥ 32 GB. |
| FMD web UI not reachable | Add `127.0.0.1 fmd.localhost` to `/etc/hosts`; check `docker compose ps`. |
| Emulator containers exit immediately | `/dev/kvm` not available or not ARM64 host; check `ls -l /dev/kvm`. |

## 8. Intended use

For academic research, education and defensive security analysis only. See `DataSources/README.md`.
