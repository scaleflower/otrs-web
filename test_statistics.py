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
    
    # Test empty first response details
    print("Testing empty first response details...")
    try:
        response = requests.post(f"{base_url}/empty-firstresponse-details")
        if response.status_code == 200:
            print("✓ Empty first response details test passed")
        else:
            print(f"✗ Empty first response details test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Empty first response details test error: {e}")
    
    # Test age details (24h segment)
    print("Testing age details (24h segment)...")
    try:
        data = {"age_segment": "24h"}
        response = requests.post(f"{base_url}/age-details", json=data)
        if response.status_code == 200:
            print("✓ Age details test passed")
        else:
            print(f"✗ Age details test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Age details test error: {e}")
    
    # Test export functionality (mock data)
    print("Testing export functionality...")
    try:
        # Create mock stats data for export test
        mock_stats = {
            "current_open_count": 0,
            "empty_firstresponse_count": 0,
            "daily_new": {},
            "daily_closed": {},
            "priority_distribution": {},
            "state_distribution": {},
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
    
    print("All tests completed!")

if __name__ == '__main__':
    test_statistics()
