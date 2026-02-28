#!/usr/bin/env bash
# exit on error
set -o errexit

# Install required system dependencies (OpenCV needs libGL)
# Note: Render uses standard Ubuntu. It might not support apt-get directly in build script
# without a Docker image, but we'll try the python environment approach.

# Update pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Convert static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
