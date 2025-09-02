#!/usr/bin/env python3
"""
Test script to verify statistics recording functionality
"""

import requests
import json
import time

def test_statistics():
    """Test statistics recording functionality"""
    base_url = "http://127.0.0.1:5000"
    
    print("Testing statistics recording functionality...")
    
    # Test empty first response details
    print("\n1. Testing empty first response details...")
    try:
        response = requests.post(f"{base_url}/empty-firstresponse-details")
        if response.status_code == 200:
            print("✓ Empty first response details test passed")
            data = response.json()
            print(f"   Returned {len(data.get('details', []))} records")
        else:
            print(f"✗ Empty first response details test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Empty first response details test error: {e}")
    
    # Test age details (24h segment)
    print("\n2. Testing age details (24h segment)...")
    try:
        data = {"age_segment": "24h"}
        response = requests.post(f"{base_url}/age-details", json=data)
        if response.status_code == 200:
            print("✓ Age details test passed")
            data = response.json()
            print(f"   Returned {len(data.get('details', []))} records")
        else:
            print(f"✗ Age details test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Age details test error: {e}")
    
    # Test export functionality (mock data)
    print("\n3. Testing export functionality...")
    try:
        # Create mock stats data for export test
        mock_stats = {
            "current_open_count": 0,
            "empty_firstresponse_count": 0,
            "daily_new": {"2023-01-01": 5, "2023-01-02": 3},
            "daily_closed": {"2023-01-01": 2, "2023-01-02": 4},
            "priority_distribution": {"High": 2, "Normal": 5},
            "state_distribution": {"Open": 3, "Closed": 4},
            "age_segments": {
                "age_24h": 0,
                "age_24_48h": 0,
                "age_48_72h": 0,
                "age_72h": 0
            }
        }
        data = {
            "stats": mock_stats,
            "total_records": 0
        }
        
        # Test Excel export
        response = requests.post(f"{base_url}/export/excel", json=data)
        if response.status_code == 200:
            print("✓ Excel export test passed")
        else:
            print(f"✗ Excel export test failed: {response.status_code}")
        
        # Test TXT export
        response = requests.post(f"{base_url}/export/txt", json=data)
        if response.status_code == 200:
            print("✓ TXT export test passed")
        else:
            print(f"✗ TXT export test failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Export test error: {e}")
    
    print("\nAll tests completed!")
    print("\nNow check the database to verify statistics were recorded:")
    print("Run: python database_manager.py check")

if __name__ == '__main__':
    test_statistics()
