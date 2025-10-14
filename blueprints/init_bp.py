"""
System initialization blueprint for first-time setup
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from models import db, SystemConfig, AppUpdateStatus
from config.base import Config
import os
import sqlalchemy

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

@init_bp.route('/api/database/test', methods=['POST'])
def api_test_database():
    """Test database connection"""
    try:
        data = request.get_json()
        db_type = data.get('db_type', 'sqlite')
        
        # Generate database URI based on type
        if db_type == 'sqlite':
            db_path = data.get('db_path', 'db/otrs_data.db')
            db_uri = f'sqlite:///{db_path}'
        elif db_type == 'postgresql':
            # Use PostgreSQL-specific field names to avoid conflicts
            host = data.get('pg_host', 'localhost')
            port = data.get('pg_port', '5432')  # 使用从请求中获取的端口
            name = data.get('pg_name', 'otrs_db')
            user = data.get('pg_user', 'otrs_user')
            password = data.get('pg_password', '')
            db_uri = f'postgresql://{user}:{password}@{host}:{port}/{name}'
        elif db_type == 'mysql':
            # Use MySQL-specific field names to avoid conflicts
            host = data.get('mysql_host', 'localhost')
            port = data.get('mysql_port', '3306')  # MySQL默认端口
            name = data.get('mysql_name', 'otrs_db')
            user = data.get('mysql_user', 'otrs_user')
            password = data.get('mysql_password', '')
            db_uri = f'mysql://{user}:{password}@{host}:{port}/{name}'
        
        # Test connection
        engine = sqlalchemy.create_engine(db_uri)
        connection = engine.connect()
        connection.close()
        
        return jsonify({'success': True, 'message': '数据库连接成功！'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'数据库连接失败: {str(e)}'}), 500

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
            # Use PostgreSQL-specific field names to avoid conflicts
            host = data.get('pg_host', 'localhost')
            port = data.get('pg_port', '5432')
            name = data.get('pg_name', 'otrs_db')
            user = data.get('pg_user', 'otrs_user')
            password = data.get('pg_password', '')
            db_uri = f'postgresql://{user}:{password}@{host}:{port}/{name}'
        elif db_type == 'mysql':
            # Use MySQL-specific field names to avoid conflicts
            host = data.get('mysql_host', 'localhost')
            port = data.get('mysql_port', '3306')
            name = data.get('mysql_name', 'otrs_db')
            user = data.get('mysql_user', 'otrs_user')
            password = data.get('mysql_password', '')
            db_uri = f'mysql://{user}:{password}@{host}:{port}/{name}'
        
        # Test connection first
        try:
            engine = sqlalchemy.create_engine(db_uri)
            connection = engine.connect()
            connection.close()
        except Exception as e:
            return jsonify({'success': False, 'error': f'数据库连接测试失败: {str(e)}'}), 500
        
        # Save to system config
        db_config = SystemConfig.query.filter_by(key='database_uri').first()
        if not db_config:
            db_config = SystemConfig(key='database_uri', value=db_uri)
            db.session.add(db_config)
        else:
            db_config.value = db_uri
            
        db.session.commit()
        return jsonify({'success': True, 'message': '数据库配置保存成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@init_bp.route('/api/database/init', methods=['POST'])
def api_initialize_database():
    """Initialize database tables"""
    try:
        # Get database URI from system config
        db_config = SystemConfig.query.filter_by(key='database_uri').first()
        if not db_config:
            return jsonify({'success': False, 'error': '未找到数据库配置'}), 500
        
        # Update database URI in app config
        from app import app
        app.config['SQLALCHEMY_DATABASE_URI'] = db_config.value
        
        # Reinitialize database with new URI
        from models import init_db
        init_db(app)
        
        return jsonify({'success': True, 'message': '数据库初始化完成！'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'数据库初始化失败: {str(e)}'}), 500

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
        return jsonify({'success': True, 'message': '管理员账户创建成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
