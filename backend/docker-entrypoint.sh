#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "
import os, sys, time
from sqlalchemy import create_engine, text
url = os.environ.get('DATABASE_URL', '')
for i in range(30):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(1)
"; do
  echo "Database unavailable - retrying..."
  sleep 2
done

echo "Running database migrations..."
cd /app/backend && alembic upgrade head

echo "Starting API server..."
exec "$@"
