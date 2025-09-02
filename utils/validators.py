"""
Data validation utilities
"""

import os
from flask import current_app

def validate_file(file):
    """Validate uploaded file"""
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    # Check file extension
    if not allowed_file(file.filename):
        return False, "Invalid file format. Please upload Excel file (.xlsx or .xls)"
    
    # Check file size
    if hasattr(file, 'content_length') and file.content_length:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        if file.content_length > max_size:
            return False, f"File too large. Maximum size is {max_size // (1024*1024)}MB"
    
    return True, None

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'xlsx', 'xls'})
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_excel_columns(df):
    """Validate Excel file has required columns"""
    if df is None or df.empty:
        return False, "Excel file is empty"
    
    # Define possible column name mappings
    required_columns = {
        'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id', 'Ticket', 'Ticket ID'],
        'state': ['State', 'Status', 'Ticket State', 'state', 'status', 'Ticket Status'],
    }
    
    found_columns = {}
    for key, possible_names in required_columns.items():
        for col in df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                found_columns[key] = col
                break
    
    # Check if at least one core column is found
    if not found_columns:
        return False, "No recognizable ticket columns found in Excel file"
    
    return True, found_columns

def validate_age_segment(age_segment):
    """Validate age segment parameter"""
    valid_segments = ['24h', '24_48h', '48_72h', '72h']
    if age_segment not in valid_segments:
        return False, f"Invalid age segment. Must be one of: {', '.join(valid_segments)}"
    return True, None

def validate_responsible_list(responsibles):
    """Validate responsible persons list"""
    if not responsibles:
        return False, "No responsible persons provided"
    
    if not isinstance(responsibles, list):
        return False, "Responsible persons must be a list"
    
    if len(responsibles) == 0:
        return False, "Responsible persons list cannot be empty"
    
    # Check for empty strings
    valid_responsibles = [r for r in responsibles if r and r.strip()]
    if len(valid_responsibles) == 0:
        return False, "No valid responsible persons found"
    
    return True, valid_responsibles

def validate_date_range(start_date, end_date):
    """Validate date range parameters"""
    from datetime import datetime
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                return False, "Start date cannot be after end date"
                
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"
    
    return True, None

def validate_schedule_time(schedule_time):
    """Validate schedule time format"""
    if not schedule_time:
        return False, "Schedule time is required"
    
    try:
        hour, minute = map(int, schedule_time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return False, "Invalid time. Hour must be 0-23 and minute must be 0-59"
    except ValueError:
        return False, "Invalid time format. Use HH:MM format"
    
    return True, None

def validate_json_data(data, required_fields=None):
    """Validate JSON request data"""
    if not data:
        return False, "No data provided"
    
    if required_fields:
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None
