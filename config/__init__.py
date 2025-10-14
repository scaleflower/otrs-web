"""
Configuration module for OTRS Web Application
"""

import os
from .base import Config as BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV') or 'default'
    return config_map.get(env, BaseConfig)