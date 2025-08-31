#!/usr/bin/env python3
"""
Production WSGI configuration for Gidamart
Compatible with shared hosting environments like Namecheap
"""
import os
import sys
import traceback

# Get the directory containing this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to Python path for absolute imports
sys.path.insert(0, current_dir)

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")

def create_error_app(error_message, details=""):
    """Create a simple error application"""
    def error_application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gidamart - Configuration Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .error {{ background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 5px; }}
                .details {{ background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 5px; }}
                code {{ background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>🚨 Gidamart Configuration Error</h1>
            <div class="error">
                <h3>Error Message:</h3>
                <p>{error_message}</p>
            </div>
            <div class="details">
                <h3>Technical Details:</h3>
                <p><strong>Current Directory:</strong> <code>{os.getcwd()}</code></p>
                <p><strong>Python Version:</strong> <code>{sys.version}</code></p>
                <p><strong>Python Path:</strong></p>
                <ul>
        """
        
        for path in sys.path[:5]:  # Show first 5 paths
            html += f"<li><code>{path}</code></li>"
        
        html += f"""
                </ul>
                {details}
            </div>
            <p><em>Please check server logs and ensure all dependencies are installed.</em></p>
        </body>
        </html>
        """
        
        return [html.encode('utf-8')]
    
    return error_application

try:
    # Import the Flask application
    from src.main import app as application
    
    # Ensure app is in production mode
    application.config['DEBUG'] = False
    application.config['TESTING'] = False
    
    print("✅ WSGI application loaded successfully")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("📁 Available files in current directory:")
    try:
        for item in os.listdir('.'):
            print(f"   - {item}")
    except:
        print("   Could not list directory")
    
    # Check if src directory exists
    if not os.path.exists('src'):
        error_msg = "The 'src' directory is missing. Please ensure all application files are uploaded correctly."
        details = """
        <p><strong>Expected structure:</strong></p>
        <ul>
            <li><code>src/</code> directory</li>
            <li><code>src/main.py</code> file</li>
            <li><code>src/models/</code> directory</li>
            <li><code>src/routes/</code> directory</li>
            <li><code>src/templates/</code> directory</li>
        </ul>
        """
    else:
        error_msg = f"Cannot import Flask application: {str(e)}"
        details = f"<p><strong>Full traceback:</strong></p><pre>{traceback.format_exc()}</pre>"
    
    application = create_error_app(error_msg, details)
    
except Exception as e:
    print(f"❌ WSGI application failed to load: {e}")
    print(f"📋 Full traceback:")
    traceback.print_exc()
    
    error_msg = f"Unexpected error while loading application: {str(e)}"
    details = f"<p><strong>Full traceback:</strong></p><pre>{traceback.format_exc()}</pre>"
    application = create_error_app(error_msg, details)

# For compatibility with different WSGI servers
app = application

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    try:
        application.run(host='0.0.0.0', port=8000, debug=False)
    except:
        print("Cannot run application directly")
        sys.exit(1)
