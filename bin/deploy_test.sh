#!/bin/bash
#
# ./deploy_test.sh $branch_name $database_backup_location
# assumes you start in a deployment env

# delete the current env if it exists
rm -rf /usr/lib/ohc/elcidrfh-$1

# clone the new branch
fab clone_branch:$1

# cd to our new directory
cd /usr/lib/ohc/elcidrfh-$1

# create the deployment env of the new repo
fab create_deployment_env:$1

# run deploy test
/home/ohc/.virtualenvs/elcidrfh-$1-deployment/bin/fab deploy_test:$2
