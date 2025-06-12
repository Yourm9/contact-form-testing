#!/bin/bash

# --- SETUP VARIABLES ---
REPO_URL="https://github.com/yourm9/contact-form-testing.git"
APP_DIR="contact-form-testing"
PYTHON_VERSION="python3"
PORT=5000

# --- UPDATE AND INSTALL DEPENDENCIES ---
echo "[1/6] Updating system..."
apt update && apt upgrade -y

# Install essential packages
echo "[2/6] Installing Python, pip, Git, and Playwright deps..."
apt install -y $PYTHON_VERSION $PYTHON_VERSION-venv $PYTHON_VERSION-dev git curl unzip ffmpeg

# --- CLONE OR UPDATE REPO ---
if [ ! -d "$APP_DIR" ]; then
  echo "[3/6] Cloning repository..."
  git clone "$REPO_URL"
else
  echo "[3/6] Pulling latest code..."
  cd "$APP_DIR"
  git pull origin main
  cd ..
fi

# --- SETUP PYTHON ENV ---
echo "[4/6] Creating Python virtual environment..."
cd "$APP_DIR"
$PYTHON_VERSION -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
playwright install

# --- OPTIONAL: CLEAN RESULTS ---
echo "[5/6] Clearing results.csv..."
echo "timestamp,domain,contact_url,status,fields_filled" > results.csv

# --- RUN GUNICORN ---
echo "[6/6] Starting app with Gunicorn..."
nohup venv/bin/gunicorn app:app --bind 0.0.0.0:$PORT > server.log 2>&1 &

# Done
echo "✅ Setup complete. App running on http://$(curl -s ifconfig.me):$PORT"
