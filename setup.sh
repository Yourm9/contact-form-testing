#!/bin/bash

set -e

echo "📦 Updating system..."
apt update && apt upgrade -y

echo "🐍 Installing Python & dependencies..."
apt install -y python3 python3-pip python3-venv git curl

echo "🚀 Cloning project repo..."
git clone https://github.com/Yourm9/contact-form-testing.git
cd contact-form-testing

echo "📁 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install flask gunicorn playwright

echo "🧱 Installing Playwright browsers & system deps..."
playwright install --with-deps || true

echo "🌐 Exposing Flask server on port 5000..."
echo "Use: SERVER_ENV=true python3 app.py OR launch with Gunicorn:"
echo "gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 180"

