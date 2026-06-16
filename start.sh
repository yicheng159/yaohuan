#!/bin/bash

echo "=== Starting Yaohuan Backend ==="
echo "Python version: $(python --version)"
echo "Environment:"
echo "  SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "  DEBUG: ${DEBUG}"
echo "  DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "  PORT: ${PORT}"

echo ""
echo "=== Running migrations ==="
python manage.py migrate --noinput

echo ""
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo ""
echo "=== Starting server ==="
gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 myproject.wsgi:application