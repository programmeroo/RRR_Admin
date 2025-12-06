"""
RRR_Admin - Admin Web Application for RateReadyRealtor
Accesses all data via REST API calls to RRR_Server
"""

# Fix Windows console encoding for emojis
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, session
from flask_cors import CORS
from datetime import datetime
from config import DevelopmentConfig, ProductionConfig
import os


def create_app():
    app = Flask(__name__)

    # Select environment config
    if os.environ.get("FLASK_ENV") == "production":
        print("✅ PRODUCTION MODE")
        app.config.from_object(ProductionConfig)
    else:
        print("✅ DEVELOPMENT MODE")
        app.config.from_object(DevelopmentConfig)

    # Initialize API mode in session
    @app.before_request
    def initialize_session():
        if 'api_mode' not in session:
            session['api_mode'] = 'local' if app.config.get('DEBUG') else 'remote'

    return app


# ---------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------

app = create_app()

print(f"📡 API URL: {app.config.get('API_URL')}")
print(f"🔑 API Key configured: {'Yes' if app.config.get('API_KEY') else 'No'}")

CORS(app)


# Register Admin routes
from routes import blueprints as admin_blueprints
for bp in admin_blueprints:
    app.register_blueprint(bp)
    print(f"✅ Registered blueprint: {bp.name}")


# ---------------------------------------------------------
# Template Utilities
# ---------------------------------------------------------

@app.context_processor
def inject_template_globals():
    """Make these variables available in all templates"""
    return {
        "current_year": datetime.now().year,
        "api_mode": session.get('api_mode', 'local'),
        "api_url": app.config.get('API_URL')
    }


# ---------------------------------------------------------
# Root Route - Redirect to Admin
# ---------------------------------------------------------

from flask import redirect, url_for

@app.route("/")
def index():
    """Redirect root to admin dashboard"""
    return redirect(url_for('admin.dashboard'))


# ---------------------------------------------------------
# Static Files
# ---------------------------------------------------------

from flask import send_from_directory

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(app.static_folder, "robots.txt")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "favicon.ico", mimetype='image/x-icon')


# ---------------------------------------------------------
# Run Development Server
# ---------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Starting RRR Admin Server")
    print("="*50)
    print(f"Mode: {'PRODUCTION' if not app.config['DEBUG'] else 'DEVELOPMENT'}")
    print(f"Port: 5001")
    print(f"URL: http://localhost:5001/admin")
    print("="*50 + "\n")

    app.run(
        host="0.0.0.0",
        port=5001,  # Different port than RRR_Server (5000)
        debug=True,
        use_reloader=False
    )
