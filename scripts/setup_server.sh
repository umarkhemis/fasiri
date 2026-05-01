#!/bin/bash
# ============================================================
# Fasiri – DigitalOcean Server Setup Script
# Ubuntu 22.04 LTS ($6/month Droplet)
#
# Run this ONCE on a fresh droplet as root:
#   curl -sL https://raw.githubusercontent.com/umarkhemis/fasiri/main/scripts/setup_server.sh | bash
#
# What this does:
#   1. Hardens the server (firewall, fail2ban, unattended upgrades)
#   2. Installs Docker + Docker Compose
#   3. Creates a deploy user
#   4. Clones the repo and starts the app
#   5. Sets up Let's Encrypt SSL
# ============================================================

set -euo pipefail

DOMAIN="${DOMAIN:-api.fasiri.io}"          # override: DOMAIN=myapi.com bash setup.sh
DEPLOY_USER="fasiri"
APP_DIR="/opt/fasiri"
REPO_URL="https://github.com/umarkhemis/fasiri.git"

echo "======================================================"
echo "  Fasiri Production Server Setup"
echo "  Domain: $DOMAIN"
echo "======================================================"

# ── 1. System updates ─────────────────────────────────────
echo ""
echo "--> Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    curl git ufw fail2ban \
    ca-certificates gnupg lsb-release \
    unattended-upgrades apt-listchanges

# Auto security updates
dpkg-reconfigure -f noninteractive unattended-upgrades

# ── 2. Firewall ───────────────────────────────────────────
echo ""
echo "--> Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw --force enable
ufw status

# ── 3. Fail2ban ───────────────────────────────────────────
echo ""
echo "--> Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = /var/log/auth.log
EOF
systemctl enable fail2ban
systemctl restart fail2ban

# ── 4. Docker ─────────────────────────────────────────────
echo ""
echo "--> Installing Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y -qq \
    docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

# ── 5. Deploy user ────────────────────────────────────────
echo ""
echo "--> Creating deploy user: $DEPLOY_USER..."
id -u $DEPLOY_USER &>/dev/null || useradd -m -s /bin/bash $DEPLOY_USER
usermod -aG docker $DEPLOY_USER

# ── 6. Clone repo ─────────────────────────────────────────
echo ""
echo "--> Cloning Fasiri repo to $APP_DIR..."
mkdir -p $APP_DIR
git clone $REPO_URL $APP_DIR 2>/dev/null || (cd $APP_DIR && git pull)
chown -R $DEPLOY_USER:$DEPLOY_USER $APP_DIR

# ── 7. Create .env ────────────────────────────────────────
echo ""
echo "--> Creating .env from template..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp $APP_DIR/env.example $APP_DIR/.env
    # Generate a secure secret key
    SECRET=$(openssl rand -hex 32)
    sed -i "s|change-me-in-production-use-openssl-rand-hex-32|$SECRET|" $APP_DIR/.env
    sed -i "s|BASE_URL=http://localhost:8000|BASE_URL=https://$DOMAIN|" $APP_DIR/.env
    echo ""
    echo "  *** IMPORTANT: Edit $APP_DIR/.env and add your API keys ***"
    echo "      HUGGINGFACE_API_KEY=hf_..."
    echo "      SUNBIRD_API_KEY=ey..."
    echo "      REDIS_URL=redis://redis:6379/0  (already set)"
fi

# ── 8. SSL via Certbot ────────────────────────────────────
echo ""
echo "--> Installing Certbot for SSL..."
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot

echo ""
echo "  To get your SSL certificate, run:"
echo "  certbot certonly --standalone -d $DOMAIN"
echo ""
echo "  Then copy certs:"
echo "  cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $APP_DIR/nginx/ssl/"
echo "  cp /etc/letsencrypt/live/$DOMAIN/privkey.pem   $APP_DIR/nginx/ssl/"
echo ""
echo "  Update $APP_DIR/nginx/conf.d/fasiri.conf:"
echo "  Replace YOUR_DOMAIN with: $DOMAIN"

# ── 9. Systemd service ────────────────────────────────────
echo ""
echo "--> Creating systemd service..."
cat > /etc/systemd/system/fasiri.service << EOF
[Unit]
Description=Fasiri API
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always
RestartSec=10
User=$DEPLOY_USER

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable fasiri

# ── 10. SSL cert auto-renewal ─────────────────────────────
echo ""
echo "--> Setting up SSL auto-renewal..."
cat > /etc/cron.d/certbot-renewal << 'EOF'
0 2 * * * root certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/*/fullchain.pem /opt/fasiri/nginx/ssl/ && cp /etc/letsencrypt/live/*/privkey.pem /opt/fasiri/nginx/ssl/ && docker compose -f /opt/fasiri/docker-compose.yml restart nginx"
EOF

echo ""
echo "======================================================"
echo "  Setup complete!"
echo "======================================================"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Edit your API keys:"
echo "     nano $APP_DIR/.env"
echo ""
echo "  2. Get SSL certificate:"
echo "     certbot certonly --standalone -d $DOMAIN"
echo "     cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $APP_DIR/nginx/ssl/"
echo "     cp /etc/letsencrypt/live/$DOMAIN/privkey.pem   $APP_DIR/nginx/ssl/"
echo ""
echo "  3. Update the domain in nginx config:"
echo "     sed -i 's/YOUR_DOMAIN/$DOMAIN/g' $APP_DIR/nginx/conf.d/fasiri.conf"
echo ""
echo "  4. Start the application:"
echo "     cd $APP_DIR && docker compose up -d --build"
echo ""
echo "  5. Verify it's running:"
echo "     curl https://$DOMAIN/health"
echo ""
echo "  Your API will be live at: https://$DOMAIN"
echo "  Docs will be at:          https://$DOMAIN/docs"
echo ""
