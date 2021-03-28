FROM python:3.8.8-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install python-dotenv

COPY . .