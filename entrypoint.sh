#!/bin/bash

echo "Waiting for postgres container to start..."
until PGPASSWORD=$DJANGO_DB_PASSWORD pg_isready -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT \
    -U $DJANGO_DB_USER -d $DJANGO_DB_NAME; do sleep 1; done \
    && PGPASSWORD=$DJANGO_DB_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT \
    -U $DJANGO_DB_USER -d $DJANGO_DB_NAME --list

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
exec "$@"
