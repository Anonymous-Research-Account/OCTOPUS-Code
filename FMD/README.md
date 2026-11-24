# Artifact Submission: OCTOPUS: Observing Communication Traffic Of Pre-installed User Software on Re-Hosted Android Mobile Devices

**Note:** This repository has been prepared for a double-blind review process. All author-identifying information, affiliations, and acknowledgments have been removed.

# Steps: Pre-Processing Extraction and Static Analysis

This repository contains a modified version of FirmwareDroid (FMD) used to pre-process Android device images. It provides the necessary source code to extract Android device images and conduct the static analysis of the pre-installed Android apps. The modifications done to the framework allow to extract the file system of the Android device images in a form that they can be re-hosted for dynamic analysis.


# Reproduction Steps for the extraction of device images and the static analysis

## Prerequisits

- Storge: We used around 20TB of storage to download, filter, and extract the Android device images.
- RAM / CPU: A system with 128 CPUs and 256GB RAM is recommended
- Download the dataset (see DataSource) folder
- OS: Linux System (Ubuntu/Debian) with docker and docker compose
- Install FirmwareDroid according to it's official manual on a Linux system 
```bash
cd FirmwareDroid
./docker/build_images.sh
```


## Step-by-Step Guide for the Static Analysis
1. Startup FMD
```bash
# Start the containers
docker compose up -d

# Check if the tools starts and log-in
https://fmd.localhost/
```
2. Store the raw Android device images in the import folder of FirmwareDroid (e.g., <firmaredroid_folder>/blob_storage/00_file_storage/<some_id>/firmware_import/)
3. Use the FirmwareDroid API to import the device images (see https://fmd.localhost/graphql)
	- The API documentation is online available, but your request should look similiar to this one to start the importer task
```graphql
mutation createFirmwareExtractorJob {
  createFirmwareExtractorJob(
    createFuzzyHashes: false
    storageIndex: 0
    keepFilesOnDisk: false
  ) {
    jobId
  }
}
```
4. Wait until all device images have been imported (might take some days depending on the number of device images). You can check the status of the importers on https://fmd.localhost/django-rq/
5. After all device images have been imported, we need to get the list of firmware ids that the system created. We use the following query to get all firmware object ids. Use the ids for the next query.
```graphql
query GetFirmwareIdList {
  android_firmware_list {
    id
    versionDetected
  }
}
```
6. In the next step, we will start the static analysis with Exodus Core. Use the previously retrieved object-ids to scan all pre-installed apps.
```graphql
mutation createApkScanJob {
  createApkScanJob(
    moduleName: "EXODUS"
    firmwareIdList: ["699ae4d00712f939dee3d9be", ...
    ]
  ) {
    jobIdList
  }
}
```
7. Wait until all pre-installed apps have been scanned. You can check the status of the scan jobs on https://fmd.localhost/django-rq/
8. Now we can export all the results into a machine readable format to conduct the static analysis within a Jupyter notebook. We use the `db_export.py` script to export the data from the database into a jsonl file.
```bash
python3 <your_path>/FirmwareDroid/source/tools/db_export.py --env-file <your_path>/FirmwareDroid/.env --collection "apk_scanner_report" --usernam mongodbroot --password <your_db_password> --host localhost
```
9. Continue with the data analysis (see `/DataAnalysis` folder within the reproduction repo)

## Step-by-Step Guide to prepare the Re-Hosting

We assume you already have imported the Android device images in this step and have obtained the firmware object-ids. We will now create the AECS files for the Re-Hoster service.

1. Use the `createAecsBuildFilesJob` to create the packages necessary for the re-hosting.
```graphql
mutation createAecsBuildFilesJob {
  createAecsBuildFilesJob(
    formatName: "BP"
    firmwareIdList: ["68afe58665e2ad36cf26d321", <your_ids_here>]
    skipFileExport: false
  ) {
    jobIdList
  }
}
```
2. Wait until the AECS files have been created (might take some days depending on the number of device images). You can check the status of the importers on https://fmd.localhost/django-rq/
3. Create an AECS job per Android version. We will later use the AECS-id you get in the re-hoster. 
  - Note: Don't mix the Android versions here. Create one AECS jobs per Android version.
```graphql
mutation updateOrCreateAecsJob {
  updateOrCreateAecsJob(
    arch: "arm64"
    firmwareIdList: [<your_firmware_id_list>]
    queueName: "extractor"
  ) {
    jobId
  }
}
```
4. Retrieve the AECS object-ids and note them down
```graphql
query aecs_job_list {
  aecs_job_list {
    id
    pk
    firmwareIdList {
      edges {
        node {
          pk
        }
      }
    }
  }
}
```
5. Use the AECS object-ids to start the Re-Hoster service (see `/ReHoster` folder within the reproduction repo)












