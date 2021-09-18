FROM python:3.9

ENV PYTHONUNBUFFERED=1

WORKDIR /movies_admin

COPY requirements requirements

RUN pip install -r requirements/prod.txt

COPY . .