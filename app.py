"""
OTRS Ticket Analysis Web Application - Refactored
Flask-based ticket data analysis web application with modular architecture
"""

from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
from config import Config
from models import init_db
from services import init_services, ticket_service, analysis_service, export_service, scheduler_service
from utils import get_processing_status, validate_age_segment, validate_responsible_list, validate_json_data

# Create Flask application
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Initialize database
init_db(app)

# Initialize services
init_services(app)

# Application version from config
APP_VERSION = app.config.get('APP_VERSION', '1.2.2')

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', APP_VERSION=APP_VERSION)

@app.route('/uploads')
def view_uploads():
    """View all uploaded data sources"""
    from models import OtrsTicket, db
    data_sources = OtrsTicket.query.with_entities(
        OtrsTicket.data_source, 
        db.func.count(OtrsTicket.id)
    ).group_by(OtrsTicket.data_source).all()
    return render_template('uploads.html', data_sources=data_sources)

@app.route('/upload/<filename>')
def view_upload_details(filename):
    """View details of a specific upload file"""
    from models import OtrsTicket
    tickets = OtrsTicket.query.filter_by(data_source=filename).all()
    return render_template('upload_details.html', filename=filename, tickets=tickets)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get clear existing option from form data
        clear_existing = request.form.get('clear_existing', 'false').lower() == 'true'
        
        # Process upload using ticket service
        result = ticket_service.process_upload(file, clear_existing)
        
        # Get analysis statistics
        stats = analysis_service.analyze_tickets_from_database()
        
        # Log the analysis
        analysis_service.log_statistic_query(
            'main_analysis',
            upload_id=result['upload_id'],
            record_count=result['total_records']
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'total_records': result['total_records'],
            'new_records_count': result['new_records_count'],
            'stats': stats,
            'filename': result['filename']
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/excel', methods=['POST'])
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

@app.route('/export/txt', methods=['POST'])
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

@app.route('/age-details', methods=['POST'])
def get_age_details():
    """Get age segment details directly from database"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['age_segment'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        age_segment = data['age_segment']
        is_valid, error = validate_age_segment(age_segment)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Get details using ticket service
        tickets = ticket_service.get_tickets_by_age_segment(age_segment)
        
        # Convert to response format
        details = []
        for ticket in tickets:
            details.append({
                'ticket_number': ticket.ticket_number or 'N/A',
                'age': ticket.age or 'N/A',
                'created': str(ticket.created_date) if ticket.created_date else 'N/A',
                'priority': ticket.priority or 'N/A'
            })
        
        # Log query
        analysis_service.log_statistic_query('age_details', age_segment=age_segment, record_count=len(details))
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/empty-firstresponse-details', methods=['POST'])
def get_empty_firstresponse_details():
    """Get empty first response details directly from database"""
    try:
        # Get details using ticket service
        tickets = ticket_service.get_empty_firstresponse_tickets()
        
        # Convert to response format
        details = []
        for ticket in tickets:
            details.append({
                'ticket_number': ticket.ticket_number or 'N/A',
                'age': ticket.age or 'N/A',
                'created': str(ticket.created_date) if ticket.created_date else 'N/A',
                'priority': ticket.priority or 'N/A',
                'state': ticket.state or 'N/A'
            })
        
        # Log query
        analysis_service.log_statistic_query('empty_firstresponse', record_count=len(details))
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/database-stats')
def database_stats():
    """Get comprehensive statistics directly from database"""
    try:
        result = analysis_service.get_database_overview()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/database')
def database_page():
    """Database statistics page"""
    return render_template('database_stats.html', APP_VERSION=APP_VERSION)

@app.route('/responsible-stats')
def responsible_stats():
    """Responsible statistics page"""
    return render_template('responsible_stats.html', APP_VERSION=APP_VERSION)

@app.route('/api/responsible-stats', methods=['POST'])
def api_responsible_stats():
    """API endpoint for responsible statistics"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['selected_responsibles'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        selected_responsibles = data['selected_responsibles']
        is_valid, validated_responsibles = validate_responsible_list(selected_responsibles)
        if not is_valid:
            return jsonify({'error': validated_responsibles}), 400
        
        # Get statistics using analysis service
        stats = analysis_service.get_responsible_statistics(validated_responsibles)
        
        # Save user selection using models
        from models import ResponsibleConfig, db
        from utils import get_user_info
        
        user_ip, _ = get_user_info()
        existing_config = ResponsibleConfig.query.filter_by(user_identifier=user_ip).first()
        
        if existing_config:
            existing_config.selected_responsibles = str(validated_responsibles)
            existing_config.updated_at = datetime.utcnow()
        else:
            new_config = ResponsibleConfig(
                user_identifier=user_ip,
                selected_responsibles=str(validated_responsibles)
            )
            db.session.add(new_config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/responsible-list')
def api_responsible_list():
    """Get list of all responsible persons"""
    try:
        from models import OtrsTicket, ResponsibleConfig
        from utils import get_user_info
        
        # Get all responsible persons
        responsibles = OtrsTicket.query.with_entities(OtrsTicket.responsible).filter(
            OtrsTicket.responsible.isnot(None),
            OtrsTicket.responsible != ''
        ).distinct().order_by(OtrsTicket.responsible).all()
        
        responsible_list = [record.responsible for record in responsibles if record.responsible]
        
        # Get user's previous selection
        user_ip, _ = get_user_info()
        user_config = ResponsibleConfig.query.filter_by(user_identifier=user_ip).first()
        selected_responsibles = []
        
        if user_config and user_config.selected_responsibles:
            try:
                selected_responsibles = eval(user_config.selected_responsibles)
            except:
                selected_responsibles = []
        
        return jsonify({
            'success': True,
            'responsibles': responsible_list,
            'selected_responsibles': selected_responsibles
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daily-statistics')
def daily_statistics_page():
    """Daily statistics page"""
    return render_template('daily_statistics.html', APP_VERSION=APP_VERSION)

@app.route('/api/daily-statistics')
def api_daily_statistics():
    """Get daily statistics data"""
    try:
        result = analysis_service.get_daily_statistics_data()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-schedule', methods=['POST'])
def api_update_schedule():
    """Update statistics schedule configuration"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['schedule_time'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        schedule_time = data['schedule_time']
        enabled = data.get('enabled', True)
        
        from utils import validate_schedule_time
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

@app.route('/api/calculate-daily-stats', methods=['POST'])
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

@app.route('/api/export-execution-logs', methods=['GET'])
def api_export_execution_logs():
    """Export all execution logs to Excel"""
    try:
        output, filename = export_service.export_execution_logs()
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-database', methods=['POST'])
def clear_database():
    """Clear all ticket data from database"""
    try:
        records_cleared, message = ticket_service.clear_all_tickets()
        
        return jsonify({
            'success': True,
            'message': message,
            'records_cleared': records_cleared
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/processing-status')
def get_processing_status_route():
    """Get current processing status"""
    return jsonify(get_processing_status())

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

if __name__ == '__main__':
    # Initialize configuration
    Config.init_app(app)
    
    # Run application
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=5000
    )
