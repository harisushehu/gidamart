# Gidamart Deployment Guide

This guide covers deploying the Gidamart Real Estate Management System to various production environments, including cloud platforms, VPS servers, and containerized deployments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Web Server Configuration](#web-server-configuration)
6. [SSL/HTTPS Setup](#ssl-https-setup)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Performance Optimization](#performance-optimization)
10. [Security Hardening](#security-hardening)

## Pre-Deployment Checklist

### Code Preparation
- [ ] All features tested in development environment
- [ ] Database migrations completed
- [ ] Static files collected and optimized
- [ ] Environment variables configured
- [ ] Security settings reviewed
- [ ] Dependencies updated and locked
- [ ] Documentation updated

### Infrastructure Requirements
- [ ] Server specifications meet minimum requirements
- [ ] Domain name configured
- [ ] SSL certificate obtained
- [ ] Database server prepared
- [ ] Backup storage configured
- [ ] Monitoring tools set up

### Security Checklist
- [ ] Strong secret key generated
- [ ] Debug mode disabled
- [ ] Database credentials secured
- [ ] File upload restrictions configured
- [ ] CORS settings reviewed
- [ ] Admin credentials changed

## Environment Configuration

### Production Environment Variables

Create a `.env` file for production:

```env
# Application Settings
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your-super-secret-production-key-here

# Database Configuration
DATABASE_URL=postgresql://gidamart_user:secure_password@localhost/gidamart_prod

# File Upload Settings
UPLOAD_FOLDER=/var/www/gidamart/uploads
MAX_CONTENT_LENGTH=16777216

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-app-password

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Performance Settings
SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 300}
```

### System Environment Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash gidamart
sudo usermod -aG sudo gidamart

# Create application directories
sudo mkdir -p /var/www/gidamart
sudo mkdir -p /var/log/gidamart
sudo mkdir -p /etc/gidamart

# Set permissions
sudo chown -R gidamart:gidamart /var/www/gidamart
sudo chown -R gidamart:gidamart /var/log/gidamart
```

## Database Setup

### PostgreSQL Setup (Recommended)

#### Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

#### Database Configuration
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE gidamart_prod;
CREATE USER gidamart_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE gidamart_prod TO gidamart_user;

# Configure connection settings
ALTER USER gidamart_user CREATEDB;
\q
```

#### PostgreSQL Configuration
Edit `/etc/postgresql/13/main/postgresql.conf`:
```conf
# Connection settings
listen_addresses = 'localhost'
port = 5432
max_connections = 100

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'error'
```

Edit `/etc/postgresql/13/main/pg_hba.conf`:
```conf
# Local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

### MySQL Setup (Alternative)

#### Installation
```bash
# Ubuntu/Debian
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
sudo systemctl enable mysqld
sudo systemctl start mysqld
```

#### Database Configuration
```sql
CREATE DATABASE gidamart_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gidamart_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON gidamart_prod.* TO 'gidamart_user'@'localhost';
FLUSH PRIVILEGES;
```

## Application Deployment

### Method 1: Traditional VPS Deployment

#### Step 1: Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip python3-venv nginx supervisor git

# Install Node.js (for asset compilation if needed)
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs
```

#### Step 2: Application Setup
```bash
# Switch to application user
sudo su - gidamart

# Clone repository
git clone https://github.com/yourusername/gidamart.git /var/www/gidamart
cd /var/www/gidamart

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Set up environment
cp .env.example .env
# Edit .env with production values

# Initialize database
python src/main.py db init
python src/main.py db migrate
python src/main.py db upgrade
```

#### Step 3: Gunicorn Configuration
Create `/etc/gidamart/gunicorn.conf.py`:
```python
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/var/log/gidamart/access.log"
errorlog = "/var/log/gidamart/error.log"
loglevel = "info"

# Process naming
proc_name = "gidamart"

# Server mechanics
daemon = False
pidfile = "/var/run/gidamart/gidamart.pid"
user = "gidamart"
group = "gidamart"
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

#### Step 4: Supervisor Configuration
Create `/etc/supervisor/conf.d/gidamart.conf`:
```ini
[program:gidamart]
command=/var/www/gidamart/venv/bin/gunicorn -c /etc/gidamart/gunicorn.conf.py src.main:app
directory=/var/www/gidamart
user=gidamart
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gidamart/supervisor.log
environment=PATH="/var/www/gidamart/venv/bin"
```

Start the application:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gidamart
```

### Method 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn psycopg2-binary

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Create necessary directories
RUN mkdir -p src/static/uploads
RUN mkdir -p src/database

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "src.main:app"]
```

#### Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://gidamart:password@db:5432/gidamart
      - FLASK_ENV=production
      - DEBUG=False
    volumes:
      - ./uploads:/app/src/static/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=gidamart
      - POSTGRES_USER=gidamart
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./uploads:/var/www/uploads
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

Deploy with Docker:
```bash
docker-compose up -d
```

### Method 3: Cloud Platform Deployment

#### Heroku Deployment

Create `Procfile`:
```
web: gunicorn src.main:app
release: python src/main.py db upgrade
```

Create `runtime.txt`:
```
python-3.9.16
```

Deploy to Heroku:
```bash
# Install Heroku CLI
# Create Heroku app
heroku create gidamart-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key

# Deploy
git push heroku main
```

#### AWS Elastic Beanstalk

Create `.ebextensions/01_packages.config`:
```yaml
packages:
  yum:
    postgresql-devel: []
    gcc: []
```

Create `application.py`:
```python
from src.main import app as application

if __name__ == "__main__":
    application.run()
```

Deploy:
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init

# Create environment
eb create gidamart-prod

# Deploy
eb deploy
```

#### DigitalOcean App Platform

Create `.do/app.yaml`:
```yaml
name: gidamart
services:
- name: web
  source_dir: /
  github:
    repo: yourusername/gidamart
    branch: main
  run_command: gunicorn --worker-tmp-dir /dev/shm src.main:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  env:
  - key: FLASK_ENV
    value: production
  - key: DEBUG
    value: "False"
databases:
- name: gidamart-db
  engine: PG
  version: "13"
```

## Web Server Configuration

### Nginx Configuration

Create `/etc/nginx/sites-available/gidamart`:
```nginx
upstream gidamart_app {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Client max body size (for file uploads)
    client_max_body_size 20M;

    # Static files
    location /static/ {
        alias /var/www/gidamart/src/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Gzip static assets
        location ~* \.(css|js)$ {
            gzip_static on;
        }
    }

    # Uploaded files
    location /static/uploads/ {
        alias /var/www/gidamart/src/static/uploads/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Application
    location / {
        proxy_pass http://gidamart_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://gidamart_app;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(\.env|\.git|requirements\.txt|Dockerfile) {
        deny all;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/gidamart /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Apache Configuration (Alternative)

Create `/etc/apache2/sites-available/gidamart.conf`:
```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/yourdomain.com.crt
    SSLCertificateKeyFile /etc/ssl/private/yourdomain.com.key

    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"

    # Static files
    Alias /static /var/www/gidamart/src/static
    <Directory /var/www/gidamart/src/static>
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </Directory>

    # Proxy to application
    ProxyPreserveHost On
    ProxyPass /static !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

## SSL/HTTPS Setup

### Let's Encrypt (Free SSL)

#### Installation
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

#### Automatic Renewal
Add to crontab:
```bash
0 12 * * * /usr/bin/certbot renew --quiet
```

### Commercial SSL Certificate

#### Installation
```bash
# Create private key
sudo openssl genrsa -out /etc/ssl/private/yourdomain.com.key 2048

# Create certificate signing request
sudo openssl req -new -key /etc/ssl/private/yourdomain.com.key -out yourdomain.com.csr

# Install certificate (provided by CA)
sudo cp yourdomain.com.crt /etc/ssl/certs/
sudo cp intermediate.crt /etc/ssl/certs/

# Set permissions
sudo chmod 600 /etc/ssl/private/yourdomain.com.key
sudo chmod 644 /etc/ssl/certs/yourdomain.com.crt
```

## Monitoring and Logging

### Application Logging

Update `src/main.py`:
```python
import logging
from logging.handlers import RotatingFileHandler
import os

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/gidamart.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Gidamart startup')
```

### System Monitoring

#### Install monitoring tools
```bash
# Install htop, iotop, and other monitoring tools
sudo apt install htop iotop nethogs

# Install and configure fail2ban
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

#### Prometheus and Grafana (Advanced)
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.30.3/prometheus-2.30.3.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-2.30.3.linux-amd64 /opt/prometheus

# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
```

### Log Management

#### Logrotate Configuration
Create `/etc/logrotate.d/gidamart`:
```
/var/log/gidamart/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 gidamart gidamart
    postrotate
        supervisorctl restart gidamart
    endscript
}
```

## Backup and Recovery

### Database Backup

#### Automated PostgreSQL Backup
Create `/usr/local/bin/backup-gidamart.sh`:
```bash
#!/bin/bash

# Configuration
DB_NAME="gidamart_prod"
DB_USER="gidamart_user"
BACKUP_DIR="/var/backups/gidamart"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/gidamart_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_FILE.gz s3://your-backup-bucket/
```

Make executable and add to crontab:
```bash
sudo chmod +x /usr/local/bin/backup-gidamart.sh
echo "0 2 * * * /usr/local/bin/backup-gidamart.sh" | sudo crontab -
```

### File Backup

#### Backup uploaded files
```bash
#!/bin/bash

UPLOAD_DIR="/var/www/gidamart/src/static/uploads"
BACKUP_DIR="/var/backups/gidamart/uploads"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$UPLOAD_DIR" .

# Remove old backups
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +7 -delete
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop application
sudo supervisorctl stop gidamart

# Restore database
gunzip -c /var/backups/gidamart/gidamart_20240115_020000.sql.gz | psql -U gidamart_user -h localhost gidamart_prod

# Start application
sudo supervisorctl start gidamart
```

#### File Recovery
```bash
# Extract files
tar -xzf /var/backups/gidamart/uploads/uploads_20240115_020000.tar.gz -C /var/www/gidamart/src/static/uploads/

# Fix permissions
sudo chown -R gidamart:gidamart /var/www/gidamart/src/static/uploads/
```

## Performance Optimization

### Database Optimization

#### PostgreSQL Tuning
Edit `/etc/postgresql/13/main/postgresql.conf`:
```conf
# Memory settings
shared_buffers = 256MB                  # 25% of RAM
effective_cache_size = 1GB              # 75% of RAM
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Connection settings
max_connections = 100
```

#### Database Indexing
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_properties_location ON properties(location);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_type ON properties(property_type);
CREATE INDEX idx_properties_status ON properties(status);
CREATE INDEX idx_inquiries_created_at ON contact_inquiries(created_at);
CREATE INDEX idx_inquiries_status ON contact_inquiries(status);
```

### Application Optimization

#### Caching with Redis
```python
from flask_caching import Cache
import redis

# Configure Redis
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

# Cache property listings
@cache.memoize(timeout=300)
def get_properties(page, per_page, filters):
    # Property query logic
    pass
```

#### Static File Optimization
```bash
# Install and configure compression
sudo apt install brotli

# Compress static files
find /var/www/gidamart/src/static -name "*.css" -exec brotli {} \;
find /var/www/gidamart/src/static -name "*.js" -exec brotli {} \;
```

### CDN Configuration

#### CloudFlare Setup
1. Sign up for CloudFlare
2. Add your domain
3. Update nameservers
4. Configure caching rules:
   - Cache static assets for 1 year
   - Cache HTML for 2 hours
   - Enable Brotli compression

#### AWS CloudFront
```json
{
  "DistributionConfig": {
    "CallerReference": "gidamart-cdn",
    "Origins": {
      "Quantity": 1,
      "Items": [
        {
          "Id": "gidamart-origin",
          "DomainName": "yourdomain.com",
          "CustomOriginConfig": {
            "HTTPPort": 443,
            "HTTPSPort": 443,
            "OriginProtocolPolicy": "https-only"
          }
        }
      ]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "gidamart-origin",
      "ViewerProtocolPolicy": "redirect-to-https",
      "Compress": true,
      "CachePolicyId": "managed-caching-optimized"
    }
  }
}
```

## Security Hardening

### Server Security

#### Firewall Configuration
```bash
# Install and configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

#### SSH Hardening
Edit `/etc/ssh/sshd_config`:
```conf
# Disable root login
PermitRootLogin no

# Use key-based authentication
PasswordAuthentication no
PubkeyAuthentication yes

# Change default port
Port 2222

# Limit users
AllowUsers gidamart

# Disable unused features
X11Forwarding no
AllowTcpForwarding no
```

#### Fail2Ban Configuration
Edit `/etc/fail2ban/jail.local`:
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

### Application Security

#### Security Headers
```python
from flask_talisman import Talisman

# Configure security headers
Talisman(app, {
    'force_https': True,
    'strict_transport_security': True,
    'content_security_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
    }
})
```

#### Input Validation
```python
from flask_wtf.csrf import CSRFProtect
from marshmallow import Schema, fields, validate

# Enable CSRF protection
csrf = CSRFProtect(app)

# Input validation schemas
class PropertySchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    location = fields.Str(required=True, validate=validate.Length(min=1, max=200))
```

### Regular Security Updates

#### Automated Updates
```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades

# Configure automatic security updates
echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades
```

#### Security Monitoring
```bash
# Install and configure AIDE (intrusion detection)
sudo apt install aide
sudo aideinit
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Add to crontab for daily checks
echo "0 3 * * * /usr/bin/aide --check" | sudo crontab -
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo tail -f /var/log/gidamart/error.log
sudo supervisorctl tail gidamart stderr

# Check configuration
sudo nginx -t
sudo supervisorctl status
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U gidamart_user -h localhost -d gidamart_prod

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### Performance Issues
```bash
# Monitor system resources
htop
iotop
df -h

# Check application performance
sudo supervisorctl tail gidamart stdout
```

### Health Checks

#### Application Health Check
```python
@app.route('/health')
def health_check():
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check file system
        upload_dir = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            raise Exception('Upload directory not accessible')
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 500
```

#### Monitoring Script
```bash
#!/bin/bash

# Check application health
curl -f http://localhost:8000/health || echo "Application unhealthy"

# Check disk space
df -h | awk '$5 > 80 {print "Disk space warning: " $0}'

# Check memory usage
free -m | awk 'NR==2{printf "Memory usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }'

# Check load average
uptime | awk '{print "Load average: " $(NF-2) " " $(NF-1) " " $NF}'
```

---

This deployment guide provides comprehensive instructions for deploying Gidamart to production environments. Choose the deployment method that best fits your infrastructure and requirements. For additional support, refer to the main documentation or create an issue on GitHub.

