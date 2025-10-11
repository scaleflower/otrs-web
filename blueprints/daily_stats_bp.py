"""
Daily Statistics Blueprint - Handles daily statistics routes
"""
from flask import Blueprint, render_template, request, jsonify
from services import scheduler_service, analysis_service
from utils.auth import require_daily_stats_password
from utils import validate_json_data, validate_schedule_time

daily_stats_bp = Blueprint('daily_stats', __name__, url_prefix='/daily-statistics')

@daily_stats_bp.route('/')
def daily_statistics_page():
    """Daily statistics page"""
    return render_template('daily_statistics.html')

@daily_stats_bp.route('/api/data')
def api_daily_statistics():
    """Get daily statistics data"""
    try:
        result = analysis_service.get_daily_statistics_data()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@daily_stats_bp.route('/api/schedule', methods=['POST'])
@require_daily_stats_password
def api_update_schedule():
    """Update statistics schedule configuration"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['schedule_time'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        schedule_time = data['schedule_time']
        enabled = data.get('enabled', True)
        
        is_valid, error = validate_schedule_time(schedule_time)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Update schedule using scheduler service
        success, message = scheduler_service.update_schedule(schedule_time, enabled)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'error': message}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@daily_stats_bp.route('/api/calculate', methods=['POST'])
@require_daily_stats_password
def api_calculate_daily_stats():
    """Manually trigger daily statistics calculation"""
    try:
        success, message = scheduler_service.trigger_manual_calculation()
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'error': message}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500