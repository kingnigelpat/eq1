#!/bin/bash

# --- Configuration ---
DOMAIN_NAME=$1
if [ -z "$DOMAIN_NAME" ]; then
    echo "Usage: $0 your-domain-or-ip"
    exit 1
fi
APP_NAME="eq1"
APP_DIR="/var/www/$APP_NAME"
USER="www-data"  # Use Nginx user for simplicity
VENV_DIR="$APP_DIR/venv"

# --- Update System ---
echo "Updating apt..."
apt update && apt upgrade -y

# --- Install Dependencies ---
echo "Installing dependencies..."
apt install -y python3-pip python3-venv nginx ufw git python3-certbot-nginx

# --- Create App Directory (Assume already there if user cloned) ---
if [ ! -d "$APP_DIR" ]; then
    echo "Creating app directory at $APP_DIR..."
    mkdir -p $APP_DIR
    chown -R $USER:$USER $APP_DIR
    echo "Please copy your project files to $APP_DIR manually if you haven't already!"
    exit 1
fi

# Permissions fix (ensure your user can write, but app user owns it)
chown -R $USER:$USER $APP_DIR

# --- Virtual Environment ---
echo "Setting up Virtual Environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# Upgrade pip and install requirements
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
# Ensure gunicorn is installed
pip install gunicorn

# --- Systemd Service ---
echo "Creating Systemd Service..."
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"
cat <<EOF > $SERVICE_FILE
[Unit]
Description=Gunicorn instance to serve $APP_NAME
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$APP_NAME.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $APP_NAME
systemctl start $APP_NAME

# --- Nginx Configuration ---
echo "Creating Nginx Config..."
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
cat <<EOF > $NGINX_CONF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
    }
    
    # Increase upload size for PDFs
    client_max_body_size 10M;
}
EOF

ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# --- Firewall ---
ufw allow 'Nginx Full'
ufw allow ssh
ufw --force enable

echo "Setup Complete! Your app should be live at http://$DOMAIN_NAME"
element
