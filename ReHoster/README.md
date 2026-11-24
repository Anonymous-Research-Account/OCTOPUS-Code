# Artifact Submission: OCTOPUS: Observing Communication Traffic Of Pre-installed User Software on Re-Hosted Android Mobile Devices

**Note:** This repository has been prepared for a double-blind review process. All author-identifying information, affiliations, and acknowledgments have been removed.

# Step: Pre-Processing Re-Hosting

We assume you already have obtained the ACES object-ids. If not, please start with the setup of the FMD framework first before continue reading (see folder `/FMD` in the reproduction repo).

## Prerequisits
- AECS object-ids for the device images
- Nexus Repository: You need to install a Nexus repository with a user that is allowed to upload blob files (see folder `/Rehoster/nexus` as example)
  - Storage: We use around 32TB of storage to be able to store all re-hosted device images and coverage data. This depends on the number of device images you process
- Re-Hoster System:
  - OS: Linux Ubuntu 22.04 LTS
  - CPU/RAM: At least 64CPUs with 128GB RAM
  - 3TB of Storage


## Setup the Re-Hoster

1. Download the AOSP source code for the Android version you want to re-host. This will require around 500GB of storage depending on the Android version. For instance, for Android 12:
```
mkdir aosp_12
cd aosp_12
sudo apt install -y repo
git config --global user.email "you@example.com"
git config --global user.name "Your Name"

# Authtenticate with Google to get a cookie:
https://android.googlesource.com/new-password

# Example With Authentication for Android 12
repo init --partial-clone -b android-12.0.0_r9 -u https://android.googlesource.com/a/platform/manifest
repo sync -j 32
```

2. Adjust the build_image.py of the AOSP version you want to use to include your credentials. Search for the `run_script_to_file` within the file and add you credentials there:
```bash
nano <your_path>/ReHoster/device_configs/development/12/r9/build_image.py

def run_script_to_file(partition):
  script_path = "/home/ubuntu/FMD-AECS/aosp_post_build_injector.py"
  outdir = "/tmp/fmd/out"
  first_marker = os.path.join(outdir, ".post_injector_first_{0}".format(partition))
  ran_marker = os.path.join(outdir, ".post_injector_ran_{0}".format(partition))
  output_path = os.path.join(outdir, "post_injector_out_{0}.log".format(partition))

  python_path = "/home/ubuntu/FMD-AECS/venv/bin/python3"
  current_env = os.environ.copy()
  # Add these env variables with your credentials
  current_env["FMD_USERNAME"]="fmd-admin"
  current_env["FMD_PASSWORD"]="<your_fmd_password>"
  current_env["DOCKER_REPO_URL"] = "https://<your_nexus_url>:8443/repository/emulator-images/"
  current_env["DOCKER_REPO_USERNAME"] = "<your_nexus_user>"
  current_env["DOCKER_REPO_PASSWORD"] = "<your_nexus_password>"
  current_env["BUILD_BROKEN_USES_NETWORK"]="true"
```


3. Prepare the AOSP repository to be used for re-hosting via the `aosp_setup.py` script. This will modify the source code of the AOSP repository:
```
source venv/bin/activate
pip install -r requirements

python3 ./aosp_setup.py --help
usage: aosp_setup.py [-h] [-V {11,12,12_1,13,14,15,16}] [-p PATH] -b BUILD_IMAGE_SCRIPT_PATH [--dry-run] [--verbose]

AOSP repository tweaks and helpers

options:
  -h, --help            show this help message and exit
  -V {11,12,12_1,13,14,15,16}, --version {11,12,12_1,13,14,15,16}
                        A single AOSP version to process (defaults to the newest known version)
  -p PATH, --path PATH  Path to the AOSP repository base. If provided, this overrides the internal AOSP_PATHS mapping for the selected version.
  -b BUILD_IMAGE_SCRIPT_PATH, --build-image-script-path BUILD_IMAGE_SCRIPT_PATH
                        Path to the custom build_image.py script to inject
  --dry-run             Print actions without making changes
  --verbose             Enable verbose output


python3 ./aosp_setup.py -V 12 -p <your_path>/aosp_12/ -b <your_path>/ReHoster/device_configs/development/12/r9/build_image.py
```

4. Start the re-hosting using your AECS object-id. The following wrapper script is an example to start re-hosting for an Android 12 device.
```bash
#!/bin/bash
export PYTHONWARNINGS="ignore:Unverified HTTPS request"
export FMD_PASSWORD=<your_fmd_password>
export DOCKER_REPO_PASSWORD=<your_nexus_uploader_password>
export BUILD_BROKEN_SRC_DIR_RW_ALLOWLIST=/home/ubuntu/FMD-AECS/out/

PYTHON_VENV="<your_path>/venv/bin/python3"
$PYTHON_VENV ./aosp_build_injector.py -t "r9_dev" -p "<your_aecs_object_id>" -f "https://<your_fmd_instance_url>" -u "fmd-admin" -s "<your_path>/aosp12_r9" -e "12" -r "https://<your_nexus_repository_url>:8443/repository/emulator-images/" -d "<your_nexus_username>" -a "arm64" --pre_injector_config "./device_configs/development/12/r9/pre_injector_config_v1.json" --post_injector_config "./device_configs/development/12/r9/post_injector_config_v1.json"
```
5. Wait until the device images have been re-hosted. You should see an output like the following one when the re-hosting is complete. 
```
Successfully built 25 of the following firmware ids: <your_object_ids>
```
Note: The device images will continously been uploaded to the Nexus repository and there is a file (`uploaded_artefacts.txt`) in the `/out` folder that shows the filenames of the uploaded device images.


