"""
Decorator utilities for OTRS Web Application
"""

import functools
import time
import logging
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def handle_errors(f):
    """
    Decorator to handle exceptions in route functions
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': '处理请求时发生错误'
                }), 500
            else:
                # For HTML requests, you might want to render an error template
                return f"处理请求时发生错误: {str(e)}", 500
    return decorated_function


def log_execution_time(f):
    """
    Decorator to log execution time of functions
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Function {f.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {f.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    return decorated_function


def validate_request(required_params=None, required_files=None):
    """
    Decorator to validate request parameters and files
    
    Args:
        required_params: List of required request parameters
        required_files: List of required files in request
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Validate required parameters
            if required_params:
                missing_params = []
                for param in required_params:
                    if param not in request.form and param not in request.args and param not in request.json:
                        missing_params.append(param)
                
                if missing_params:
                    error_msg = f"Missing required parameters: {', '.join(missing_params)}"
                    logger.warning(f"Request validation failed: {error_msg}")
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': error_msg,
                            'message': '请求参数不完整'
                        }), 400
                    else:
                        return error_msg, 400
            
            # Validate required files
            if required_files:
                missing_files = []
                for file_key in required_files:
                    if file_key not in request.files or not request.files[file_key].filename:
                        missing_files.append(file_key)
                
                if missing_files:
                    error_msg = f"Missing required files: {', '.join(missing_files)}"
                    logger.warning(f"Request validation failed: {error_msg}")
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': error_msg,
                            'message': '请求文件不完整'
                        }), 400
                    else:
                        return error_msg, 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_json(f):
    """
    Decorator to ensure request contains JSON data
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must contain JSON data',
                'message': '请求必须包含JSON数据'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def cache_result(duration=300):
    """
    Decorator to cache function results for a specified duration
    
    Args:
        duration: Cache duration in seconds (default: 5 minutes)
    """
    def decorator(f):
        cache = {}
        cache_time = {}
        
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if cache_key in cache and cache_key in cache_time:
                if current_time - cache_time[cache_key] < duration:
                    logger.debug(f"Returning cached result for {f.__name__}")
                    return cache[cache_key]
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = result
            cache_time[cache_key] = current_time
            
            # Clean up old cache entries (simple cleanup)
            keys_to_remove = []
            for key, timestamp in cache_time.items():
                if current_time - timestamp >= duration:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                cache.pop(key, None)
                cache_time.pop(key, None)
            
            return result
        return decorated_function
    return decorator
