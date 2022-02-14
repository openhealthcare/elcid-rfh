`sudo docker build -t rfh_ansible_image .`

`docker run -d -P --name rfh_ansible_container rfh_ansible_image`

# find the port
`sudo docker port rfh_ansible_container`

update the ssh config

# find the ip address
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' rfh_ansible_container

For whatever reason we can't ssh via the port we need to ssh via the port mapping.


You can find out the port mapping with `docker port`

for me you run `ssh -v root@localhost -p 55006`

I found it easier to update my ssh config with `rfh-ansible`

password is **mypassword**

### generating a pem file
you should not need to do this, we've done it but...
`ssh-keygen -f rfh.pem -t rsa -b 4096` generates our local pem file
`ssh-copy-id rfh-ansible`


### deploying
`ansible-playbook setup_prod.yml`


### TODO
1. Set up the backups
2. Set up the restore
3. Split out the rfh database to deploy to a seperate server
4. Split out the cron job to split out to a seperate server
5. Add in ansible vault and the encrypted variables
6. Add in database restore