## Step: Containerization and Runtime Testing

## Prerequisits

This depends on the number of emulators you want to run in parallel. For around 20 emulators you need the following setup:
- Runtime System: 
  - Arch: **ARM64v8**
  - OS: Linux Ubuntu 22.04 LTS
  - CPU/RAM: At least 128CPUs with 502GB RAM
  - 6TB of Storage
  - Software:
    - KVM
    - docker and docker compose


## Step-by-Step Guide to create the docker containers


### Setup an dynamic docker orchestration service

To test all the images, it is recommended to setup an automated docker orchestrator that handles starting and stopping the docker containers.

We will configure a linux deamon to dynamically start and stop emulator containers as following:
```
nano /etc/systemd/system/fmd-consumer.service   

[Unit]
Description=FMD-Reloaded Emulator Consumer Daemon
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=<your_path>/FMD-AECS
ExecStart=<your_path>/venv/bin/python3 <your_path>/consumer.py
Restart=always
RestartSec=10
# Optional: Run as your specific user instead of root
# User=your_username 

[Install]
WantedBy=multi-user.target

```

This will execute the `consumer.py` script within the ReHoster. On top of the `consumer.py` you can configure the maximal number of emulators to start:

```
...
# --- Resource Pool Configuration ---
MAX_CONCURRENT_EMULATORS = 20
...
```
Note: If you set the `MAX_CONCURRENT_EMULATORS` too high it might influence the experiment results as emulators might freez or crash due to ressource limitations of your host machine.


### Create the docker images and start them continously

As next step, we will start the creation of the docker containers and start the automated dynamic analysis.

1. Create within the ReHoster folder a file named `uploaded_artefacts.txt`. This file will include the re-hosted device images to be downloaded from the Nexus repository and to be started for testing. For instance:
```
"698c1b2cab2ebd4d06d32e2d_v12_sdk_phone64_arm64_userdebug_r9_dev.zip","698c1bb3ab2ebd4d06d3481f_v12_sdk_phone64_arm64_userdebug_r9_dev.zip"
```
The artefact names can be obtained on the Re-Hosting system from the `out/upload_artefacts.txt` or directly from the Nexus repository.

Note: That all filenames must be seperated by commas and on one line.

2. Next we create a simple bash wrapper to start run the containerization and spawn the docker containers.
```bash
#!/bin/bash
export PYTHONWARNINGS="ignore:Unverified HTTPS request"
export DOCKER_REPO_PASSWORD=<your_nexus_user_password>

source ./venv/bin/activate && python3 ./create_docker_emulator_images.py -w 10 --skip-push --aria2-connections 4 --download-workers 5 -r "https://<your_nexus_url>:8443/service/rest/v1/assets?repository=emulator-images" -d "https://<your_nexus_url>:8083/nexus3/repository/docker-emulator-images/" -u "<your_nexus_user>" --input-dir "<your_path>/emulator_images" --file-list-file <your_path>/uploaded_artefacts.txt
```
3. After you have executed the script in the previous step, the containers should start the re-hosted device images and automatically executed the testing script. You can check if the containers are running with the `docker ps` command. The output should look similiar to this one:
```
af7f04067466   68b2c67765e2ad36cf60f6d4_v12_sdk_phone64_arm64_userdebug_r9_dev   "/usr/local/bin/dock…"   9 hours ago   Up 9 hours              0.0.0.0:2229->22/tcp, [::]:2229->22/tcp, 0.0.0.0:5007->5037/tcp, [::]:5007->5037/tcp, 0.0.0.0:5562->5555/tcp, [::]:5562->5555/tcp, 0.0.0.0:8561->8554/tcp, [::]:8561->8554/tcp   android_emulator_2153
bba07ea9f7e3   68b24fb565e2ad36cf090495_v12_sdk_phone64_arm64_userdebug_r9_dev   "/usr/local/bin/dock…"   9 hours ago   Up 9 hours              0.0.0.0:2230->22/tcp, [::]:2230->22/tcp, 0.0.0.0:5008->5037/tcp, [::]:5008->5037/tcp, 0.0.0.0:5563->5555/tcp, [::]:5563->5555/tcp, 0.0.0.0:8562->8554/tcp, [::]:8562->8554/tcp   android_emulator_2144
c5ce545053bd   68b280f165e2ad36cf2f0786_v12_sdk_phone64_arm64_userdebug_r9_dev   "/usr/local/bin/dock…"   9 hours ago   Up 9 hours              0.0.0.0:2234->22/tcp, [::]:2234->22/tcp, 0.0.0.0:5012->5037/tcp, [::]:5012->5037/tcp, 0.0.0.0:5567->5555/tcp, [::]:5567->5555/tcp, 0.0.0.0:8566->8554/tcp, [::]:8566->8554/tcp   android_emulator_2142
```
4. Depending on the number of apps to test, the containers will run several hours or just some minutes. The results and logs of the execution will be stored in the folder `./emulator/emulator_out/<artefact_name>`.
5. Copy the data artefacts from the `./emulator/emulator_out/` to the post-processing folder (see `/DataAnalysis` in the reproduction package).








