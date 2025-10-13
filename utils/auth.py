"""
Authentication utilities for OTRS Web Application
"""

from functools import wraps
from flask import request, jsonify, render_template, redirect, url_for, flash, session, abort
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime, timedelta
from services import system_config_service

class PasswordProtection:
    """Password protection utility class"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

def require_daily_stats_password(f):
    """Decorator to require password for daily statistics access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if password is already validated in session
        if 'daily_stats_authenticated' in session:
            # Check if session is still valid (2 hours)
            auth_time = session.get('daily_stats_auth_time')
            if auth_time:
                auth_datetime = datetime.fromisoformat(auth_time)
                if datetime.utcnow() - auth_datetime < timedelta(hours=2):
                    return f(*args, **kwargs)
            
            # Session expired, remove from session
            session.pop('daily_stats_authenticated', None)
            session.pop('daily_stats_auth_time', None)
        
        # Check if password is provided in request
        if request.method == 'POST':
            password = request.form.get('password') or request.json.get('password') if request.is_json else None
        else:
            password = request.args.get('password')
        
        # Get expected password from config
        expected_password = os.environ.get('DAILY_STATS_PASSWORD') or 'Enabling@2025'
        
        if password and password == expected_password:
            # Set session for 2 hours
            session['daily_stats_authenticated'] = True
            session['daily_stats_auth_time'] = datetime.utcnow().isoformat()
            return f(*args, **kwargs)
        
        # Return password form
        if request.is_json:
            return jsonify({
                'error': 'Password required',
                'message': 'Please provide password in request'
            }), 401
        
        return render_template('password_required.html', target_url=request.url)
    
    return decorated_function

def require_admin_password(f):
    """Decorator to require admin password for configuration management"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if admin is already authenticated in session
        if 'admin_authenticated' in session:
            # Check if session is still valid (1 hour)
            auth_time = session.get('admin_auth_time')
            if auth_time:
                auth_datetime = datetime.fromisoformat(auth_time)
                if datetime.utcnow() - auth_datetime < timedelta(hours=1):
                    return f(*args, **kwargs)
            
            # Session expired, remove from session
            session.pop('admin_authenticated', None)
            session.pop('admin_auth_time', None)
        
        # Check if password is provided in request
        if request.method == 'POST':
            password = request.form.get('admin_password') or request.json.get('admin_password') if request.is_json else None
        else:
            password = request.args.get('admin_password')
        
        # Get expected admin password from system config service
        expected_password = system_config_service.get_config_value('ADMIN_PASSWORD', 'admin@2025')
        
        if password and password == expected_password:
            # Set session for 1 hour
            session['admin_authenticated'] = True
            session['admin_auth_time'] = datetime.utcnow().isoformat()
            return f(*args, **kwargs)
        
        # Return admin password form
        if request.is_json:
            return jsonify({
                'error': 'Admin password required',
                'message': 'Please provide admin password in request'
            }), 401
        
        # For AJAX requests, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'error': 'Admin password required',
                'message': 'Please provide admin password in request'
            }), 401
        
        return render_template('admin/password_required.html')
    
    return decorated_function

# Global password protection instance
password_protection = PasswordProtection()