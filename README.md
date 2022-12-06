# Gcloud parser
#### v 0.2 

This is a gcloud parser that browses through project's log and saves them according to their type.

There are two versions:
    - gcp-mass-download: download logs from all the projects recursively using gcloud CLI
    - gcp-gcloud-parser.py: allow download logs for a project.
    - gcp-mass-native.py: download logs from all projects recursively using native python library

### requirements 

For gcp-mass-download and gcp-cloud-parser:
- Need gcloud CLI installed in the running system. https://cloud.google.com/sdk/docs/install
For all the files:
- Need a file called service-account.json in the same directory as the .py with the sufficient permissions to access
resources. This file must be a service account key file.

##usage:
all logs and files are saved in data/ dir. This dir needs to be created before run the program.

- gcp-mass-native.py:
    Can download files per type in all the projects under your accounts:
- usage example:
~~~
    gcp-mass-download -h --> show help.
    gcp-mass-download --log_type audit --> download audit logs from all the projects
    gcp-mass-download --log_type audit --start '1 month ago' --end today --> download all audit logs from the projects in
      the timestamp selected.
    gcp-mass-download --log_type audit --start '1 month ago' --end today --format json --> download all audit logs
      from the projects in the timestamp selected with format json.
~~~ 

- gcp-mass-download:
    Can download files per type in all the projects under your accounts:
- usage example:
~~~
    gcp-mass-download -h --> show help.
    gcp-mass-download --log_type audit --> download audit logs from all the projects
    gcp-mass-download --log_type audit --start '1 month ago' --end today --> download all audit logs from the projects in
      the timestamp selected.
    gcp-mass-download --log_type audit --start '1 month ago' --end today --format json --> download all audit logs
      from the projects in the timestamp selected with format json.      
~~~
- gcp-gcloud-parser:
    Can download files per type in one projects.

### Docker image 

If you don't want to install gcloud CLI on you system you can create a Docker image:

1. Copy service-account.json inside directory

2. execute:
~~~
sudo docker build --tag gparser .

~~~

3. when build finished create volume data inside your home directory and execute:

~~~
sudo docker run -ti --rm -v ~./data:/app/data gparser
~~~



