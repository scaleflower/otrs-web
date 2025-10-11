"""
Export Blueprint - Handles data export routes
"""
from flask import Blueprint, request, send_file, jsonify
from services import export_service
from utils import validate_json_data

export_bp = Blueprint('export', __name__, url_prefix='/export')

@export_bp.route('/excel', methods=['POST'])
def export_excel():
    """Export analysis results to Excel with histogram"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Export using export service
        output, filename = export_service.export_to_excel(data)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/txt', methods=['POST'])
def export_txt():
    """Export analysis results to text file"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Export using export service
        output, filename = export_service.export_to_text(data)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/responsible-excel', methods=['POST'])
def api_export_responsible_excel():
    """Export responsible statistics to Excel"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['stats'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        stats = data['stats']
        
        # Export using export service
        output, filename = export_service.export_responsible_stats_to_excel(stats)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500