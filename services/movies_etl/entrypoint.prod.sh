#!/bin/sh

echo "Waiting for postgres and elasticsearch..."

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1s
done

echo "PostgreSQL started"

while ! nc -z "$ELASTICSEARCH_HOST" "$ELASTICSEARCH_PORT"; do
  sleep 0.1s
done

echo "Elasticsearch started"

exec "$@"