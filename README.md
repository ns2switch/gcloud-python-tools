# Gcloud parser
#### v 0.8

This is a gcloud parser that browses through project's log and saves them according to their type.

- gcp-mass-native.py: download logs from all projects recursively using native python library, can also download a single project

### requirements:

- Need a file called service-account.json in the same directory as the .py with the sufficient permissions to access
resources. This file must be a service account key file.

## Installation:

~~~

python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
mkdir data
./gcp-mass-native.py -h

~~~

## usage:
all logs and files are saved in data/ dir. This dir needs to be created before run the program.


- gcp-mass-native.py:
    Can download files per type in all the projects under your accounts:

- usage example:
~~~
    gcp-mass-native.py -h --> show help.

    gcp-mass-native --log_type audit --> download audit logs from all the projects

    gcp-mass-native --log_type audit --resume yes --> download audit logs from all the projects, resuming from the last project 

    gcp-mass-native --log_type audit --start '1 month ago' --end today --> download all audit logs from the projects in the timestamp selected.

    gcp-mass-native --log_type audit --start '1 month ago' --end now --select_project yes --> download audit logs
      from the projects in the timestamp selected..
~~~ 


