#! /bin/bash

NAME=${1:-"league_predictor"}
TAG=${2:-"latest"}
CONTAINER_NAME=$NAME

if [ $GID ]; then
    GROUP_ID=$GID
else
    GROUP_ID=1001
fi

docker build \
    -t ${NAME}:${TAG} \
    -f ./Dockerfile \
    --build-arg="USER_ID=${UID}" \
    --build-arg="GROUP_ID=${GROUP_ID}" \
    --build-arg="GROUP_NAME=summoner" \
    --build-arg="USER_NAME='summoner'" \
    .

status="$( docker container inspect -f '{{.State.Status}}' ${CONTAINER_NAME} 2> /dev/null )"

if [ -z $status ]; then
    docker run --name ${CONTAINER_NAME} -d ${NAME}:${TAG} 
elif [ $status = "exited" ]; then
    docker start ${CONTAINER_NAME}
fi
