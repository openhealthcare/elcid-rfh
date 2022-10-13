## Purpose
At present the steps in this readme should:

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

`cd deployment`

Then run

`docker build -t rfh_ansible_image . `

This builds you the docker container as laid our by the Dockerfile file.

### 2. Create the docker conatiner
Run `docker run -d -P --name rfh_app_container rfh_ansible_image`
Run `docker run -d -P --name rfh_db_container rfh_ansible_image`


This will create you a docker container.

Run `docker port rfh_app_container`
and `docker port rfh_db_container`

This will show you the port forwarding configurations for http (80), ssh (22) and postgres (5432) for this container

Add an entry to your `./ssh/config` file for the container e.g.

```
Host elcidwebserver
HostName 0.0.0.0
User ohc
Port 55003
```

Run `ssh-copy-id elcidwebserver` to allow passwordless ssh in future - the password is *ohc*

You need to wire the db container to the app container. This is done using the bridge that docker sets up by default.

Run `docker inspect rfh_db_container`, put the value of `Networks.bridge.IPAddress` into DB_ADDRESS in group_vars/all


### 3. Deployment

Create a python 3 virtualenv

Run `pip install -r requirements.txt` - this should be the requirements file located at ./deployment/requirements.txt

Update *hosts.dev* to point to the container, as configured by your `.ssh/config` e.g.

```
[webserver]
elcidwebserver
```

Create an ansible.cfg that looks something like

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
