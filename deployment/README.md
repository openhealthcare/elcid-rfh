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

### 1. Create the docker image
First install docker by following the instructions here https://docs.docker.com/desktop/install/mac-install/

Then run sudo docker build -t rfh_ansible_image .
This builds you the docker container as laid our by
the Dockerfile file.

### 2. Create the docker conatiner
Run `docker run -d -P --name rfh_ansible_container rfh_ansible_image`

This will create you a docker container.

Run `docker port rfh_ansible_container`

This will show you the ports to ssh into the container with.

`ssh-copy-id -p {{ ssh port }} ohc@0.0.0.0` to allow access by our pem file the password is *ohc*

### 3. Deployment
Create a virtualenv pointing to python 3.8.6

Run `pip install -r requirements.txt`

Update *hosts.dev* to point to the *rfh_ansible_container*

Run `ansible-playbook setup_prod.yml` to setup a prod server
Run `ansible-playbook setup_test.yml` to setup a test server

If you go to *0.0.0.0:{{ http port }}* you should see your application.

## Rerunning deployment
Run `docker container rm -f rfh_ansible_container`

Run steps 2 onwards.
