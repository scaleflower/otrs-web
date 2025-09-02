#!/usr/bin/env python3
"""
Test script to verify scheduler fix
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from services import scheduler_service
from models import StatisticsConfig, StatisticsLog, db

def test_scheduler_fix():
    """Test that the scheduler fix works properly"""
    print("=== Testing Scheduler Fix ===")
    
    with app.app_context():
        # Get current log count
        initial_log_count = StatisticsLog.query.count()
        print(f"Initial log count: {initial_log_count}")
        
        # Set schedule to 1 minute from now
        next_minute = datetime.now() + timedelta(minutes=1)
        schedule_time = next_minute.strftime('%H:%M')
        
        print(f"Setting schedule time to: {schedule_time} (1 minute from now)")
        success, message = scheduler_service.update_schedule(schedule_time, True)
        print(f"Update result: {success} - {message}")
        
        # Verify the job is scheduled
        status = scheduler_service.get_scheduler_status()
        print(f"Scheduler running: {status.get('running', False)}")
        print(f"Next execution: {status.get('jobs', [{}])[0].get('next_run_time', 'None')}")
        
        print(f"Waiting for job to execute at {schedule_time}...")
        print("Please wait approximately 1 minute...")
        
        # Wait for about 70 seconds to ensure job execution
        time.sleep(70)
        
        # Check if new log was created
        final_log_count = StatisticsLog.query.count()
        print(f"Final log count: {final_log_count}")
        
        if final_log_count > initial_log_count:
            print("✓ SUCCESS: Scheduled job executed and created a log entry!")
            
            # Get the latest log
            latest_log = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).first()
            print(f"Latest log: {latest_log.execution_time} - {latest_log.status}")
            if latest_log.error_message:
                print(f"Error: {latest_log.error_message}")
            
            return True
        else:
            print("✗ FAILED: No new log entry created, scheduled job may not have executed")
            return False

def test_manual_vs_scheduled():
    """Compare manual trigger vs scheduled execution"""
    print("\n=== Manual vs Scheduled Comparison ===")
    
    with app.app_context():
        print("Testing manual trigger...")
        success, message = scheduler_service.trigger_manual_calculation()
        print(f"Manual trigger result: {success} - {message}")
        
        if success:
            print("✓ Manual trigger works correctly")
        else:
            print("✗ Manual trigger failed")

if __name__ == '__main__':
    print("Testing scheduler fix...")
    print(f"Current time: {datetime.now()}")
    
    # First test manual trigger to ensure basic functionality works
    test_manual_vs_scheduled()
    
    # Then test the scheduled execution
    scheduler_works = test_scheduler_fix()
    
    if scheduler_works:
        print("\n🎉 SCHEDULER FIX VERIFIED: Automatic execution is working!")
    else:
        print("\n❌ SCHEDULER ISSUE PERSISTS: Automatic execution still not working")
    
    print("\n=== Test completed ===")
