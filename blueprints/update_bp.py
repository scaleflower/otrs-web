"""
Update Blueprint - Handles application update routes
"""
from flask import Blueprint, request, jsonify, current_app, render_template
from services import update_service
from utils.auth import require_daily_stats_password

update_bp = Blueprint('update', __name__, url_prefix='/update')

@update_bp.route('/progress/<int:update_log_id>')
def update_progress(update_log_id):
    """Real-time update progress page"""
    return render_template('update_progress.html', update_log_id=update_log_id)

@update_bp.route('/api/progress/<int:update_log_id>')
def api_update_progress(update_log_id):
    """Get real-time update progress"""
    try:
        import json
        from pathlib import Path
        
        progress_dir = Path('db') / 'update_progress'
        progress_file = progress_dir / f"{update_log_id}.json"
        
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            return jsonify({'success': True, 'progress': progress_data})
        else:
            # 检查是否是开始事件
            start_file = progress_dir / f"{update_log_id}_start.json"
            if start_file.exists():
                with open(start_file, 'r', encoding='utf-8') as f:
                    start_data = json.load(f)
                return jsonify({'success': True, 'progress': start_data})
            else:
                return jsonify({'success': True, 'progress': None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
def execute_update():
    """Execute application update"""
    try:
        data = request.get_json() if request.is_json else request.form
        password = data.get('password')
        target_version = data.get('target_version')
        force_reinstall = data.get('force_reinstall', False)
        source = data.get('source', 'github')  # 支持指定更新源
        
        # 验证密码
        if not password:
            return jsonify({'error': 'Password required'}), 400
            
        from utils.auth import PasswordProtection
        if not PasswordProtection.verify_password(password):
            return jsonify({'error': 'Invalid password'}), 401

        # 触发更新
        result = update_service.trigger_update(
            target_version=target_version,
            force_reinstall=force_reinstall,
            source=source
        )
        
        if result['success']:
            # 重定向到进度页面而不是返回JSON
            from flask import redirect, url_for
            return redirect(url_for('update.update_progress', update_log_id=result['update_log_id']))
        else:
            return jsonify(result), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
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