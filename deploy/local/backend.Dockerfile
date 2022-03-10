FROM python:3.8

LABEL maintainer="Keith Cheveralls <keith.cheveralls@czbiohub.org>"

RUN apt-get update

COPY requirements.txt /opencell/requirements.txt

WORKDIR /opencell

RUN pip install -r requirements.txt

COPY . /opencell

RUN pip install -e .

COPY ./deploy/local/docker-entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
