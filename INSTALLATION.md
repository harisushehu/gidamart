# Gidamart Installation Guide

This comprehensive guide will walk you through the installation process for the Gidamart Real Estate Management System on various platforms.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [First Run](#first-run)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Setup](#advanced-setup)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 1GB free space
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **Operating System**: Latest stable versions
- **Python**: Version 3.9 or 3.10
- **RAM**: 8GB or more
- **Storage**: 5GB free space (for images and database growth)
- **Network**: Broadband internet connection

### Software Dependencies
- Python 3.8+
- pip (Python package installer)
- Git (for cloning the repository)
- Web browser (Chrome, Firefox, Safari, or Edge)

## Installation Methods

### Method 1: Git Clone (Recommended)
Best for developers and users familiar with Git.

### Method 2: Download ZIP
Suitable for users who prefer not to use Git.

### Method 3: Docker (Advanced)
For containerized deployment.

## Step-by-Step Installation

### Method 1: Git Clone Installation

#### Step 1: Install Prerequisites

**On Windows:**
1. Download and install Python from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation
2. Download and install Git from [git-scm.com](https://git-scm.com)
3. Open Command Prompt or PowerShell

**On macOS:**
1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python and Git:
   ```bash
   brew install python git
   ```
3. Open Terminal

**On Linux (Ubuntu/Debian):**
1. Update package list:
   ```bash
   sudo apt update
   ```
2. Install Python and Git:
   ```bash
   sudo apt install python3 python3-pip python3-venv git
   ```
3. Open Terminal

#### Step 2: Clone the Repository

```bash
git clone https://github.com/yourusername/gidamart.git
cd gidamart
```

#### Step 3: Create Virtual Environment

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the beginning of your command prompt, indicating the virtual environment is active.

#### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required Python packages:
- Flask (web framework)
- Flask-SQLAlchemy (database ORM)
- Flask-Login (user authentication)
- Werkzeug (utilities)
- And other dependencies

#### Step 5: Create Required Directories

```bash
mkdir -p src/database
mkdir -p src/static/uploads
```

### Method 2: Download ZIP Installation

#### Step 1: Download the Project
1. Go to the GitHub repository
2. Click the green "Code" button
3. Select "Download ZIP"
4. Extract the ZIP file to your desired location

#### Step 2: Follow Steps 3-5 from Method 1
Continue with the virtual environment setup and dependency installation.

### Method 3: Docker Installation

#### Step 1: Install Docker
Download and install Docker Desktop from [docker.com](https://docker.com)

#### Step 2: Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p src/database src/static/uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=src/main.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "src/main.py"]
```

#### Step 3: Build and Run
```bash
docker build -t gidamart .
docker run -p 5000:5000 gidamart
```

## Database Setup

### Automatic Setup (Default)
The application automatically creates the SQLite database on first run. No manual setup required.

### Manual Database Initialization
If you need to manually initialize the database:

```bash
python -c "
from src.main import app
from src.models import db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"
```

### Using PostgreSQL (Production)

#### Step 1: Install PostgreSQL
**On Windows:** Download from [postgresql.org](https://postgresql.org)
**On macOS:** `brew install postgresql`
**On Linux:** `sudo apt install postgresql postgresql-contrib`

#### Step 2: Create Database
```sql
CREATE DATABASE gidamart;
CREATE USER gidamart_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gidamart TO gidamart_user;
```

#### Step 3: Update Configuration
Create a `.env` file:
```env
DATABASE_URL=postgresql://gidamart_user:your_password@localhost/gidamart
```

#### Step 4: Install PostgreSQL Adapter
```bash
pip install psycopg2-binary
```

### Using MySQL (Alternative)

#### Step 1: Install MySQL
Follow the official MySQL installation guide for your platform.

#### Step 2: Create Database
```sql
CREATE DATABASE gidamart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gidamart_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON gidamart.* TO 'gidamart_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Step 3: Install MySQL Adapter
```bash
pip install PyMySQL
```

#### Step 4: Update Configuration
```env
DATABASE_URL=mysql+pymysql://gidamart_user:your_password@localhost/gidamart
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application Settings
SECRET_KEY=your-very-secret-key-here
DEBUG=True
FLASK_ENV=development

# Database Configuration
DATABASE_URL=sqlite:///src/database/app.db

# File Upload Settings
UPLOAD_FOLDER=src/static/uploads
MAX_CONTENT_LENGTH=16777216

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Admin Settings
ADMIN_EMAIL=admin@gidamart.com
ADMIN_PASSWORD=admin123
```

### Security Configuration

#### Generate a Secure Secret Key
```python
import secrets
print(secrets.token_hex(32))
```

Use the generated key in your `.env` file.

#### File Upload Security
The application includes several security measures:
- File type validation (only images allowed)
- File size limits (16MB default)
- Secure filename generation
- Upload directory protection

### Performance Configuration

#### For Development
```env
DEBUG=True
FLASK_ENV=development
```

#### For Production
```env
DEBUG=False
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
```

## First Run

### Step 1: Start the Application

**Development Mode:**
```bash
python src/main.py
```

**Production Mode:**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 src.main:app
```

### Step 2: Access the Application

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. You should see the Gidamart homepage

### Step 3: Admin Setup

1. Go to `http://localhost:5000/admin/login`
2. Use the default credentials:
   - Email: `admin@gidamart.com`
   - Password: `admin123`
3. **Important:** Change the admin password immediately after first login

### Step 4: Test Basic Functionality

1. **Homepage:** Verify the homepage loads correctly
2. **Navigation:** Test all navigation links
3. **Admin Dashboard:** Log in and explore the admin interface
4. **Property Management:** Try adding a test property
5. **Image Upload:** Test the image upload functionality

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Python not found"
**Solution:**
- Ensure Python is installed and added to PATH
- Try using `python3` instead of `python`
- Reinstall Python with "Add to PATH" option checked

#### Issue: "pip not found"
**Solution:**
```bash
python -m ensurepip --upgrade
```

#### Issue: "Permission denied" on Linux/macOS
**Solution:**
```bash
sudo chown -R $USER:$USER /path/to/gidamart
```

#### Issue: "Port 5000 already in use"
**Solution:**
- Kill the process using port 5000:
  ```bash
  # On Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  
  # On macOS/Linux
  lsof -ti:5000 | xargs kill -9
  ```
- Or use a different port:
  ```python
  app.run(host='0.0.0.0', port=8000, debug=True)
  ```

#### Issue: Database connection errors
**Solution:**
1. Check database URL in configuration
2. Ensure database server is running
3. Verify credentials and permissions
4. Check firewall settings

#### Issue: Images not uploading
**Solution:**
1. Check upload directory permissions:
   ```bash
   chmod 755 src/static/uploads
   ```
2. Verify file size limits
3. Check available disk space

#### Issue: Styles not loading
**Solution:**
1. Clear browser cache
2. Check static file serving configuration
3. Verify file paths in templates

### Debug Mode

Enable debug mode for detailed error messages:

```python
app.run(debug=True)
```

### Logging

Add logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Setup

### SSL/HTTPS Configuration

#### Using nginx (Recommended)

1. Install nginx
2. Configure SSL certificate
3. Create nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/gidamart/src/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Performance Optimization

#### Database Optimization
1. Add database indexes for frequently queried fields
2. Use connection pooling for production
3. Implement database caching

#### Static File Optimization
1. Use a CDN for static files
2. Enable gzip compression
3. Set proper cache headers

#### Application Optimization
1. Use Redis for session storage
2. Implement application-level caching
3. Optimize database queries

### Monitoring and Maintenance

#### Health Checks
Add a health check endpoint:

```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

#### Backup Strategy
1. Regular database backups
2. Image file backups
3. Configuration backups

#### Updates and Maintenance
1. Regular security updates
2. Dependency updates
3. Performance monitoring

### Multi-Environment Setup

#### Development Environment
```env
FLASK_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///src/database/dev.db
```

#### Staging Environment
```env
FLASK_ENV=staging
DEBUG=False
DATABASE_URL=postgresql://user:pass@staging-db/gidamart
```

#### Production Environment
```env
FLASK_ENV=production
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db/gidamart
SECRET_KEY=production-secret-key
```

## Support and Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)

### Community Support
- GitHub Issues: Report bugs and request features
- Stack Overflow: General Flask and Python questions
- Flask Discord: Real-time community support

### Professional Support
For professional installation and setup services, contact the development team.

---

**Installation complete!** Your Gidamart Real Estate Management System should now be running successfully. If you encounter any issues, please refer to the troubleshooting section or create an issue on GitHub.

