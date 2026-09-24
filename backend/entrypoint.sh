#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:29519
