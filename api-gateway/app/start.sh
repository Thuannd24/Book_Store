#!/bin/sh
set -e

until python manage.py shell -c "from django.db import connections; connections['default'].cursor().execute('SELECT 1')" >/dev/null 2>&1; do
  echo "Waiting for database to be ready..."
  sleep 1
done

python manage.py makemigrations --noinput
python manage.py migrate --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
