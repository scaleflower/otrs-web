"""
System configuration database model
"""

from datetime import datetime
from . import db

class SystemConfig(db.Model):
    """System configuration table for storing application settings"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)  # Configuration key
    value = db.Column(db.Text)  # Configuration value
    description = db.Column(db.String(500))  # Description of the configuration
    category = db.Column(db.String(100))  # Configuration category (e.g., security, database, etc.)
    is_encrypted = db.Column(db.Boolean, default=False)  # Whether the value is encrypted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'
    
    def to_dict(self):
        """Convert system config to dictionary"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'category': self.category,
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_config_value(cls, key, default=None):
        """Get configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        if config:
            return config.value
        return default
    
    @classmethod
    def set_config_value(cls, key, value, description="", category="", is_encrypted=False):
        """Set configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.description = description
            config.category = category
            config.is_encrypted = is_encrypted
            config.updated_at = datetime.utcnow()
        else:
            config = cls(
                key=key,
                value=value,
                description=description,
                category=category,
                is_encrypted=is_encrypted
            )
            db.session.add(config)
        db.session.commit()
        return config
    
    @classmethod
    def get_all_configs(cls):
        """Get all configurations"""
        return cls.query.all()
    
    @classmethod
    def get_configs_by_category(cls, category):
        """Get configurations by category"""
        return cls.query.filter_by(category=category).all()