import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Initialize database drivers if needed
try:
    # Try to import PyMySQL for MySQL support (if available)
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # PyMySQL not available, will use SQLite

from flask import Flask, send_from_directory, render_template
from flask_login import LoginManager
from src.models import db, User, Property, PropertyImage, ContactInquiry, UserApplication, AdminLog, State, LocalGovernment
from src.routes.user import user_bp
from src.routes.admin import admin_bp
from src.routes.admin_antispam import admin_antispam_bp
from src.routes.public import public_bp
from src.config import get_config

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    try:
        config = get_config()
        app.config.update(config)
        print(f"✅ Configuration loaded: {app.config.get('FLASK_ENV', 'development')} environment")
    except Exception as e:
        print(f"⚠️ Configuration warning: {e}")
        # Fallback configuration
        from src.config import config
        app.config.update(config)
        print("✅ Fallback configuration loaded")
    
    # Initialize database
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'public.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_antispam_bp, url_prefix='/admin/antispam')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Serve favicon
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        try:
            # Quick DB check
            db.session.execute(db.text('SELECT 1'))
            return {'status': 'ok'}, 200
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

    # Create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables verified/created")
        except Exception as e:
            print(f"⚠️ Database warning: {e}")
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
