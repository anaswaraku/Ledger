# Ledger Web Application - Operations & Deployment Guide

This document describes how to deploy, secure, and maintain the Ledger Web Application in a production environment.

---

## 1. Production Deployment Guide

### Recommended System Specifications
- **Operating System**: Ubuntu 22.04 LTS (or similar Debian-based Linux distribution)
- **Memory**: Minimum 1GB RAM (2GB recommended for multiple journals and reports rendering)
- **Storage**: SSD with at least 10GB free space (scaled to transaction logs size)
- **Software**: Docker Engine and Docker Compose V2

### Step 1: Initial Server Setup & Firewall
Ensure the system firewall is active and only allows required incoming traffic:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Step 2: Clone Code & Configure Production Environment
1. Clone the repository to `/opt/ledger-web`:
   ```bash
   sudo git clone <repository-url> /opt/ledger-web
   sudo chown -R $USER:$USER /opt/ledger-web
   cd /opt/ledger-web
   ```
2. Create the production `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` to configure production-specific credentials:
   - **`POSTGRES_HOST`**: Set to `db` (since it matches the database container name in `docker-compose.yml`).
   - **`POSTGRES_PASSWORD`**: Replace the default `ledgeweb` with a strong random string.
   - **`SECRET_KEY`**: Generate a secure JWT signing key by running `python3 -c "import secrets; print(secrets.token_hex(32))"` and pasting it here.

### Step 3: Run the Application with Docker Compose
To run the application in daemon mode:
```bash
docker compose up -d --build
```
On initial startup, Docker Compose will build the FastAPI application container, download the PostgreSQL 15 alpine image, and start both containers.

### Step 4: Apply Database Schema Migrations
Once the containers are running, apply the Alembic database migrations:
```bash
docker compose exec app alembic upgrade head
```

---

## 2. Reverse Proxy & SSL Setup

It is highly recommended to run the FastAPI container behind a reverse proxy (like Nginx or Caddy) to handle SSL/TLS termination, request throttling, and static file caching.

### Option A: Reverse Proxy with Nginx (Classic)

1. **Install Nginx**:
   ```bash
   sudo apt update
   sudo apt install nginx -y
   ```
2. **Configure Nginx**:
   Create a configuration block for the application at `/etc/nginx/sites-available/ledger`:
   ```nginx
   server {
       listen 80;
       server_name ledger.example.com; # Replace with your domain name

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. **Enable Configuration**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ledger /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### SSL Certificate Generation & Renewal (Nginx + Certbot)
1. **Install Certbot**:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```
2. **Request Certificate**:
   Certbot will automatically verify the domain, obtain a Let's Encrypt certificate, and edit your Nginx config to serve over HTTPS:
   ```bash
   sudo certbot --nginx -d ledger.example.com
   ```
3. **SSL Auto-Renewal Process**:
   Let's Encrypt certificates are valid for 90 days. Certbot configures a systemd timer to check for renewals twice a day.
   - **Check timer status**:
     ```bash
     sudo systemctl status certbot.timer
     ```
   - **Manual dry-run verification**:
     ```bash
     sudo certbot renew --dry-run
     ```

---

### Option B: Reverse Proxy with Caddy (Modern & Automatic SSL)

Caddy handles reverse-proxying and SSL certificate acquisition/renewal automatically without needing Certbot.

1. **Install Caddy**:
   Follow instructions to install Caddy on Ubuntu: [Caddy Installation Docs](https://caddyserver.com/docs/install#debian-ubuntu-raspbian).
2. **Configure Caddyfile**:
   Edit `/etc/caddy/Caddyfile`:
   ```caddy
   ledger.example.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```
3. **Start and Enable Caddy**:
   ```bash
   sudo systemctl enable --now caddy
   ```
   Caddy will automatically request and install the SSL certificate on startup and renew it silently before expiration.

---

## 3. Server & Database Maintenance

### Database Backups (pg_dump)
To protect your accounting ledger data, configure a cron job to take daily database backups.

#### Manual Backup Command
```bash
# Create backups directory
mkdir -p /opt/ledger-web/backups

# Dump database to a SQL file
docker compose exec -T db pg_dump -U ledge_users ledger > /opt/ledger-web/backups/ledger_backup_$(date +%F_%H%M%S).sql
```

#### Automated Backup Script (Cron)
1. Create a script `/opt/ledger-web/backup.sh`:
   ```bash
   #!/bin/bash
   BACKUP_DIR="/opt/ledger-web/backups"
   FILE_NAME="${BACKUP_DIR}/ledger_$(date +%F_%H%M%S).sql"
   mkdir -p "$BACKUP_DIR"
   docker compose -f /opt/ledger-web/docker-compose.yml exec -T db pg_dump -U ledge_users ledger > "$FILE_NAME"
   # Keep only the last 30 days of backups
   find "$BACKUP_DIR" -type f -name "*.sql" -mtime +30 -delete
   ```
2. Make it executable:
   ```bash
   chmod +x /opt/ledger-web/backup.sh
   ```
3. Register the script to run daily at 2 AM using cron:
   ```bash
   # Open crontab editor
   crontab -e
   # Add this line at the bottom:
   0 2 * * * /bin/bash /opt/ledger-web/backup.sh
   ```

### Database Restoration (pg_restore)
In the event of a database corruption or host failure, you can restore a SQL backup file:
```bash
# 1. Stop the application container to halt write traffic
docker compose stop app

# 2. Re-create a clean ledger database (Warning: Drops existing data)
docker compose exec db psql -U ledge_users -d postgres -c "DROP DATABASE ledger;"
docker compose exec db psql -U ledge_users -d postgres -c "CREATE DATABASE ledger;"

# 3. Restore data from backup file
docker compose exec -T db psql -U ledge_users -d ledger < /opt/ledger-web/backups/ledger_backup_file.sql

# 4. Restart the application container
docker compose start app
```

---

## 4. Troubleshooting & Monitoring

### 1. Inspect Application Logs
If the application is unresponsive or returns server errors (500), inspect the container runtime logs:
```bash
# View real-time logs
docker compose logs -f app

# Search logs for Exceptions
docker compose logs app | grep -i "error"
```

### 2. Monitor Container System Resources
Ensure the application is not running out of memory:
```bash
docker stats
```

---

## 5. Assumptions / Information Needed

> [!IMPORTANT]
> **Assumptions**:
> - This operations guide assumes deployment is targeted on a Linux host (e.g. Ubuntu 22.04 LTS) with standard Docker and Docker Compose packages installed.
> - The configurations assume the production domain is configured via DNS A records pointing to the server's public IP address before requesting SSL certificates.
