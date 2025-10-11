#!/usr/bin/env python3
"""
Test script to diagnose scheduler execution issue
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from services import scheduler_service
from models import StatisticsConfig, StatisticsLog, db

def test_scheduler_status():
    """Test current scheduler status"""
    print("=== Scheduler Status Test ===")
    
    with app.app_context():
        # Check if scheduler is running
        status = scheduler_service.get_scheduler_status()
        print(f"Scheduler running: {status.get('running', False)}")
        print(f"Job count: {status.get('job_count', 0)}")
        print(f"Jobs: {status.get('jobs', [])}")
        
        if 'error' in status:
            print(f"Scheduler error: {status['error']}")
        
        # Check current configuration
        config = StatisticsConfig.query.first()
        if config:
            print(f"Schedule time: {config.schedule_time}")
            print(f"Enabled: {config.enabled}")
            print(f"Updated at: {config.updated_at}")
        else:
            print("No statistics configuration found in database")
        
        # Check recent execution logs
        recent_logs = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).limit(5).all()
        print(f"\nRecent execution logs ({len(recent_logs)} found):")
        for log in recent_logs:
            print(f"  {log.execution_time} - {log.status} - Total Open: {log.total_open}")
            if log.error_message:
                print(f"    Error: {log.error_message}")

def test_manual_trigger():
    """Test manual trigger functionality"""
    print("\n=== Manual Trigger Test ===")
    
    with app.app_context():
        print("Triggering manual calculation...")
        success, message = scheduler_service.trigger_manual_calculation()
        print(f"Result: {success} - {message}")
        
        # Check if a new log was created
        latest_log = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).first()
        if latest_log:
            print(f"Latest log: {latest_log.execution_time} - {latest_log.status}")

def test_schedule_update():
    """Test schedule update functionality"""
    print("\n=== Schedule Update Test ===")
    
    with app.app_context():
        # Set schedule to next minute
        next_minute = datetime.now() + timedelta(minutes=1)
        schedule_time = next_minute.strftime('%H:%M')
        
        print(f"Setting schedule time to: {schedule_time}")
        success, message = scheduler_service.update_schedule(schedule_time, True)
        print(f"Update result: {success} - {message}")
        
        # Check if the job was scheduled correctly
        status = scheduler_service.get_scheduler_status()
        print(f"Updated scheduler status:")
        print(f"  Running: {status.get('running', False)}")
        print(f"  Jobs: {status.get('jobs', [])}")

if __name__ == '__main__':
    print("Testing scheduler functionality...")
    print(f"Current time: {datetime.now()}")
    
    test_scheduler_status()
    test_manual_trigger()
    test_schedule_update()
    
    print("\n=== Test completed ===")
