"""
Base configuration for OTRS Web Application
"""

import os
from datetime import timedelta

class BaseConfig:
    """Base configuration class"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    APP_VERSION = "1.2.2"
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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
    
    # Cache settings
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Database backup settings
    BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER') or 'database_backups'
    AUTO_BACKUP = True
    
    # API settings
    API_RATE_LIMIT = "100 per hour"
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create required directories
        for folder in [BaseConfig.UPLOAD_FOLDER, BaseConfig.LOG_FOLDER, BaseConfig.BACKUP_FOLDER]:
            os.makedirs(folder, exist_ok=True)
