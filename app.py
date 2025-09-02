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
    from models import UploadDetail
    upload_sessions = UploadDetail.query.order_by(UploadDetail.upload_time.desc()).all()
    return render_template('uploads.html', upload_sessions=upload_sessions)

@app.route('/upload/<filename>')
def view_upload_details(filename):
    """View details of a specific upload file"""
    from models import OtrsTicket, UploadDetail
    
    # Find the upload session for this filename
    upload_session = UploadDetail.query.filter_by(filename=filename).first()
    
    if not upload_session:
        # If no UploadDetail record found, create a mock one for backward compatibility
        upload_session = type('MockSession', (), {
            'filename': filename,
            'upload_time': None,
            'record_count': 0,
            'import_mode': 'Unknown'
        })()
    
    # Get tickets for this filename
    tickets = OtrsTicket.query.filter_by(data_source=filename).all()
    
    return render_template('upload_details.html', upload_session=upload_session, tickets=tickets)

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
        
        # Get period parameter (default to 'total')
        period = data.get('period', 'total')
        
        # Get statistics using analysis service with period filtering
        stats = analysis_service.get_responsible_statistics(validated_responsibles, period)
        
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

@app.route('/api/responsible-details', methods=['POST'])
def api_responsible_details():
    """Get detailed ticket information for a responsible person"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['responsible', 'period', 'timeValue'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        responsible = data['responsible']
        period = data['period']
        time_value = data['timeValue']
        
        from models import OtrsTicket
        from datetime import datetime, timedelta
        
        # Build base query for the responsible person
        base_query = OtrsTicket.query.filter(OtrsTicket.responsible == responsible)
        
        if period == 'age':
            # Age-based filtering (for total statistics)
            open_tickets = base_query.filter(OtrsTicket.closed_date.is_(None)).all()
            
            # Filter by age segment
            tickets = []
            for ticket in open_tickets:
                if ticket.age_hours is not None:
                    if time_value == 'age_24h' and ticket.age_hours <= 24:
                        tickets.append(ticket)
                    elif time_value == 'age_24_48h' and 24 < ticket.age_hours <= 48:
                        tickets.append(ticket)
                    elif time_value == 'age_48_72h' and 48 < ticket.age_hours <= 72:
                        tickets.append(ticket)
                    elif time_value == 'age_72h' and ticket.age_hours > 72:
                        tickets.append(ticket)
        else:
            # Period-based filtering (for day/week/month statistics)
            if period == 'day':
                # Filter by specific date
                try:
                    target_date = datetime.strptime(time_value, '%Y-%m-%d').date()
                    start_datetime = datetime.combine(target_date, datetime.min.time())
                    end_datetime = start_datetime + timedelta(days=1)
                    
                    tickets = base_query.filter(
                        OtrsTicket.created_date >= start_datetime,
                        OtrsTicket.created_date < end_datetime
                    ).all()
                except ValueError:
                    return jsonify({'error': 'Invalid date format'}), 400
                    
            elif period == 'week':
                # Filter by specific week
                try:
                    # Parse week format like "2025-35" 
                    year, week_num = time_value.replace('第', '').replace('周', '').split('-')
                    year = int(year)
                    week_num = int(week_num)
                    
                    # Calculate week start and end dates
                    # This is a simplified approach - you might need more precise week calculation
                    jan_1 = datetime(year, 1, 1)
                    week_start = jan_1 + timedelta(weeks=week_num-1)
                    week_start = week_start - timedelta(days=week_start.weekday())  # Monday
                    week_end = week_start + timedelta(days=7)
                    
                    tickets = base_query.filter(
                        OtrsTicket.created_date >= week_start,
                        OtrsTicket.created_date < week_end
                    ).all()
                except (ValueError, IndexError):
                    return jsonify({'error': 'Invalid week format'}), 400
                    
            elif period == 'month':
                # Filter by specific month
                try:
                    # Parse month format like "2025-08"
                    year, month = time_value.split('-')
                    year = int(year)
                    month = int(month)
                    
                    month_start = datetime(year, month, 1)
                    if month == 12:
                        month_end = datetime(year + 1, 1, 1)
                    else:
                        month_end = datetime(year, month + 1, 1)
                    
                    tickets = base_query.filter(
                        OtrsTicket.created_date >= month_start,
                        OtrsTicket.created_date < month_end
                    ).all()
                except (ValueError, IndexError):
                    return jsonify({'error': 'Invalid month format'}), 400
            else:
                return jsonify({'error': 'Invalid period type'}), 400
        
        # Convert tickets to response format
        details = []
        for ticket in tickets:
            details.append({
                'ticket_number': ticket.ticket_number or 'N/A',
                'created': str(ticket.created_date) if ticket.created_date else 'N/A',
                'closed': str(ticket.closed_date) if ticket.closed_date else 'N/A',
                'state': ticket.state or 'N/A',
                'priority': ticket.priority or 'N/A',
                'title': ticket.title or 'N/A'
            })
        
        return jsonify({
            'success': True,
            'count': len(details),
            'details': details
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

@app.route('/api/export-responsible-excel', methods=['POST'])
def api_export_responsible_excel():
    """Export responsible statistics to Excel"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['period', 'selectedResponsibles', 'statsData', 'totalsData'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Extract export parameters
        period = data['period']
        selected_responsibles = data['selectedResponsibles']
        stats_data = data['statsData']
        totals_data = data['totalsData']
        export_type = data.get('exportType', 'summary')  # Default to summary
        
        # Export using export service
        output, filename = export_service.export_responsible_stats_to_excel(
            period, selected_responsibles, stats_data, totals_data, export_type
        )
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-responsible-txt', methods=['POST'])
def api_export_responsible_txt():
    """Export responsible statistics to text"""
    try:
        data = request.get_json()
        is_valid, error = validate_json_data(data, ['period', 'selectedResponsibles', 'statsData', 'totalsData'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Extract export parameters
        period = data['period']
        selected_responsibles = data['selectedResponsibles']
        stats_data = data['statsData']
        totals_data = data['totalsData']
        export_type = data.get('exportType', 'summary')  # Default to summary
        
        # Export using export service
        output, filename = export_service.export_responsible_stats_to_text(
            period, selected_responsibles, stats_data, totals_data, export_type
        )
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
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

@app.route('/api/latest-upload-info')
def api_latest_upload_info():
    """Get information about the most recent upload"""
    try:
        from models import OtrsTicket, UploadDetail, db
        
        # Get the latest upload from UploadDetail table
        latest_upload_detail = UploadDetail.query.order_by(UploadDetail.upload_time.desc()).first()
        
        if not latest_upload_detail:
            return jsonify({
                'success': True,
                'has_data': False,
                'message': '暂无上传记录'
            })
        
        # Get total count and open tickets count from OtrsTicket
        total_count = OtrsTicket.query.count()
        open_count = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).count()
        
        # Format upload time using server time (no timezone conversion)
        upload_time = latest_upload_detail.upload_time.strftime('%Y-%m-%d %H:%M:%S') if latest_upload_detail.upload_time else 'Unknown'
        
        return jsonify({
            'success': True,
            'has_data': True,
            'latest_upload': {
                'filename': latest_upload_detail.filename,
                'record_count': latest_upload_detail.record_count,
                'upload_time': upload_time,
                'total_records': total_count,
                'open_tickets': open_count
            }
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
