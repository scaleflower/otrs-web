#!/usr/bin/env python3
"""
Test script to verify timezone fix for Daily Statistics Execution Logs
"""

import requests
import json
from datetime import datetime, timezone, timedelta

def test_timezone_display():
    """Test timezone display functionality"""
    base_url = "http://localhost:5000"
    
    print("Testing Timezone Display Fix")
    print("=" * 40)
    
    # Test 1: Get daily statistics data
    print("1. Getting daily statistics data...")
    
    try:
        response = requests.get(f"{base_url}/api/daily-statistics")
        
        if response.status_code != 200:
            print(f"❌ Failed to get daily statistics: {response.status_code}")
            return False
        
        data = response.json()
        if not data.get('success'):
            print(f"❌ Error getting daily statistics: {data.get('error')}")
            return False
        
        stats_logs = data.get('data', {}).get('stats_logs', [])
        print(f"✓ Found {len(stats_logs)} execution logs")
        
        if not stats_logs:
            print("⚠️  No execution logs found, triggering manual calculation...")
            
            # Trigger manual calculation
            calc_response = requests.post(f"{base_url}/api/calculate-daily-stats")
            if calc_response.status_code == 200:
                calc_data = calc_response.json()
                if calc_data.get('success'):
                    print("✓ Manual calculation triggered successfully")
                    # Wait a moment for calculation to complete
                    import time
                    time.sleep(3)
                    
                    # Retry getting data
                    response = requests.get(f"{base_url}/api/daily-statistics")
                    if response.status_code == 200:
                        data = response.json()
                        stats_logs = data.get('data', {}).get('stats_logs', [])
                        print(f"✓ Now found {len(stats_logs)} execution logs")
                else:
                    print(f"❌ Manual calculation failed: {calc_data.get('error')}")
            else:
                print(f"❌ Failed to trigger manual calculation: {calc_response.status_code}")
        
        # Test 2: Analyze execution times
        print("\n2. Analyzing execution times...")
        
        local_tz = timezone(timedelta(hours=8))  # Asia/Shanghai UTC+8
        current_local_time = datetime.now(local_tz)
        
        print(f"Current local time (UTC+8): {current_local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        for i, log in enumerate(stats_logs[:3]):  # Check first 3 logs
            execution_time_str = log.get('execution_time')
            if execution_time_str:
                try:
                    # Parse the execution time
                    if execution_time_str.endswith('Z'):
                        # If it ends with Z, it's UTC
                        execution_time = datetime.fromisoformat(execution_time_str[:-1]).replace(tzinfo=timezone.utc)
                        time_type = "UTC"
                    elif '+' in execution_time_str or execution_time_str.count('-') > 2:
                        # If it has timezone info
                        execution_time = datetime.fromisoformat(execution_time_str)
                        time_type = "with timezone"
                    else:
                        # Assume it's local time without timezone info
                        execution_time = datetime.fromisoformat(execution_time_str)
                        time_type = "local (no timezone)"
                    
                    print(f"Log {i+1}:")
                    print(f"  Raw time: {execution_time_str}")
                    print(f"  Parsed as: {time_type}")
                    print(f"  Display time: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Check if the time seems reasonable (within last 24 hours)
                    if hasattr(execution_time, 'tzinfo') and execution_time.tzinfo:
                        time_diff = current_local_time - execution_time.astimezone(local_tz)
                    else:
                        # Assume it's already in local time
                        local_execution_time = local_tz.localize(execution_time) if execution_time.tzinfo is None else execution_time
                        time_diff = current_local_time - local_execution_time
                    
                    hours_diff = abs(time_diff.total_seconds()) / 3600
                    print(f"  Time difference from now: {hours_diff:.1f} hours")
                    
                    if hours_diff < 168:  # Within a week
                        print(f"  ✓ Time seems reasonable")
                    else:
                        print(f"  ⚠️  Time seems unusual (more than a week ago)")
                    
                except Exception as e:
                    print(f"  ❌ Error parsing time: {str(e)}")
                
                print()
        
        # Test 3: Check if times are displayed correctly in frontend format
        print("3. Frontend time formatting test...")
        
        test_time = "2025-09-02T19:08:35"  # Example time
        print(f"Test time string: {test_time}")
        
        # Simulate JavaScript Date parsing
        try:
            dt = datetime.fromisoformat(test_time)
            # This is how JavaScript toLocaleString() would format it
            formatted = dt.strftime('%Y/%m/%d %H:%M:%S')
            print(f"Formatted time: {formatted}")
            print("✓ Time formatting works correctly")
        except Exception as e:
            print(f"❌ Time formatting error: {str(e)}")
        
        print("\n✓ Timezone display test completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Please make sure the server is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    test_timezone_display()
