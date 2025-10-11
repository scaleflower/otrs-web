"""
Base configuration for OTRS Web Application
"""

import os
from datetime import timedelta

class BaseConfig:
    """Base configuration class"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    APP_VERSION = "1.2.3"
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Disable SQL query logging for better performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # Scheduler settings
    SCHEDULER_DEFAULT_TIME = "23:59"
    SCHEDULER_TIMEZONE = "Asia/Shanghai"
    
    # Logging settings
    LOG_FOLDER = os.environ.get('LOG_FOLDER') or 'logs'
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # Server settings
    APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
    APP_PORT = int(os.environ.get('APP_PORT', os.environ.get('PORT', '15001')))
    
    # Cache settings
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Database backup settings
    BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER') or 'database_backups'
    AUTO_BACKUP = os.environ.get('AUTO_BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_TIME = os.environ.get('BACKUP_TIME') or '02:00'
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
    
    # API settings
    API_RATE_LIMIT = "100 per hour"
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Daily Statistics Password Protection
    DAILY_STATS_PASSWORD = os.environ.get('DAILY_STATS_PASSWORD') or 'Enabling@2025'

    # Session settings for password protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 密码认证有效期2小时

    # Auto update settings
    APP_UPDATE_ENABLED = os.environ.get('APP_UPDATE_ENABLED', 'true').lower() == 'true'
    APP_UPDATE_REPO = os.environ.get('APP_UPDATE_REPO', 'scaleflower/otrs-web')
    APP_UPDATE_BRANCH = os.environ.get('APP_UPDATE_BRANCH', 'main')
    APP_UPDATE_SCRIPT = os.environ.get('APP_UPDATE_SCRIPT', 'scripts/update_app.py')
    APP_UPDATE_GITHUB_TOKEN = os.environ.get('APP_UPDATE_GITHUB_TOKEN')
    APP_UPDATE_RESTART_DELAY = int(os.environ.get('APP_UPDATE_RESTART_DELAY', '5'))
    APP_UPDATE_DOWNLOAD_DIR = os.environ.get('APP_UPDATE_DOWNLOAD_DIR')
    APP_UPDATE_PRESERVE_PATHS = os.environ.get(
        'APP_UPDATE_PRESERVE_PATHS',
        '.env,uploads,database_backups,logs,db/otrs_data.db'
    )
    APP_UPDATE_INSTALL_DEPENDENCIES = os.environ.get('APP_UPDATE_INSTALL_DEPENDENCIES', 'true').lower() in ['1', 'true', 'yes', 'on']
    APP_UPDATE_RUN_MIGRATIONS = os.environ.get('APP_UPDATE_RUN_MIGRATIONS', 'true').lower() in ['1', 'true', 'yes', 'on']
    APP_UPDATE_PIP_ARGS = os.environ.get('APP_UPDATE_PIP_ARGS')
    APP_UPDATE_MIGRATION_SCRIPTS = os.environ.get('APP_UPDATE_MIGRATION_SCRIPTS')

    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create required directories
        for folder in [BaseConfig.UPLOAD_FOLDER, BaseConfig.LOG_FOLDER, BaseConfig.BACKUP_FOLDER]:
            os.makedirs(folder, exist_ok=True)
