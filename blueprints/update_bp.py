"""
Update Blueprint - Handles application update routes
"""
from flask import Blueprint, request, jsonify, current_app
from services import update_service
from utils.auth import require_daily_stats_password

update_bp = Blueprint('update', __name__, url_prefix='/update')

@update_bp.route('/status')
def api_update_status():
    """Get application update status"""
    try:
        status = update_service.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@update_bp.route('/check', methods=['POST'])
@require_daily_stats_password
def api_check_for_updates():
    """Manually check for application updates"""
    try:
        result = update_service.check_for_updates()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@update_bp.route('/acknowledge', methods=['POST'])
def api_acknowledge_update():
    """Acknowledge update notification"""
    try:
        result = update_service.acknowledge_notification()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@update_bp.route('/execute', methods=['POST'])
@require_daily_stats_password
def api_execute_update():
    """Execute application update"""
    try:
        data = request.get_json()
        force = data.get('force', False) if data else False
        source = data.get('source', 'github') if data else 'github'  # 默认使用GitHub源
        target_version = data.get('target_version') if data else None  # 允许指定目标版本
        
        # 如果提供了目标版本，则使用目标版本更新
        if target_version:
            result = update_service.trigger_update(target_version=target_version, force_reinstall=force, source=source)
        else:
            result = update_service.execute_update(force=force)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@update_bp.route('/execute/<source>/<target_version>', methods=['POST'])
@require_daily_stats_password
def api_execute_update_from_source(source, target_version):
    """Execute application update from specific source and version"""
    try:
        data = request.get_json()
        force = data.get('force', False) if data else False
        
        result = update_service.trigger_update(target_version=target_version, force_reinstall=force, source=source)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@update_bp.route('/logs')
def api_update_logs():
    """Get update logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        logs = update_service.get_logs(page=page, per_page=per_page)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@update_bp.route('/logs/<int:log_id>')
def api_update_log_details(log_id):
    """Get detailed update log"""
    try:
        log_details = update_service.get_log_details(log_id)
        return jsonify(log_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500