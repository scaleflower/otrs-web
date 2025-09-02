"""
Configuration module for OTRS Web Application
"""

import os
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, config_map['default'])

# Export commonly used config
Config = get_config()
