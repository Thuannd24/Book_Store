#!/bin/sh
set -e

# Wait for PostgreSQL to be ready
until python -c "
import os, psycopg2
url = os.getenv('POSTGRES_MIGRATION_URL', '')
if url:
    psycopg2.connect(url).close()
" >/dev/null 2>&1; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

# Wait for MongoDB to be ready
until python -c "import os; from pymongo import MongoClient; MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'), serverSelectionTimeoutMS=3000).admin.command('ping')" >/dev/null 2>&1; do
  echo "Waiting for MongoDB to be ready..."
  sleep 1
done

# Run Django migrations to create PostgreSQL tables
python manage.py makemigrations comment_rate
python manage.py migrate --noinput

python -m comment_rate.infrastructure.migrate_postgres_to_mongo

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3