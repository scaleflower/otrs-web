"""
Development configuration for OTRS Web Application
"""

import os
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development configuration class"""
    
    DEBUG = True
    TESTING = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///../db/otrs_data.db'
    SQLALCHEMY_ECHO = True  # Enable SQL query logging in development
    
    # Logging settings
    LOG_LEVEL = 'DEBUG'
    
    # Cache settings
    CACHE_TYPE = "simple"
    
    # Development specific settings
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for development
    
    # Scheduler settings
    SCHEDULER_ENABLED = True
    
    # Security settings (relaxed for development)
    WTF_CSRF_ENABLED = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with development configuration"""
        BaseConfig.init_app(app)
        
        # Development specific initialization
        print("🚀 Running in DEVELOPMENT mode")
        print(f"📁 Upload folder: {cls.UPLOAD_FOLDER}")
        print(f"📊 Database: {cls.SQLALCHEMY_DATABASE_URI}")
        print(f"📝 Log level: {cls.LOG_LEVEL}")
