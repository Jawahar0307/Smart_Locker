#!/usr/bin/env bash
# =============================================================================
# Render Build Script – Smart Storage Locker Management System
# This script is executed during each deploy on Render.
# =============================================================================

set -o errexit  # Exit on error

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate --no-input

echo "==> Build complete!"
