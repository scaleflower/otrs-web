"""
Service for managing system configurations
"""

from models import SystemConfig, db
from datetime import datetime
import json
import os


class SystemConfigService:
    """Service for handling system configuration operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize service with Flask app"""
        self.app = app
    
    def get_config_value(self, key, default=None):
        """
        Get configuration value by key
        First check database, then check environment variables, finally return default
        """
        # Check database first
        db_value = SystemConfig.get_config_value(key)
        if db_value is not None:
            return db_value
        
        # Check environment variables
        if self.app and key in self.app.config:
            return self.app.config[key]
        
        env_value = self._get_env_value(key)
        if env_value is not None:
            return env_value
        
        # Return default value
        return default
    
    def _get_env_value(self, key):
        """Get value from environment variables"""
        # Map config keys to environment variable names
        env_mapping = {
            'SECRET_KEY': 'SECRET_KEY',
            'APP_PORT': 'APP_PORT',
            'APP_HOST': 'APP_HOST',
            'DAILY_STATS_PASSWORD': 'DAILY_STATS_PASSWORD',
            'APP_UPDATE_GITHUB_TOKEN': 'APP_UPDATE_GITHUB_TOKEN',
            'BACKUP_RETENTION_DAYS': 'BACKUP_RETENTION_DAYS',
            'BACKUP_TIME': 'BACKUP_TIME',
            'ADMIN_PASSWORD': 'ADMIN_PASSWORD'
        }
        
        env_key = env_mapping.get(key, key)
        return os.environ.get(env_key)
    
    def set_config_value(self, key, value, description="", category="", is_encrypted=False):
        """Set configuration value"""
        # Ensure we're in an application context
        if not self.app:
            raise RuntimeError("SystemConfigService not initialized with Flask app")
            
        with self.app.app_context():
            return SystemConfig.set_config_value(
                key=key,
                value=value,
                description=description,
                category=category,
                is_encrypted=is_encrypted
            )
    
    def get_all_configs(self):
        """Get all configurations"""
        # Ensure we're in an application context
        if not self.app:
            raise RuntimeError("SystemConfigService not initialized with Flask app")
            
        with self.app.app_context():
            return SystemConfig.get_all_configs()
    
    def get_configs_by_category(self, category):
        """Get configurations by category"""
        # Ensure we're in an application context
        if not self.app:
            raise RuntimeError("SystemConfigService not initialized with Flask app")
            
        with self.app.app_context():
            return SystemConfig.get_configs_by_category(category)
    
    def get_config_dict(self):
        """Get all configurations as dictionary"""
        configs = self.get_all_configs()
        return {config.key: config.value for config in configs}
    
    def initialize_default_configs(self):
        """Initialize default configurations"""
        # Ensure we're in an application context
        if not self.app:
            raise RuntimeError("SystemConfigService not initialized with Flask app")
            
        with self.app.app_context():
            default_configs = [
                {
                    'key': 'SECRET_KEY',
                    'value': 'dev-secret-key-change-in-production',
                    'description': 'Application secret key for security',
                    'category': 'security'
                },
                {
                    'key': 'APP_PORT',
                    'value': '5001',
                    'description': 'Application port',
                    'category': 'server'
                },
                {
                    'key': 'APP_HOST',
                    'value': '0.0.0.0',
                    'description': 'Application host',
                    'category': 'server'
                },
                {
                    'key': 'DAILY_STATS_PASSWORD',
                    'value': 'Enabling@2025',
                    'description': 'Password for daily statistics access',
                    'category': 'security'
                },
                {
                    'key': 'APP_UPDATE_GITHUB_TOKEN',
                    'value': '',
                    'description': 'GitHub token for update checks',
                    'category': 'update',
                    'is_encrypted': True
                },
                {
                    'key': 'BACKUP_RETENTION_DAYS',
                    'value': '30',
                    'description': 'Number of days to keep backups',
                    'category': 'backup'
                },
                {
                    'key': 'BACKUP_TIME',
                    'value': '02:00',
                    'description': 'Time to perform automatic backups',
                    'category': 'backup'
                },
                {
                    'key': 'ADMIN_PASSWORD',
                    'value': 'admin@2025',
                    'description': 'Admin password for configuration management',
                    'category': 'security',
                    'is_encrypted': True
                }
            ]
            
            for config_data in default_configs:
                # Only initialize if not already exists
                existing = SystemConfig.query.filter_by(key=config_data['key']).first()
                if not existing:
                    self.set_config_value(
                        key=config_data['key'],
                        value=config_data['value'],
                        description=config_data['description'],
                        category=config_data['category'],
                        is_encrypted=config_data.get('is_encrypted', False)
                    )