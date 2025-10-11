"""
System configuration model for OTRS Web Application
"""

from . import db
from utils.encryption import encrypt_data, decrypt_data
from flask import current_app

class SystemConfig(db.Model):
    """System configuration model"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    is_encrypted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_decrypted_value(),
            'description': self.description,
            'category': self.category,
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    def get_decrypted_value(self):
        """Get decrypted value"""
        if self.is_encrypted:
            try:
                secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
                return decrypt_data(self.value, secret_key)
            except Exception:
                # If decryption fails, return the encrypted value
                return self.value
        
        return self.value
        
    def set_encrypted_value(self, value):
        """Set encrypted value"""
        if self.is_encrypted:
            secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
            self.value = encrypt_data(value, secret_key)
        else:
            self.value = value
    
    @staticmethod
    def get_config_value(key):
        """
        Get decrypted configuration value by key
        
        Args:
            key: Configuration key
            
        Returns:
            Decrypted configuration value or None if not found
        """
        config = SystemConfig.query.filter_by(key=key).first()
        if not config:
            return None
            
        if config.is_encrypted:
            try:
                secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
                return decrypt_data(config.value, secret_key)
            except Exception:
                # If decryption fails, return None
                return None
        
        return config.value
    
    @classmethod
    def set_config_value(cls, key, value, description="", category="", is_encrypted=False):
        """Set configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        if config:
            config.key = key
            config.description = description
            config.category = category
            config.is_encrypted = is_encrypted
            if is_encrypted:
                secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
                config.value = encrypt_data(value, secret_key)
            else:
                config.value = value
        else:
            config = cls(
                key=key,
                description=description,
                category=category,
                is_encrypted=is_encrypted
            )
            if is_encrypted:
                secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
                config.value = encrypt_data(value, secret_key)
            else:
                config.value = value
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