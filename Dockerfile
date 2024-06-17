FROM python:3.12-slim
RUN apt-get update

COPY ./requirements-dev.txt .

RUN python3 -m pip install -r ./requirements-dev.txt

COPY . /app
WORKDIR /app

VOLUME [ "/app" ]

CMD [ "tail", "-f", "/dev/null" ]
