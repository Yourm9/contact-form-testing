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
if [ ! -d /root/contact-form-testing ]; then
  git clone https://github.com/Yourm9/contact-form-testing.git /root/contact-form-testing
fi

cd /root/contact-form-testing

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt || pip install flask playwright gunicorn

# Install Playwright browsers and dependencies
playwright install
playwright install-deps

# Create and enable cft systemd service
echo "🔧 Setting up systemd service..."

cat <<EOF > /etc/systemd/system/cft.service
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

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable cft
systemctl start cft

echo "✅ Systemd service created and started (cft.service)"

# --- Deployment Script ---
echo "📄 Creating deploy.sh..."
cat << 'EOF' > /root/contact-form-testing/deploy.sh
#!/bin/bash
set -e

cd /root/contact-form-testing

echo "📥 Pulling latest changes from GitHub..."
git reset --hard
git pull origin main

echo "🔄 Restarting systemd service..."
systemctl restart cft

echo "✅ Deployed and restarted"
EOF

chmod +x /root/contact-form-testing/deploy.sh

# --- Webhook Listener ---
echo "🐍 Creating webhook.py..."
cat << 'EOF' > /root/contact-form-testing/webhook.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook received. Deploying...")
        subprocess.run(["/root/contact-form-testing/deploy.sh"])

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 9000), WebhookHandler)
    print("🚀 Webhook server running on port 9000...")
    server.serve_forever()
EOF

# --- Webhook Service ---
echo "🛠️ Creating webhook.service..."
cat << 'EOF' > /etc/systemd/system/webhook.service
[Unit]
Description=GitHub Webhook Listener
After=network.target

[Service]
ExecStart=/root/contact-form-testing/venv/bin/python /root/contact-form-testing/webhook.py
WorkingDirectory=/root/contact-form-testing
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Enabling and starting webhook service..."
systemctl daemon-reload
systemctl enable webhook
systemctl start webhook

echo "✅ Webhook service created and running on port 9000"
