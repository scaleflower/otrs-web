"""
Admin blueprint for system configuration management
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models import SystemConfig
from services import system_config_service
import json

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', methods=['GET', 'POST'])
def admin_dashboard():
    """Admin dashboard"""
    configs = system_config_service.get_all_configs()
    return render_template('admin/dashboard.html', configs=configs)

@admin_bp.route('/configs')
def config_list():
    """List all configurations"""
    configs = system_config_service.get_all_configs()
    return render_template('admin/config_list.html', configs=configs)

@admin_bp.route('/configs/edit/<int:config_id>', methods=['GET', 'POST'])
def edit_config(config_id):
    """Edit a configuration"""
    config = SystemConfig.query.get_or_404(config_id)
    
    if request.method == 'POST':
        try:
            config.value = request.form.get('value', config.value)
            config.description = request.form.get('description', config.description)
            config.category = request.form.get('category', config.category)
            config.is_encrypted = bool(request.form.get('is_encrypted'))
            
            from models import db
            db.session.commit()
            
            flash('配置更新成功', 'success')
            return redirect(url_for('admin.config_list'))
        except Exception as e:
            flash(f'更新配置时出错: {str(e)}', 'error')
    
    return render_template('admin/config_edit.html', config=config)

@admin_bp.route('/configs/create', methods=['GET', 'POST'])
def create_config():
    """Create a new configuration"""
    if request.method == 'POST':
        try:
            key = request.form.get('key')
            value = request.form.get('value', '')
            description = request.form.get('description', '')
            category = request.form.get('category', '')
            is_encrypted = bool(request.form.get('is_encrypted'))
            
            # Check if key already exists
            existing = SystemConfig.query.filter_by(key=key).first()
            if existing:
                flash('配置键已存在', 'error')
                return render_template('admin/config_create.html')
            
            system_config_service.set_config_value(
                key=key,
                value=value,
                description=description,
                category=category,
                is_encrypted=is_encrypted
            )
            
            flash('配置创建成功', 'success')
            return redirect(url_for('admin.config_list'))
        except Exception as e:
            flash(f'创建配置时出错: {str(e)}', 'error')
    
    return render_template('admin/config_create.html')

@admin_bp.route('/configs/delete/<int:config_id>', methods=['POST'])
def delete_config(config_id):
    """Delete a configuration"""
    try:
        config = SystemConfig.query.get_or_404(config_id)
        from models import db
        db.session.delete(config)
        db.session.commit()
        flash('配置删除成功', 'success')
    except Exception as e:
        flash(f'删除配置时出错: {str(e)}', 'error')
    
    return redirect(url_for('admin.config_list'))

@admin_bp.route('/api/configs')
def api_configs():
    """API endpoint to get all configurations"""
    configs = system_config_service.get_all_configs()
    return jsonify([config.to_dict() for config in configs])

@admin_bp.route('/api/configs/<key>')
def api_get_config(key):
    """API endpoint to get a specific configuration"""
    config = SystemConfig.query.filter_by(key=key).first()
    if config:
        return jsonify(config.to_dict())
    return jsonify({'error': 'Configuration not found'}), 404

@admin_bp.route('/api/configs/<key>', methods=['PUT'])
def api_update_config(key):
    """API endpoint to update a configuration"""
    try:
        data = request.get_json()
        config = SystemConfig.query.filter_by(key=key).first()
        
        if not config:
            # Create new config if not exists
            config = SystemConfig(key=key)
            from models import db
            db.session.add(config)
        
        config.value = data.get('value', config.value)
        config.description = data.get('description', config.description)
        config.category = data.get('category', config.category)
        config.is_encrypted = data.get('is_encrypted', config.is_encrypted)
        
        from models import db
        db.session.commit()
        
        return jsonify(config.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500