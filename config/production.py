"""
Production configuration for OTRS Web Application
"""

import os
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration class"""
    
    DEBUG = False
    TESTING = False
    
    # Database settings - support both SQLite and PostgreSQL
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
    
    if DATABASE_TYPE == 'postgresql':
        # PostgreSQL configuration
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = os.environ.get('DB_PORT', '5432')
        DB_NAME = os.environ.get('DB_NAME', 'otrs_db')
        DB_USER = os.environ.get('DB_USER', 'otrs_user')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        
        # PostgreSQL specific engine options
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,  # Longer recycle time for production
            'pool_size': 10,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10,
            }
        }
    else:
        # SQLite configuration (default)
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///db/otrs_data.db'
        
        # SQLite specific engine options
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,  # Longer recycle time for production
        }
    
    SQLALCHEMY_ECHO = False  # Disable SQL query logging in production
    
    # Logging settings
    LOG_LEVEL = 'WARNING'
    
    # Cache settings
    CACHE_TYPE = "redis" if os.environ.get('REDIS_URL') else "simple"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = 600  # Longer cache timeout for production
    
    # Production specific settings
    TEMPLATES_AUTO_RELOAD = False
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year caching for static files
    
    # Scheduler settings
    SCHEDULER_ENABLED = True
    
    # Security settings (strict for production)
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Error handling
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS', '').split(',') if os.environ.get('ADMINS') else []
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with production configuration"""
        BaseConfig.init_app(app)
        
        # Production specific initialization
        print("🔒 Running in PRODUCTION mode")
        print(f"🗄️  Using database type: {cls.DATABASE_TYPE}")
        
        # Set up error logging via email
        if cls.MAIL_SERVER:
            import logging
            from logging.handlers import SMTPHandler
            
            auth = None
            if cls.MAIL_USERNAME or cls.MAIL_PASSWORD:
                auth = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            
            secure = None
            if cls.MAIL_USE_TLS:
                secure = ()
            
            mail_handler = SMTPHandler(
                mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
                fromaddr=cls.MAIL_USERNAME,
                toaddrs=cls.ADMINS,
                subject='OTRS Web Application Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)