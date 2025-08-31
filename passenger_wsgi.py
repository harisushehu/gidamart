#!/usr/bin/env python3
"""
Production Passenger WSGI Configuration for Namecheap Hosting
"""

import sys
import os
import traceback

# Set up paths
app_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(app_dir, 'src')

# Add directories to Python path
sys.path.insert(0, app_dir)
sys.path.insert(0, src_dir)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DEBUG'] = 'False'

# Change to app directory
os.chdir(app_dir)

def create_error_page(error_type, error_message, traceback_str=None):
    """Create a detailed error page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gidamart - {error_type}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .error {{ color: #dc3545; }}
            .success {{ color: #28a745; }}
            .warning {{ color: #ffc107; background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; }}
            pre {{ background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ padding: 5px; border-bottom: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="error">🚨 {error_type}</h1>
            <p><strong>Error:</strong> {error_message}</p>
            
            <div class="warning">
                <strong>⚠️ MOST LIKELY ISSUE:</strong> The .env file is missing from your server!<br>
                The .env file is ignored by git and must be uploaded manually.
            </div>
            
            <h3>Environment Info:</h3>
            <ul>
                <li><strong>Working Directory:</strong> {os.getcwd()}</li>
                <li><strong>Python Version:</strong> {sys.version}</li>
                <li><strong>App Directory:</strong> {app_dir}</li>
                <li><strong>Src Directory Exists:</strong> {os.path.exists(src_dir)}</li>
                <li><strong>.env File Exists:</strong> {os.path.exists(os.path.join(app_dir, '.env'))}</li>
            </ul>
            
            <h3>Python Path:</h3>
            <ul>
                {''.join(f'<li>{p}</li>' for p in sys.path[:8])}
            </ul>
            
            <h3>Files in App Directory:</h3>
            <ul>
                {''.join(f'<li>{f}</li>' for f in sorted(os.listdir(app_dir)) if not f.startswith('.') and os.path.isfile(os.path.join(app_dir, f)))}
            </ul>
            
            <h3>Files in Src Directory:</h3>
            <ul>
                {''.join(f'<li>{f}</li>' for f in sorted(os.listdir(src_dir)) if os.path.exists(src_dir) and not f.startswith('.') and os.path.isfile(os.path.join(src_dir, f)))}
            </ul>
            
            {f'<h3>Traceback:</h3><pre>{traceback_str}</pre>' if traceback_str else ''}
            
            <h3>🔧 How to Fix:</h3>
            <ol>
                <li>The .env file is in your local folder but not on the server</li>
                <li>You need to manually upload the .env file</li>
                <li>Or copy the .env content and create it on the server</li>
            </ol>
        </div>
    </body>
    </html>
    """.encode('utf-8')

def error_application(environ, start_response, error_type, error_message, traceback_str=None):
    """WSGI error application"""
    status = '500 Internal Server Error'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [create_error_page(error_type, error_message, traceback_str)]

# Try to import the Flask application
try:
    from src.main import app as application
    # If we get here, the import was successful
    
except ImportError as e:
    # Import failed - create error application
    def application(environ, start_response):
        return error_application(environ, start_response, "Import Error", str(e), traceback.format_exc())
        
except Exception as e:
    # Other error - create error application
    def application(environ, start_response):
        return error_application(environ, start_response, "Configuration Error", str(e), traceback.format_exc())
