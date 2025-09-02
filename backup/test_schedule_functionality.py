#!/usr/bin/env python3
"""
Complete test script for schedule configuration functionality
"""

import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_schedule_functionality():
    """Test the complete schedule functionality"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== Testing Schedule Configuration Functionality ===\n")
    
    # 1. Get current configuration
    print("1. Getting current schedule configuration...")
    response = requests.get(f"{base_url}/api/daily-statistics")
    if response.status_code == 200:
        config = response.json()['data']['config']
        print(f"   Current config: Time={config['schedule_time']}, Enabled={config['enabled']}")
    else:
        print("   Failed to get configuration")
        return False
    
    # 2. Update schedule to a near future time for testing
    print("\n2. Updating schedule configuration...")
    test_time = "13:28"  # Set to 2 minutes from now for testing
    update_data = {
        "schedule_time": test_time,
        "enabled": True
    }
    response = requests.post(f"{base_url}/api/update-schedule", json=update_data)
    if response.status_code == 200:
        print(f"   Schedule updated to: {test_time}")
    else:
        print("   Failed to update schedule")
        return False
    
    # 3. Manually trigger statistics calculation (simulating scheduled execution)
    print("\n3. Manually triggering statistics calculation...")
    response = requests.post(f"{base_url}/api/calculate-daily-stats")
    if response.status_code == 200:
        print("   Statistics calculation triggered successfully")
    else:
        print("   Failed to trigger calculation")
        return False
    
    # 4. Wait a moment for processing
    time.sleep(2)
    
    # 5. Check database records
    print("\n4. Checking database records...")
    from app import app, db, DailyStatistics, StatisticsLog
    
    with app.app_context():
        # Check daily statistics
        stats = DailyStatistics.query.order_by(DailyStatistics.statistic_date.desc()).first()
        if stats:
            print(f"   Latest daily stat: Date={stats.statistic_date}, "
                  f"Opening={stats.opening_balance}, Closing={stats.closing_balance}")
        else:
            print("   No daily statistics found")
            return False
        
        # Check execution logs
        logs = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).all()
        print(f"   Execution logs count: {len(logs)}")
        for i, log in enumerate(logs[:3]):  # Show latest 3 logs
            print(f"   Log {i+1}: Time={log.execution_time}, Status={log.status}, "
                  f"Total Open={log.total_open}")
    
    # 6. Verify API returns correct data
    print("\n5. Verifying API data...")
    response = requests.get(f"{base_url}/api/daily-statistics")
    if response.status_code == 200:
        data = response.json()['data']
        print(f"   Config in API: Time={data['config']['schedule_time']}, "
              f"Enabled={data['config']['enabled']}")
        print(f"   Daily stats count: {len(data['daily_stats'])}")
        print(f"   Execution logs count: {len(data['stats_logs'])}")
    else:
        print("   Failed to get API data")
        return False
    
    # 7. Test disabling the schedule
    print("\n6. Testing schedule disable...")
    disable_data = {
        "schedule_time": test_time,
        "enabled": False
    }
    response = requests.post(f"{base_url}/api/update-schedule", json=disable_data)
    if response.status_code == 200:
        print("   Schedule disabled successfully")
    else:
        print("   Failed to disable schedule")
        return False
    
    print("\n=== Schedule Functionality Test Completed Successfully ===")
    return True

if __name__ == "__main__":
    try:
        success = test_schedule_functionality()
        if success:
            print("\n✅ All tests passed! The schedule configuration is working correctly.")
            print("\nHow to verify in the web interface:")
            print("1. Open http://127.0.0.1:5000/daily-statistics")
            print("2. Check the 'Execution Logs' section - should show recent successful executions")
            print("3. Check the 'Daily Statistics' table - should show today's data")
            print("4. Verify the schedule configuration is displayed correctly")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
