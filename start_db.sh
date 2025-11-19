#! /bin/bash


sudo docker compose --env-file .env -f tests/docker-compose.yml pull
sudo docker compose --env-file .env -f tests/docker-compose.yml down
sudo docker compose --env-file .env -f tests/docker-compose.yml up -d --force-recreate --remove-orphans
