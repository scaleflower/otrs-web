"""
Helper utilities for common operations
"""

import os
from datetime import datetime
from flask import request

# Global variable to store processing progress
processing_status = {
    'current_step': 0,
    'total_steps': 7,
    'message': '',
    'details': ''
}

def update_processing_status(step, message, details=''):
    """Update processing status with optimized logging"""
    global processing_status
    processing_status['current_step'] = step
    processing_status['message'] = message
    processing_status['details'] = details
    
    # Only print key milestones to reduce console noise
    # Print only step changes and important messages
    if (step != processing_status.get('last_printed_step', 0) or 
        'completed' in message.lower() or 
        'error' in message.lower() or
        'import' in message.lower()):
        print(f"Step {step}/{processing_status['total_steps']}: {message}")
        processing_status['last_printed_step'] = step

def get_processing_status():
    """Get current processing status"""
    return processing_status.copy()

def get_user_info():
    """Get user information from request"""
    if not request:
        return 'unknown', 'unknown'
    
    user_ip = request.remote_addr if request.remote_addr else 'unknown'
    user_agent = request.headers.get('User-Agent', 'unknown')[:100]
    
    return user_ip, user_agent

def generate_filename(prefix, extension, include_timestamp=True):
    """Generate filename with optional timestamp"""
    if include_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{extension}"
    return f"{prefix}.{extension}"

def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if not"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        print(f"✓ Created directory: {directory_path}")
    return directory_path

def safe_dict_get(dictionary, key, default=None):
    """Safely get value from dictionary"""
    if not isinstance(dictionary, dict):
        return default
    return dictionary.get(key, default)

def calculate_percentage(part, total):
    """Calculate percentage with safe division"""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)

def batch_process(items, batch_size=100):
    """Process items in batches"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def get_file_extension(filename):
    """Get file extension from filename"""
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()

def is_valid_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized

def get_memory_usage():
    """Get current memory usage (if psutil is available)"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent()
        }
    except ImportError:
        return None

def format_timedelta(td):
    """Format timedelta to human readable string"""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
