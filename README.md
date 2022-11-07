Gcloud parser

v 0.02

==requirements ==

Need a file called service-account.json in the same directory as the .py with the sufficient permissions to access
resources.

This file must be a service account key file.

====Docker image ===

If you don't want install gcloud on you system you can create a Docker image:

Copy service-account.json inside directory

execute:
sudo docker build --tag gparser .

when build finished execute:

sudo docker run -ti --rm gparser


