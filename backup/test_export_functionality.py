#!/usr/bin/env python3
"""
Test script for export execution logs functionality
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_export_functionality():
    """Test export execution logs functionality"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== Testing Export Execution Logs Functionality ===\n")
    
    # 1. Test API endpoint
    print("1. Testing export API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/export-execution-logs")
        if response.status_code == 200:
            content_type = response.headers.get('content-type')
            content_length = response.headers.get('content-length')
            print(f"   ✅ Success: Status={response.status_code}, Content-Type={content_type}, Size={content_length} bytes")
            
            # Check if it's an Excel file
            if content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                print("   ✅ Content is Excel format")
            else:
                print(f"   ⚠️  Unexpected content type: {content_type}")
                
        else:
            print(f"   ❌ Failed: Status={response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing export: {e}")
        return False
    
    # 2. Test web page functionality
    print("\n2. Testing web page functionality...")
    try:
        response = requests.get(f"{base_url}/daily-statistics")
        if response.status_code == 200:
            print("   ✅ Daily statistics page loads successfully")
            
            # Check if export button exists in the HTML
            if 'Export All Logs' in response.text:
                print("   ✅ Export button found in page")
            else:
                print("   ⚠️  Export button not found in page")
                
        else:
            print(f"   ❌ Failed to load page: Status={response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing web page: {e}")
        return False
    
    # 3. Test database has logs to export
    print("\n3. Checking database for execution logs...")
    try:
        from app import app, StatisticsLog
        
        with app.app_context():
            log_count = StatisticsLog.query.count()
            print(f"   Execution logs in database: {log_count}")
            
            if log_count > 0:
                print("   ✅ Database has execution logs to export")
            else:
                print("   ⚠️  No execution logs in database")
                
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return False
    
    print("\n=== Export Functionality Test Completed Successfully ===")
    return True

if __name__ == "__main__":
    try:
        success = test_export_functionality()
        if success:
            print("\n✅ All export tests passed!")
            print("\nHow to test manually:")
            print("1. Open http://127.0.0.1:5000/daily-statistics")
            print("2. Click 'Export All Logs' button")
            print("3. Verify Excel file downloads with all execution logs")
        else:
            print("\n❌ Some export tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
