===============================================================================
MERIDIAN ENTERPRISE APPLICATION - BACKEND/BIN USAGE & DEPLOYMENT GUIDE
===============================================================================

1. PURPOSE OF THIS FOLDER (backend/bin)
---------------------------------------
This folder contains the bundled MeshCentral CLI client ("meshctrl.js") and its 
minimal Node.js dependencies. It enables the Meridian Enterprise Application to 
perform remote remediation and generate Jira remote sharing links against the 
deployed MeshCentral AWS server WITHOUT having to install the full, heavy 
MeshCentral server package (50+ MB) on the application host.


2. CONTENTS OF THIS FOLDER
--------------------------
  - meshctrl.js        : The standalone MeshCentral command-line interface tool.
  - package.json       : Defines the two minimal dependencies required by meshctrl:
                         * "ws" (WebSocket client)
                         * "minimist" (Command-line arguments parser)
  - package-lock.json  : Deterministic dependency lockfile for npm.
  - node_modules/      : Installed runner dependencies for meshctrl.js.


3. HOW THE ENTERPRISE APPLICATION USES IT
-----------------------------------------
When an employee interacts with the Self-Help AI Copilot or when an issue is 
escalated to L2 Support:

  a) Device Discovery:
     backend/services/meshcentral_service.py calls:
     node backend/bin/meshctrl.js ListDevices --json --url <MESHCENTRAL_URL> ...
     This identifies the user's online machine (e.g., AVDAILAB79-13).

  b) Remote Remediation (Zoom Cache Clear):
     meshcentral_service.py calls:
     node backend/bin/meshctrl.js RunCommand --id <NODE_ID> --run <POWERSHELL_SCRIPT> ...
     This stops frozen Zoom processes and cleans corrupted cache files directly 
     on the user's endpoint.

  c) 30-Minute Ephemeral Remote Desktop Link:
     meshcentral_service.py calls:
     node backend/bin/meshctrl.js DeviceSharing --id <NODE_ID> --add "L2-Support" --duration 30 ...
     This creates a temporary, self-expiring remote desktop sharing link that is
     automatically stored in the Jira Cloud ticket and Support Dashboard.


4. ENVIRONMENT CONFIGURATION (.env)
-----------------------------------
In your Meridian Enterprise Application .env file, configure the following:

  # Relative path to the bundled meshctrl.js (no machine-specific path needed)
  MESHCTRL_PATH=backend/bin/meshctrl.js

  # Deployed MeshCentral server WebSocket endpoint
  MESHCENTRAL_URL=wss://meshcentral-nlb-57f1b2a74defca19.elb.us-east-1.amazonaws.com

  # MeshCentral administrative credentials
  MESHCENTRAL_USER=admin-sd
  MESHCENTRAL_PASS=smartfix@1


5. HOW AUTOMATIC PATH RESOLUTION WORKS
--------------------------------------
In backend/services/meshcentral_service.py, the function find_meshctrl_executable() 
automatically resolves the script path in the following order:

  1. MESHCTRL_PATH environment variable (supports relative paths like "backend/bin/meshctrl.js")
  2. Bundled repository path: backend/bin/meshctrl.js
  3. Project node_modules: ./node_modules/meshcentral/meshctrl.js
  4. Standard Linux / Docker paths:
     - /app/backend/bin/meshctrl.js
     - /usr/local/lib/node_modules/meshcentral/meshctrl.js
     - /app/node_modules/meshcentral/meshctrl.js


6. HOW TO DEPLOY ON SERVERS & CONTAINERS
----------------------------------------

Option A: Standard Linux VM (AWS EC2 / Ubuntu / Debian)
  1. Ensure Python 3.10+ and Node.js 18+ are installed:
       sudo apt-get update
       sudo apt-get install -y python3 python3-pip nodejs npm
  2. Install application Python dependencies:
       pip install -r requirements.txt
  3. Install the bin dependencies:
       cd backend/bin
       npm install
       cd ../..
  4. In .env, set:
       MESHCTRL_PATH=backend/bin/meshctrl.js
  5. Run the application:
       python run.py

Option B: Docker Container
  Add Node.js to your Dockerfile and install bin dependencies:

       FROM python:3.11-slim
       RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
       WORKDIR /app
       COPY . /app
       RUN pip install --no-cache-dir -r requirements.txt
       RUN cd /app/backend/bin && npm install
       ENV MESHCTRL_PATH=/app/backend/bin/meshctrl.js
       ENV MESHCENTRAL_URL=wss://meshcentral-nlb-57f1b2a74defca19.elb.us-east-1.amazonaws.com
       EXPOSE 8001
       CMD ["python", "run.py"]


7. MANUAL CLI VERIFICATION COMMAND
----------------------------------
To verify that this bin runner can connect to MeshCentral from any terminal:

Windows (PowerShell):
  node backend\bin\meshctrl.js ListDevices --url "wss://meshcentral-nlb-57f1b2a74defca19.elb.us-east-1.amazonaws.com" --loginuser "admin-sd" --loginpass "smartfix@1"

Linux / Bash:
  node backend/bin/meshctrl.js ListDevices --url "wss://meshcentral-nlb-57f1b2a74defca19.elb.us-east-1.amazonaws.com" --loginuser "admin-sd" --loginpass "smartfix@1"

Expected output:
  Device group: "smartfix-poc"
  id, name, icon, conn, pwr
  -------------------------
  "3PLI6CuViWqjKLkTgGFaU5ymrZ3yt@GeGhDGA6U$0M$HZQMakvOSzB4elf6iS@EW", "AVDAILAB79-13", 8, 1, 1
===============================================================================
