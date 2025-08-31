import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_config():
    """Get configuration with environment-specific overrides"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Base configuration
    base_config = {
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///app.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'RECAPTCHA_SITE_KEY': os.environ.get('RECAPTCHA_SITE_KEY'),
        'RECAPTCHA_SECRET_KEY': os.environ.get('RECAPTCHA_SECRET_KEY'),
        'RECAPTCHA_V3_SITE_KEY': os.environ.get('RECAPTCHA_V3_SITE_KEY'),
        'RECAPTCHA_V3_SECRET_KEY': os.environ.get('RECAPTCHA_V3_SECRET_KEY'),
        'FLASK_ENV': env,
        'UPLOAD_FOLDER': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads'),
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max file size
    }
    
    # Production-specific settings
    if env == 'production':
        base_config.update({
            'DEBUG': False,
            'TESTING': False,
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 86400  # 24 hours
        })
    else:
        # Development settings
        base_config.update({
            'DEBUG': True,
            'TESTING': False,
            'SESSION_COOKIE_SECURE': False,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax'
        })
    
    return base_config

# Fallback configuration for backwards compatibility
config = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///app.db'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
    'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
    'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
    'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
    'RECAPTCHA_SITE_KEY': os.environ.get('RECAPTCHA_SITE_KEY'),
    'RECAPTCHA_SECRET_KEY': os.environ.get('RECAPTCHA_SECRET_KEY'),
    'RECAPTCHA_V3_SITE_KEY': os.environ.get('RECAPTCHA_V3_SITE_KEY'),
    'RECAPTCHA_V3_SECRET_KEY': os.environ.get('RECAPTCHA_V3_SECRET_KEY'),
    'FLASK_ENV': os.environ.get('FLASK_ENV', 'development'),
    'UPLOAD_FOLDER': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
    'DEBUG': False,
    'TESTING': False
}
