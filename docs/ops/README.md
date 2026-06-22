# Ledger Web Application — Operations Guide

Covers deployment, SSL/TLS certificate renewal, and routine server maintenance.

---

## 1. Deployment

### Prerequisites
- Docker Engine 24.x+ and Docker Compose v2 plugin
- A `.env` file configured from `.env.example`

### Environment Setup

```bash
cp .env.example .env
```

Key values to set in `.env` for production:

| Variable | Production Value |
| :--- | :--- |
| `POSTGRES_HOST` | `ledger_db` (Docker service name, not `localhost`) |
| `POSTGRES_PASSWORD` | Strong random password |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` (reduce for higher security) |

### Start Services

```bash
# Build the image and start both containers (app + db) in detached mode
docker compose up -d --build

# Apply all database migrations
docker compose exec app alembic upgrade head
```

### Verify

```bash
docker compose ps           # Both containers should show 'Up (healthy)'
curl http://localhost:8000/docs  # Should return HTTP 200
```

### Deploy Updates

```bash
git pull origin main
docker compose up -d --build
docker compose exec app alembic upgrade head
```

---

## 2. SSL/TLS Certificate Renewal

The application does not terminate TLS directly. Use **Nginx as a reverse proxy** on the host, with **Certbot** managing Let's Encrypt certificates.

### Obtain a Certificate (First Time)

```bash
sudo certbot --nginx -d <your-domain.com> -d www.<your-domain.com>
```

Certbot will update the Nginx configuration automatically and set up HTTP → HTTPS redirection.

### Nginx Reverse Proxy (Minimal Config)

```nginx
server {
    listen 443 ssl http2;
    server_name <your-domain.com>;

    ssl_certificate     /etc/letsencrypt/live/<your-domain.com>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<your-domain.com>/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

### Certificate Renewal

Certbot installs a systemd timer that auto-renews certificates before expiry (90-day validity). To test:

```bash
sudo certbot renew --dry-run
```

To auto-reload Nginx after renewal, add a deploy hook:

```bash
echo '#!/bin/bash\nsystemctl reload nginx' \
  | sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

Check expiry at any time:

```bash
sudo certbot certificates
```

> [!NOTE]
> If using **Caddy** as a reverse proxy, TLS is fully automatic — no Certbot setup is needed. Configure `<your-domain.com> { reverse_proxy localhost:8000 }` in your `Caddyfile`.

---

## 3. Server Maintenance

### 3.1 Host OS Updates

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y

# RHEL/Fedora
sudo dnf update -y
```

Reboot after kernel updates and verify containers restarted: `docker compose ps`.

### 3.2 Docker Housekeeping

```bash
# Remove stopped containers, dangling images, and build cache
docker system prune -f

# Check Docker disk usage
docker system df
```

### 3.3 Database Backup

```bash
# Create a timestamped compressed backup
docker compose exec -T db pg_dump \
  -U ledge_users -d ledger --format=custom --compress=9 \
  > /backups/ledger_$(date +%Y%m%d_%H%M%S).dump
```

**Automate daily at 2 AM** (`sudo crontab -e`):

```cron
0 2 * * * docker compose -f /path/to/Ledger/docker-compose.yml exec -T db pg_dump -U ledge_users -d ledger --format=custom --compress=9 > /backups/ledger_$(date +\%Y\%m\%d).dump

# Delete backups older than 7 days
0 3 * * * find /backups -name "ledger_*.dump" -mtime +7 -delete
```

### 3.4 Database Restore

> [!CAUTION]
> This overwrites all existing data. Stop the app first.

```bash
docker compose stop app
docker compose exec -T db pg_restore -U ledge_users -d ledger --clean --if-exists \
  < /backups/ledger_<timestamp>.dump
docker compose start app
docker compose exec app alembic current   # Confirm schema is at head
```

### 3.5 Log Management

```bash
docker compose logs -f app          # Stream app logs
docker compose logs --tail=200 app  # Last 200 lines
```

Prevent unbounded log growth by adding to `/etc/docker/daemon.json` on the host:

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "50m", "max-file": "5" }
}
```

Then restart Docker: `sudo systemctl restart docker && docker compose up -d`.

### 3.6 Health Checks

```bash
# Application
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs   # expect 200

# Database
docker inspect ledger_db --format '{{.State.Health.Status}}'        # expect healthy

# Migration status
docker compose exec app alembic current                              # expect (head)
```

### 3.7 Emergency: Rollback a Migration

```bash
docker compose exec app alembic downgrade -1       # Roll back last migration
docker compose exec app alembic history            # List all revision IDs
```
