FROM python:3.8.0

RUN apt-get update && \
    apt-get install -y postgresql-contrib nginx supervisor gettext pandoc unixodbc-dev netcat

RUN mkdir /app
# set work directory

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt ./app/requirements.txt
RUN pip install -r /app/requirements.txt

# copy project
COPY ./ /app/

WORKDIR /app