# Hosting EQ on Hostinger VPS (with Firebase)

This guide explains how to deploy the EQ application on a Hostinger VPS using **Firebase** as the backend storage. 

## 1. Firebase Setup (Crucial)
Since we've migrated to Firebase, you no longer need to setup a MySQL database on your VPS. However, you MUST provide the service account key.

1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Open your project.
3.  Go to **Project Settings** > **Service Accounts**.
4.  Click **Generate new private key**.
5.  Save the file as `service account key.json` and upload it to your VPS in the root folder of the app.

## 2. Server Setup
Connect to your VPS via SSH and run the following:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Pip
sudo apt install python3 python3-pip python3-venv -y

# Clone your repository (if applicable) or upload via FileZilla
# cd /path/to/eq1

# Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Environment Variables
Create a `.env` file or export them in your shell:

```bash
export OPENROUTER_API_KEY="your_api_key"
export SECRET_KEY="your_flask_secret"
export FLASK_DEBUG="False"
```

## 4. Running with Gunicorn
To keep the app running in the background, use Gunicorn and a systemd service.

### Create Systemd Service
`sudo nano /etc/systemd/system/eq.service`

```ini
[Unit]
Description=Gunicorn instance to serve EQ
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/eq1
Environment="PATH=/root/eq1/venv/bin"
Environment="OPENROUTER_API_KEY=your_key"
Environment="SECRET_KEY=your_secret"
ExecStart=/root/eq1/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5001 app:app

[Install]
WantedBy=multi-user.target
```

### Start Service
```bash
sudo systemctl start eq
sudo systemctl enable eq
```

## 5. Nginx Proxy (Optional but Recommended)
Setup Nginx to handle traffic and SSL.

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/eq
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        include proxy_params;
        proxy_pass http://localhost:5001;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/eq /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

EQ is now live on your VPS! 🚀
