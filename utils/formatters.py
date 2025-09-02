"""
Data formatting utilities
"""

import re
import pandas as pd
from datetime import datetime

def format_number(num):
    """Format numbers with commas for display"""
    if num is None:
        return "0"
    return f"{num:,}"

def parse_age_to_hours(age_str):
    """Parse Age string to total hours"""
    if pd.isna(age_str) or age_str is None:
        return 0
    
    age_str = str(age_str).lower()
    days = 0
    hours = 0
    minutes = 0
    
    # Extract days
    day_match = re.search(r'(\d+)\s*d', age_str)
    if day_match:
        days = int(day_match.group(1))
    
    # Extract hours
    hour_match = re.search(r'(\d+)\s*h', age_str)
    if hour_match:
        hours = int(hour_match.group(1))
    
    # Extract minutes
    minute_match = re.search(r'(\d+)\s*m', age_str)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    return (days * 24) + hours + (minutes / 60)

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string"""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    return str(dt)

def clean_string_value(value):
    """Clean string value for database storage"""
    if pd.isna(value) or value is None:
        return None
    
    value = str(value).strip()
    
    # Handle common null representations
    if value.lower() in ['nan', 'none', 'null', '', 'n/a']:
        return None
    
    return value

def safe_int_conversion(value, default=0):
    """Safely convert value to integer"""
    try:
        if pd.isna(value) or value is None:
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float_conversion(value, default=0.0):
    """Safely convert value to float"""
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def truncate_text(text, max_length=50):
    """Truncate text to specified length"""
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
