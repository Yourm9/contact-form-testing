#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export APT_LISTCHANGES_FRONTEND=none

# Exit on errors
set -e

# Wait for apt to be free with timeout and auto-kill
echo "⏳ Waiting for apt to be free (timeout after 5 minutes)..."
timeout=300
elapsed=0

while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed + 1))
    if [ "$elapsed" -ge "$timeout" ]; then
        echo "⚠️ apt is still locked after $timeout seconds. Killing any stuck process..."
        pid=$(lsof -t /var/lib/dpkg/lock-frontend)
        if [ -n "$pid" ]; then
            echo "🔪 Killing process $pid..."
            kill -9 "$pid"
        fi
        break
    fi
done

# Auto-fix if dpkg is interrupted
echo "🛠 Checking for interrupted dpkg state..."
dpkg --configure -a || true

# Update system and try fix-missing on error
echo "📦 Updating system packages..."
apt update --fix-missing
apt -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade -y

# Install system dependencies
echo "📥 Installing system libraries..."
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
echo "🎭 Installing Playwright and dependencies..."
playwright install || echo "⚠️ playwright install failed, check manually"
playwright install-deps || echo "⚠️ playwright install-deps failed, continuing anyway"

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

# --- Webhook Listener with Logging ---
echo "🐍 Creating webhook.py with logging..."
cat << 'EOF' > /root/contact-form-testing/webhook.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import logging

# Set up logging to file
logging.basicConfig(
    filename='/var/log/webhook.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        logging.info("Webhook received. Running deploy script...")
        try:
            subprocess.run(["/root/contact-form-testing/deploy.sh"], check=True)
            logging.info("Deploy completed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Deploy script failed: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook received. Deploying...")

if __name__ == "__main__":
    logging.info("🚀 Webhook server starting on port 9000...")
    server = HTTPServer(('0.0.0.0', 9000), WebhookHandler)
    server.serve_forever()
EOF

# --- Webhook systemd service ---
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
