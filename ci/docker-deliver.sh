#!/bin/bash

REPO_PATH="/home/centos/elastic-indices-lifecycle/"

cd "${REPO_PATH}" && git pull origin master || :
git push github master 

docker-compose build
docker-compose push