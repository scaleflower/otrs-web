"""
Backup Blueprint - Handles database backup routes
"""
from flask import Blueprint, request, send_file, jsonify
from services import scheduler_service
import os

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/status')
def api_backup_status():
    """Get backup service status and statistics"""
    try:
        status = scheduler_service.get_backup_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/list')
def api_backup_list():
    """Get list of all available backups"""
    try:
        if not scheduler_service.backup_service:
            return jsonify({'error': 'Backup service not available'}), 500
        
        backups = scheduler_service.backup_service.list_backups()
        
        # Format backup data for API response
        formatted_backups = []
        for backup in backups:
            formatted_backups.append({
                'filename': backup['filename'],
                'size_mb': backup['size_mb'],
                'created_date': backup['created_date'].isoformat(),
                'age_days': backup['age_days'],
                'compressed': backup['compressed']
            })
        
        return jsonify({
            'success': True,
            'backups': formatted_backups
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/verify', methods=['POST'])
def api_verify_backup():
    """Verify backup file integrity"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': 'Backup filename required'}), 400
        
        filename = data['filename']
        success, message = scheduler_service.verify_backup(filename)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'error': message}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/cleanup', methods=['POST'])
def api_cleanup_backups():
    """Clean up old backup files"""
    try:
        data = request.get_json()
        retention_days = data.get('retention_days') if data else None
        
        success, message, deleted_count = scheduler_service.cleanup_old_backups(retention_days)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'deleted_count': deleted_count
            })
        else:
            return jsonify({'error': message}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/restore', methods=['POST'])
def api_restore_backup():
    """Restore database from backup"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': 'Backup filename required'}), 400
        
        filename = data['filename']
        
        if not scheduler_service.backup_service:
            return jsonify({'error': 'Backup service not available'}), 500
        
        success, message = scheduler_service.backup_service.restore_backup(filename)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'warning': 'Application restart recommended after database restore'
            })
        else:
            return jsonify({'error': message}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/download/<filename>')
def api_download_backup(filename):
    """Download a backup file"""
    try:
        if not scheduler_service.backup_service:
            return jsonify({'error': 'Backup service not available'}), 500
        
        backup_path = os.path.join(scheduler_service.backup_service.backup_folder, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500