import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session
from flask_cors import CORS
from config import Config
from utils.db import init_db
from utils.auth import get_current_user
from routes.auth import auth_bp
from routes.table import table_bp
from routes.api import api_bp

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY  # Required for sessions
CORS(app, supports_credentials=True)

# Setup logging
def setup_logging():
    """Configure application logging"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Kitchen Table startup')

setup_logging()

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(table_bp)
app.register_blueprint(api_bp)

# Routes
@app.route('/')
def index():
    """Landing page"""
    user = get_current_user()
    if user:
        return render_template('redirect.html', url='/table')
    return render_template('landing.html')

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    app.logger.error(f"Server error: {str(error)}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

# Initialize database on first run
@app.before_request
def initialize():
    """Initialize database if needed"""
    if not os.path.exists(Config.DATABASE_PATH):
        app.logger.info("Initializing database...")
        if init_db():
            app.logger.info("Database initialized successfully")
        else:
            app.logger.error("Failed to initialize database")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
