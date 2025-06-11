#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Update package list and install ffmpeg and pip
echo "Updating package list and installing dependencies (apt-utils, ffmpeg, python3-pip)..."
apt-get update -y
apt-get install -y apt-utils ffmpeg python3-pip

# Install Python dependencies from requirements.txt
if [ -f requirements.txt ]; then
  echo "Installing Python dependencies from requirements.txt..."
  pip3 install --no-cache-dir -r requirements.txt
else
  echo "Error: requirements.txt not found!"
  exit 1
fi

# Run the Streamlit application
# Defaults for server.enableCORS and server.enableXsrfProtection are true, which is good.
echo "Starting Streamlit application on port 9000..."
streamlit run app.py --server.port=9000 --server.address=0.0.0.0 --server.headless=true

echo "Application started."
