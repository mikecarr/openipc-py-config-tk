# OpenIPC py-config-tk

Configurator app in Python

Key Features
* Tabs: Includes tabs for wfb.conf, majestic.yaml, and application logs.
* SSH Connection: Connects to a remote device via SSH and retrieves configuration files.
* Save Functions:
    * Save Log: Allows users to save logs to a text file.
    * Save Majestic YAML: Collects updated YAML entries and saves them to a specified path.

## Setup
```
python -m venv .venv
source .venv/bin/activate 
pip install -r requirements.txt

python app.py
```


## Images
* Tabs
![WFB](images/tab-wfb.png)
![Majestic](images/tab-majestic.png)
![Log](images/tab-logs.png)