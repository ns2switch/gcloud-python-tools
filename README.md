# Gcloud parser
#### v 0.1 

This is a gcloud parser that browses through project's log and saves them according to their type.

There are two versions:
    - gcp-mass-download: download logs from all the projects recursively
    - gcp-gclod-parser: allow download logs for a project.

### requirements 

- Need gcloud CLI installed in the running system. https://cloud.google.com/sdk/docs/install
- Need a file called service-account.json in the same directory as the .py with the sufficient permissions to access
resources. This file must be a service account key file.

##usage:
- gcp-mass-download:
    Can download files per type in all the projects under your accounts:
    - gcp-mass-download -h --> show help.
    - gcp-mass-download --log_type audit --> download audit logs from all the projects
    - gcp-mass-download --log_type audit --start 1 month ago -end today --> download all audit logs from the projects in
      the timestamp selected.
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



