# Deployment Guide

This guide covers deployment options for the Air Quality Monitoring System.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Python 3.8 or higher
- Redis (optional, for caching)
- DuckDB
- OpenAQ API key

### System Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 20GB storage
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB storage
- **Large Scale**: 8+ CPU cores, 16GB+ RAM, 100GB+ storage

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd air-quality-pipeline
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Initialize Database
```bash
python scripts/setup_db.py
```

### 6. Seed Initial Data
```bash
python scripts/seed_locations.py
python scripts/collect_data.py
```

## Local Development

### Running Dashboard
```bash
python app/main.py dashboard --debug
```

Access at: `http://localhost:8050`

### Running API Server
```bash
uvicorn app.api.app:api_app --reload --host 0.0.0.0 --port 8000
```

API docs at: `http://localhost:8000/docs`

### Running Pipeline
```bash
python app/main.py pipeline
```

## Production Deployment

### Using Gunicorn (Dashboard)

**Install Gunicorn:**
```bash
pip install gunicorn gevent
```

**Run with Gunicorn:**
```bash
gunicorn app.dashboard.app:server \
  --workers 4 \
  --worker-class gevent \
  --bind 0.0.0.0:8050 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

**Systemd Service (Linux):**

Create `/etc/systemd/system/air-quality-dashboard.service`:
```ini
[Unit]
Description=Air Quality Dashboard
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/air-quality-pipeline
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn app.dashboard.app:server --workers 4 --worker-class gevent --bind 0.0.0.0:8050
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable air-quality-dashboard
sudo systemctl start air-quality-dashboard
sudo systemctl status air-quality-dashboard
```

### Using Uvicorn (API)

**Production Uvicorn:**
```bash
uvicorn app.api.app:api_app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --access-log \
  --log-level info
```

**Systemd Service (API):**

Create `/etc/systemd/system/air-quality-api.service`:
```ini
[Unit]
Description=Air Quality API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/air-quality-pipeline
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.api.app:api_app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

**Nginx Configuration:**
```nginx
upstream dashboard {
    server 127.0.0.1:8050;
}

upstream api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Dashboard
    location / {
        proxy_pass http://dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /api/v1/ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Scheduled Data Collection

**Cron Job:**
```bash
# Edit crontab
crontab -e

# Add collection every 15 minutes
*/15 * * * * cd /path/to/air-quality-pipeline && /path/to/venv/bin/python scripts/collect_data.py >> logs/collection.log 2>&1

# Add location sync daily at 2 AM
0 2 * * * cd /path/to/air-quality-pipeline && /path/to/venv/bin/python scripts/seed_locations.py >> logs/sync.log 2>&1
```

**Systemd Timer (Linux):**

Create `/etc/systemd/system/air-quality-collect.service`:
```ini
[Unit]
Description=Air Quality Data Collection

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/path/to/air-quality-pipeline
ExecStart=/path/to/venv/bin/python scripts/collect_data.py
```

Create `/etc/systemd/system/air-quality-collect.timer`:
```ini
[Unit]
Description=Run Air Quality Collection every 15 minutes

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable air-quality-collect.timer
sudo systemctl start air-quality-collect.timer
```

## Docker Deployment

### Dockerfile

Create `docker/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create directories
RUN mkdir -p data logs temp/exports

# Expose ports
EXPOSE 8050 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run
CMD ["python", "app/main.py", "dashboard"]
```

### Docker Compose

Create `docker/docker-compose.yml`:
```yaml
version: '3.8'

services:
  dashboard:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8050:8050"
      - "8000:8000"
    environment:
      - DATABASE_PATH=/app/data/air_quality.db
      - REDIS_URL=redis://redis:6379/0
      - OPENAQ_API_KEY=${OPENAQ_API_KEY}
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
      - ../temp:/app/temp
    depends_on:
      - redis
    restart: unless-stopped

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: uvicorn app.api.app:api_app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_PATH=/app/data/air_quality.db
      - REDIS_URL=redis://redis:6379/0
      - OPENAQ_API_KEY=${OPENAQ_API_KEY}
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - dashboard
      - api
    restart: unless-stopped

volumes:
  redis_data:
```

### Build and Run

```bash
# Build images
docker-compose -f docker/docker-compose.yml build

# Start services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

## Monitoring

### Health Checks

**Dashboard:**
```bash
curl http://localhost:8050/healthz
```

**API:**
```bash
curl http://localhost:8000/api/v1/health
```

### Log Monitoring

**View application logs:**
```bash
tail -f logs/app.log
```

**Filter errors:**
```bash
jq '.level == "ERROR"' logs/app.log
```

**Monitor collection logs:**
```bash
tail -f logs/collection.log
```

### Performance Monitoring

**System resources:**
```bash
htop
```

**Database size:**
```bash
du -sh data/air_quality.db
```

**API response time:**
```bash
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health
```

### Prometheus Metrics (Optional)

Add to `app/api/app.py`:
```python
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

Access metrics at: `http://localhost:8000/metrics`

## Troubleshooting

### Common Issues

**Dashboard not loading:**
- Check if service is running: `sudo systemctl status air-quality-dashboard`
- View logs: `sudo journalctl -u air-quality-dashboard -f`
- Check port: `netstat -tlnp | grep 8050`

**API returning 500 errors:**
- Check API logs: `sudo journalctl -u air-quality-api -f`
- Verify database connection
- Check environment variables

**Data collection failing:**
- Check OpenAQ API key validity
- Verify rate limit settings
- Check logs: `tail -f logs/collection.log`

**Memory issues:**
- Reduce worker count
- Limit export rows
- Clear old data

**Database locked:**
- Ensure only one process writes to database
- Check for long-running queries
- Restart services

### Performance Optimization

**Enable Redis caching:**
```bash
# Install Redis
sudo apt install redis-server

# Update .env
REDIS_URL=redis://localhost:6379/0
```

**Optimize database queries:**
- Use presentation views
- Add indexes
- Limit result sets

**Scale horizontally:**
- Use load balancer
- Deploy multiple instances
- Use shared storage

### Backup and Recovery

**Backup database:**
```bash
cp data/air_quality.db backups/air_quality_$(date +%Y%m%d).db
```

**Automated backup (cron):**
```bash
0 3 * * * cp /path/to/data/air_quality.db /path/to/backups/air_quality_$(date +\%Y\%m\%d).db
```

**Restore database:**
```bash
cp backups/air_quality_20240101.db data/air_quality.db
```

### Security Hardening

**Update .env for production:**
```bash
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=<generate-strong-key>
```

**Generate secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Firewall rules:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**Regular updates:**
```bash
pip list --outdated
pip install --upgrade <package>
```

## Scaling Considerations

### Vertical Scaling
- Increase CPU cores
- Add more RAM
- Use faster storage (SSD)

### Horizontal Scaling
- Deploy multiple instances
- Use load balancer
- Implement session management
- Use shared database/storage

### Database Scaling
- Consider PostgreSQL for production
- Implement read replicas
- Use connection pooling
- Archive old data

## Support

For deployment issues:
1. Check logs in `logs/` directory
2. Review this documentation
3. Check system resources
4. Verify configuration
5. Open GitHub issue with details
