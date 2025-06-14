#!/bin/bash

# Exit on errors
set -e

# Update system
apt update && apt upgrade -y

# Install system dependencies
apt install -y python3 python3-venv python3-pip git curl unzip wget \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libpango-1.0-0 libcairo2 libasound2

# Clone repo if not already
if [ ! -d ~/contact-form-testing ]; then
  git clone https://github.com/Yourm9/contact-form-testing.git ~/contact-form-testing
fi

cd ~/contact-form-testing

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt || pip install flask playwright gunicorn

# Install Playwright browsers and dependencies
playwright install
playwright install-deps

# Run app with Gunicorn
pkill gunicorn || true
gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 180

echo "🔧 Setting up systemd service..."

cat <<EOF | sudo tee /etc/systemd/system/cft.service
[Unit]
Description=Gunicorn Contact Form Tester Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/contact-form-testing
Environment="PATH=/root/contact-form-testing/venv/bin"
ExecStart=/root/contact-form-testing/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 180
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable cft
sudo systemctl start cft

echo "✅ Systemd service created and started (cft.service)"
