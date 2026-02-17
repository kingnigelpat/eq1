# Deployment Preparation for Hostinger VPS

Your application is ready for deployment. Here are the steps to deploy on your Hostinger VPS (or any Ubuntu-based VPS).

## 1. Prerequisites
Ensure you have:
- Access to your VPS terminal (SSH).
- Python 3.10+ installed.
- Git installed.

## 2. Server Setup (First Time)

### Install Dependencies
Run these commands on your VPS:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git nginx -y
```

### Clone Your Repository
```bash
git clone <your-repo-url> eq1
cd eq1
```

### Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration (.env)
Create a `.env` file on the server with your production secrets:
```bash
nano .env
```
Paste your keys:
```text
FLASK_DEBUG=False
SECRET_KEY=your-secure-random-string-here
OPENROUTER_API_KEY=your-key
ELEVENLABS_API_KEY=your-key (if using)
```

## 4. Run with Gunicorn
Test it first:
```bash
gunicorn -c gunicorn_config.py app:app
```
If it runs without errors, press `Ctrl+C`.

## 5. Set Up Systemd Service (Keep it running)
Create a service file:
```bash
sudo nano /etc/systemd/system/eq1.service
```
Content:
```ini
[Unit]
Description=Gunicorn instance to serve EQ1
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/eq1
Environment="PATH=/root/eq1/venv/bin"
EnvironmentFile=/root/eq1/.env
ExecStart=/root/eq1/venv/bin/gunicorn -c gunicorn_config.py app:app

[Install]
WantedBy=multi-user.target
```
*Note: Adjust paths `/root/eq1` if you cloned elsewhere (e.g., `/home/username/eq1`).*

Start the service:
```bash
sudo systemctl start eq1
sudo systemctl enable eq1
```

## 6. Configure Nginx (Reverse Proxy)
Create site config:
```bash
sudo nano /etc/nginx/sites-available/eq1
```
Content:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and Restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/eq1 /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

## 7. Updates
To update later:
```bash
cd eq1
git pull
sudo systemctl restart eq1
```
