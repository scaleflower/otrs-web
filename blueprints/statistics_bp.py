"""
Statistics Blueprint - Handles statistical analysis routes
"""
from flask import Blueprint, render_template, request, jsonify
from services import analysis_service
from utils import validate_age_segment, validate_responsible_list, validate_json_data
from models import OtrsTicket, ResponsibleConfig, db
from utils import get_user_info
from datetime import datetime

statistics_bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@statistics_bp.route('/database')
def database_page():
    """Database statistics page"""
    return render_template('database_stats.html')

@statistics_bp.route('/database/api')
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

@statistics_bp.route('/responsible')
def responsible_stats():
    """Responsible statistics page"""
    return render_template('responsible_stats.html')

@statistics_bp.route('/responsible/api/list')
def api_responsible_list():
    """Get list of all responsible persons"""
    try:
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

@statistics_bp.route('/responsible/api/stats', methods=['POST'])
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

@statistics_bp.route('/responsible/api/details', methods=['POST'])
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
        
        from datetime import timedelta
        
        # Build base query for the responsible person
        base_query = OtrsTicket.query.filter(OtrsTicket.responsible == responsible)
        closed_tickets_query = base_query.filter(OtrsTicket.closed_date.isnot(None))
        
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
            # Period-based filtering (for total/day/week/month statistics)
            if period == 'total':
                tickets = closed_tickets_query.order_by(OtrsTicket.closed_date.desc()).limit(200).all()
            elif period == 'day':
                # Filter by specific date
                try:
                    target_date = datetime.strptime(time_value, '%Y-%m-%d').date()
                    start_datetime = datetime.combine(target_date, datetime.min.time())
                    end_datetime = start_datetime + timedelta(days=1)
                    
                    tickets = closed_tickets_query.filter(
                        OtrsTicket.closed_date >= start_datetime,
                        OtrsTicket.closed_date < end_datetime
                    ).order_by(OtrsTicket.closed_date.desc()).all()
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
                    
                    tickets = closed_tickets_query.filter(
                        OtrsTicket.closed_date >= week_start,
                        OtrsTicket.closed_date < week_end
                    ).order_by(OtrsTicket.closed_date.desc()).all()
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
                    
                    tickets = closed_tickets_query.filter(
                        OtrsTicket.closed_date >= month_start,
                        OtrsTicket.closed_date < month_end
                    ).order_by(OtrsTicket.closed_date.desc()).all()
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

@statistics_bp.route('/age-details', methods=['POST'])
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
        tickets = analysis_service.get_tickets_by_age_segment(age_segment)
        
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
        analysis_service.log_statistic_query('age_details', age_segment=age_segment, record_count=len(details))
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistics_bp.route('/empty-firstresponse-details', methods=['POST'])
def get_empty_firstresponse_details():
    """Get empty first response details directly from database"""
    try:
        # Get details using ticket service
        tickets = analysis_service.get_empty_firstresponse_tickets()
        
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