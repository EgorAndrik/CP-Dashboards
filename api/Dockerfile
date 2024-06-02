FROM condaforge/mambaforge as env
ARG DEBIAN_FRONTEND=noninteractive

RUN apt update -y && apt upgrade -y 


FROM python:3.11-alpine as prod

# RUN pip install pyuwsgi
RUN apk update && apk add gcc openssl openssl-dev python3-dev build-base linux-headers pcre-dev
RUN pip install pyuwsgi

RUN CFLAGS="-I/usr/local/opt/openssl/include" LDFLAGS="-L/usr/local/opt/openssl/lib" \
  UWSGI_PROFILE_OVERRIDE=ssl=true pip3 install uwsgi -Iv

WORKDIR /app

RUN python -m venv /opt/venv
# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY flaskr flaskr

COPY uwsgi.ini .

CMD [ "uwsgi", "uwsgi.ini"]

FROM env as dev
RUN conda create -n cenv python=3.11

COPY requirements.txt .
RUN conda run --no-capture-output -n cenv pip install -Ur requirements.txt
