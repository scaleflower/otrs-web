"""
Authentication utilities for OTRS Web Application
"""

from functools import wraps
from flask import request, jsonify, session, current_app
import hashlib
import secrets

class PasswordProtection:
    """Password protection utilities for daily statistics"""
    
    SESSION_KEY = 'daily_stats_authenticated'
    
    @staticmethod
    def hash_password(password):
        """Create a hash of the password for comparison"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_password(provided_password):
        """Verify if the provided password matches the configured password"""
        configured_password = current_app.config.get('DAILY_STATS_PASSWORD', 'admin123')
        return provided_password == configured_password
    
    @staticmethod
    def is_authenticated():
        """Check if the current session is authenticated for daily stats modifications"""
        return session.get(PasswordProtection.SESSION_KEY, False)
    
    @staticmethod
    def authenticate_session():
        """Mark the current session as authenticated"""
        session[PasswordProtection.SESSION_KEY] = True
        session.permanent = True
    
    @staticmethod
    def deauthenticate_session():
        """Remove authentication from the current session"""
        session.pop(PasswordProtection.SESSION_KEY, None)

def require_daily_stats_password(f):
    """
    Decorator to require password authentication for daily statistics modification endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if already authenticated in this session
        if PasswordProtection.is_authenticated():
            return f(*args, **kwargs)
        
        # Check if password is provided in the request
        try:
            if request.is_json:
                data = request.get_json() or {}
                password = data.get('auth_password')
            else:
                password = request.form.get('auth_password')
        except Exception:
            # If JSON parsing fails, assume no password provided
            password = None
        
        if not password:
            return jsonify({
                'error': 'Password required for this operation',
                'auth_required': True
            }), 401
        
        # Verify password
        if not PasswordProtection.verify_password(password):
            return jsonify({
                'error': 'Invalid password',
                'auth_required': True
            }), 401
        
        # Authenticate session
        PasswordProtection.authenticate_session()
        
        # Proceed with the original function
        return f(*args, **kwargs)
    
    return decorated_function
