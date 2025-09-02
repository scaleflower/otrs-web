#!/usr/bin/env python3
"""
Test script to verify direct database query functionality
"""

import requests
import json
import time

def test_direct_db_queries():
    """Test direct database query functionality"""
    base_url = "http://127.0.0.1:5000"
    
    print("Testing direct database query functionality...")
    
    # Test upload functionality
    print("\n1. Testing file upload and database storage...")
    try:
        # Create a test Excel file
        import pandas as pd
        test_data = {
            'Ticket Number': ['TICKET001', 'TICKET002', 'TICKET003'],
            'Created': ['2023-01-01 10:00:00', '2023-01-02 11:00:00', '2023-01-03 12:00:00'],
            'Closed': ['2023-01-05 15:00:00', None, None],
            'State': ['Closed', 'Open', 'Open'],
            'Priority': ['High', 'Normal', 'Low'],
            'FirstResponse': ['Response 1', '', 'Response 3'],
            'Age': ['1d 2h', '2d 5h', '3d 1h']
        }
        
        df = pd.DataFrame(test_data)
        df.to_excel('test_upload.xlsx', index=False)
        
        # Upload the test file
        files = {'file': open('test_upload.xlsx', 'rb')}
        data = {'clear_existing': 'true'}
        
        response = requests.post(f"{base_url}/upload", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            print("✓ File upload test passed")
            print(f"   Total records: {result.get('total_records', 0)}")
            print(f"   New records: {result.get('new_records_count', 0)}")
            print(f"   Current open: {result.get('stats', {}).get('current_open_count', 0)}")
        else:
            print(f"✗ File upload test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"✗ File upload test error: {e}")
    
    # Test empty first response details (direct from database)
    print("\n2. Testing empty first response details (direct from DB)...")
    try:
        response = requests.post(f"{base_url}/empty-firstresponse-details")
        if response.status_code == 200:
            data = response.json()
            print("✓ Empty first response details test passed")
            print(f"   Returned {len(data.get('details', []))} records")
        else:
            print(f"✗ Empty first response details test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Empty first response details test error: {e}")
    
    # Test age details (direct from database)
    print("\n3. Testing age details (direct from DB)...")
    try:
        data = {"age_segment": "24h"}
        response = requests.post(f"{base_url}/age-details", json=data)
        if response.status_code == 200:
            data = response.json()
            print("✓ Age details test passed")
            print(f"   Returned {len(data.get('details', []))} records")
        else:
            print(f"✗ Age details test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Age details test error: {e}")
    
    # Test database content
    print("\n4. Testing database content...")
    try:
        from app import db, OtrsTicket
        with db.app.app_context():
            total_tickets = OtrsTicket.query.count()
            open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).count()
            print(f"✓ Database contains {total_tickets} total tickets")
            print(f"✓ Database contains {open_tickets} open tickets")
    except Exception as e:
        print(f"✗ Database content test error: {e}")
    
    print("\nAll tests completed!")
    print("\nNow check the database to verify data was stored correctly:")
    print("Run: python database_manager.py check")

if __name__ == '__main__':
    test_direct_db_queries()
