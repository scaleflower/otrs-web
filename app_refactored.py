"""
OTRS Ticket Analysis Web Application - Refactored
Flask-based ticket data analysis web application with modular architecture
"""

# Load environment variables from .env file (if available)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️  python-dotenv 未安装，使用系统环境变量")
    print("💡 安装提示：pip install python-dotenv")
except Exception as e:
    print(f"⚠️  加载 .env 文件时出错：{e}")

from flask import Flask, render_template, jsonify
import os

# Re-import configuration classes to ensure environment variables are loaded
import importlib
import config
importlib.reload(config)
from config import Config
from models import init_db

# Import services
from services import (
    init_services,
    ticket_service,
    analysis_service,
    export_service,
    scheduler_service,
    update_service
)

# Import blueprints
from blueprints.upload_bp import upload_bp
from blueprints.statistics_bp import statistics_bp
from blueprints.export_bp import export_bp
from blueprints.daily_stats_bp import daily_stats_bp
from blueprints.backup_bp import backup_bp
from blueprints.update_bp import update_bp

# Create Flask application
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Initialize database
init_db(app)

# Initialize services
init_services(app)

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(statistics_bp)
app.register_blueprint(export_bp)
app.register_blueprint(daily_stats_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(update_bp)

# Perform an initial update check so clients know the latest version
if app.config.get('APP_UPDATE_ENABLED', True):
    try:
        update_service.check_for_updates()
    except Exception as exc:  # pragma: no cover - logging path
        app.logger.warning('Initial update check failed: %s', exc)

# Application version from config
APP_VERSION = app.config.get('APP_VERSION', '1.2.9')

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', APP_VERSION=APP_VERSION)

@app.route('/update-logs')
def update_logs_page():
    """Update logs page"""
    return render_template('update_logs.html', APP_VERSION=APP_VERSION)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

if __name__ == '__main__':
    # Initialize configuration
    Config.init_app(app)
    
    # Determine runtime configuration (prefer environment overrides for convenience)
    host = os.environ.get('APP_HOST', app.config.get('APP_HOST', '0.0.0.0'))
    port = int(os.environ.get('APP_PORT', app.config.get('APP_PORT', 5001)))
    debug_flag = app.config.get('DEBUG', False)
    
    # Run application
    app.run(
        debug=debug_flag,
        host=host,
        port=port
    )
