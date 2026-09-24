#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

exec gunicorn config.wsgi_application --bind 0.0.0.0:29519
