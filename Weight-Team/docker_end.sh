docker stop $(docker ps -aq) && docker rm $(docker ps -aq) && docker rmi $(docker ps -aq) && docker-compose down -v
