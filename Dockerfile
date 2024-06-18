FROM python:3.12-slim

ARG USER_ID
ARG GROUP_ID

RUN groupadd --gid ${GROUP_ID} summoner \
    && useradd --create-home --no-log-init --uid ${USER_ID} --gid ${GROUP_ID} summoner

RUN apt-get update && apt-get -y install git

COPY ./requirements-dev.txt .

RUN python3 -m pip install -r ./requirements-dev.txt

COPY . /app
WORKDIR /app

VOLUME [ "/app" ]

USER summoner

CMD [ "tail", "-f", "/dev/null" ]
