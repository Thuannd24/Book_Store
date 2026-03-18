#!/bin/sh
set -e

until python -c "import os; from pymongo import MongoClient; MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'), serverSelectionTimeoutMS=3000).admin.command('ping')" >/dev/null 2>&1; do
  echo "Waiting for MongoDB to be ready..."
  sleep 1
done

python -m comment_rate.infrastructure.migrate_postgres_to_mongo

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3