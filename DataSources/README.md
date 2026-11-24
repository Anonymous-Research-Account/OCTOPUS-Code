# Data Sources

We provide the initial download source links to get the Android images from the original source servers. The dataset of Android device images requires several terabytes of storage and consists of a mix of official Android device images and community provided device images. In addition, we provide a list of cryptographic file hashes (md5 and sha256) for each of the analysed Android firmware images together with other meta-data (e.g., original file name, file size, etc.). The meta-data can be found in the `android_firmware.jsonl` file on Zenodo (https://zenodo.org/records/24012262, see `DataArtefacts/README.md`).


## Folder Structure:

```text
.
├── Blocklists/
│   └── Source URLs and copy of the used blocklists.
│
├── DataArtefacts/
│   └── Description of the released data files (Zenodo) and their MD5 checksums
│
└── AndroidFirmware/
   └── Source URLs to download the initial Android device image dataset
```


## Intended Use and Academic Disclaimer

**For Academic and Educational Purposes Only**
The methodologies, scripts, blocklists, and data sources provided in this repository are intended strictly for academic research, educational purposes, and defensive security analysis. This includes, but is not limited to, the dynamic analysis of internal systems, vulnerability detection, and the observation of communication traffic. 

The authors do not condone or support the use of these materials for malicious purposes. Users of this dataset and the associated artifacts are solely responsible for ensuring that their research complies with all applicable local, national, and international laws, as well as the terms of service of the original firmware distributors. Please note that the direct redistribution of proprietary binaries may constitute copyright infringement in certain jurisdictions.

