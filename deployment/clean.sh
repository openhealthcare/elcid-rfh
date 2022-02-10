docker stop rfh_ansible_container
docker rm rfh_ansible_container
docker rmi rfh_ansible_image
sudo docker build -t rfh_ansible_image .
docker run -d -P --name rfh_ansible_container rfh_ansible_image
sudo docker port rfh_ansible_container
