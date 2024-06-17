#! /bin/bash

NAME=${1:-"league_predictor"}
TAG=${2:-"latest"}
CONTAINER_NAME=$NAME

docker build -t ${NAME}:${TAG} -f ./Dockerfile .

if [ "$( docker container inspect -f '{{.State.Status}}' $CONTAINER_NAME)" != "running" ]; then
    docker run --name ${CONTAINER_NAME} -d ${NAME}:${TAG} 
fi
