"""
System initialization blueprint for first-time setup
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from models import db, SystemConfig, AppUpdateStatus
from config import Config
import os

init_bp = Blueprint('init_bp', __name__, url_prefix='/init')

@init_bp.route('/')
def init_welcome():
    """Show initialization welcome page"""
    # Check if system is already initialized
    initialized = SystemConfig.query.filter_by(key='system_initialized').first()
    if initialized and initialized.value == 'true':
        return redirect(url_for('index'))
    
    return render_template('init/welcome.html')

@init_bp.route('/database')
def init_database():
    """Show database configuration page"""
    # Check if system is already initialized
    initialized = SystemConfig.query.filter_by(key='system_initialized').first()
    if initialized and initialized.value == 'true':
        return redirect(url_for('index'))
    
    return render_template('init/database.html')

@init_bp.route('/admin')
def init_admin():
    """Show admin user configuration page"""
    # Check if system is already initialized
    initialized = SystemConfig.query.filter_by(key='system_initialized').first()
    if initialized and initialized.value == 'true':
        return redirect(url_for('index'))
    
    return render_template('init/admin.html')

@init_bp.route('/complete')
def init_complete():
    """Show initialization completion page"""
    # Check if system is already initialized
    initialized = SystemConfig.query.filter_by(key='system_initialized').first()
    if initialized and initialized.value == 'true':
        return redirect(url_for('index'))
    
    return render_template('init/complete.html')

@init_bp.route('/api/database', methods=['POST'])
def api_configure_database():
    """Configure database settings"""
    try:
        data = request.get_json()
        db_type = data.get('db_type', 'sqlite')
        
        # Save database configuration
        if db_type == 'sqlite':
            db_path = data.get('db_path', 'db/otrs_data.db')
            db_uri = f'sqlite:///{db_path}'
        elif db_type == 'postgresql':
            host = data.get('db_host', 'localhost')
            port = data.get('db_port', '5432')
            name = data.get('db_name', 'otrs_db')
            user = data.get('db_user', 'otrs_user')
            password = data.get('db_password', '')
            db_uri = f'postgresql://{user}:{password}@{host}:{port}/{name}'
        elif db_type == 'mysql':
            host = data.get('db_host', 'localhost')
            port = data.get('db_port', '3306')
            name = data.get('db_name', 'otrs_db')
            user = data.get('db_user', 'otrs_user')
            password = data.get('db_password', '')
            db_uri = f'mysql://{user}:{password}@{host}:{port}/{name}'
        
        # Save to system config
        db_config = SystemConfig.query.filter_by(key='database_uri').first()
        if not db_config:
            db_config = SystemConfig(key='database_uri', value=db_uri)
            db.session.add(db_config)
        else:
            db_config.value = db_uri
            
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@init_bp.route('/api/admin', methods=['POST'])
def api_configure_admin():
    """Configure admin user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # TODO: Implement admin user creation
        # This would typically involve creating a User model and hashing the password
        
        # Mark system as initialized
        initialized = SystemConfig.query.filter_by(key='system_initialized').first()
        if not initialized:
            initialized = SystemConfig(key='system_initialized', value='true')
            db.session.add(initialized)
        else:
            initialized.value = 'true'
            
        # Set initial version
        update_status = AppUpdateStatus.query.first()
        if not update_status:
            update_status = AppUpdateStatus(current_version=Config.APP_VERSION)
            db.session.add(update_status)
            
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500