#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate --no-input || echo "==> Note: Migrations will run at container startup."

echo "==> Seeding initial coach & category data..."
python seed_initial_data.py || echo "==> Note: Data seeding will run at container startup."

echo "==> Build completed successfully!"
