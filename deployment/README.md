## Purpose
At present the steps in this readme should.

* Create a docker container
* Create a postgres database
* Create the application
* Install and setup nginx and circus

It does not
* Run backups
* Deploy cron jobs
* Restore from a backup


## Stages

### 1. Create the docker images
First install docker by following the instructions here https://docs.docker.com/desktop/install/mac-install/

Then run sudo docker build -t rfh_ansible_image .
This builds you the docker container as laid our by
the Dockerfile file.

Create your ssh key `ssh-keygen -f rfh.pem -t rsa -b 4096`
this will be used to access your new container after you create it.

### 2. Create the docker conatiner
Run `docker run -d -P --name rfh_app_container rfh_ansible_image`
Run `docker run -d -P --name rfh_db_container rfh_ansible_image`


This will create you a docker container.

Run `docker port rfh_app_container`
and `docker port rfh_db_container`

This will show you the ports to ssh into the container with.

`ssh-copy-id -p {{ ssh port }} ohc@0.0.0.0` to allow access by our pem file the password is *ohc*

You need to wire the db container to the app container. This is done using the bridge that docker sets up by default.

Run `docker inspect rfh_db_container`, put the value of `Networks.bridge.IPAddress` into DB_ADDRESS in group_vars/all


### 3. Deployment
Create a virtualenv pointing to python 3.8.6

Run `pip install -r requirements.txt`
Create an ansible.cfg that looks someting like

```
[defaults]
inventory = hosts.dev
allow_world_readable_tmpfiles=true
host_key_checking = false
```


Run `ansible-playbook setup_prod.yml` to setup a prod server
Run `ansible-playbook setup_test.yml` to setup a test server

If you go to *0.0.0.0:{{ http port }}* you should see your application.

## Rerunning deployment
Run `docker container rm -f rfh_db_container`
Run `docker container rm -f rfh_app_container`

Run steps 2 onwards.
