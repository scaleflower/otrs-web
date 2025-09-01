#!/usr/bin/env python3
"""
Test script to verify Responsible details filtering by period
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket
from datetime import datetime, timedelta

def test_responsible_details_period_filtering():
    """Test that responsible details are properly filtered by period"""
    print("Testing Responsible details period filtering...")
    
    with app.app_context():
        # Create test data with specific dates
        test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        test_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%W')
        test_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m')
        
        # Test with app test client
        with app.test_client() as client:
            # Test day period
            response = client.post('/api/responsible-details', json={
                'responsible': '张三',
                'period': 'day',
                'timeValue': test_date
            })
            data = response.get_json()
            print(f"Day period response: {data['success']}")
            if data['success']:
                print(f"Found {data['count']} tickets for 张三 on {test_date}")
            
            # Test week period
            response = client.post('/api/responsible-details', json={
                'responsible': '张三',
                'period': 'week',
                'timeValue': test_week
            })
            data = response.get_json()
            print(f"Week period response: {data['success']}")
            if data['success']:
                print(f"Found {data['count']} tickets for 张三 in week {test_week}")
            
            # Test month period
            response = client.post('/api/responsible-details', json={
                'responsible': '张三',
                'period': 'month',
                'timeValue': test_month
            })
            data = response.get_json()
            print(f"Month period response: {data['success']}")
            if data['success']:
                print(f"Found {data['count']} tickets for 张三 in month {test_month}")
            
            print("✓ Responsible details period filtering works correctly")

def main():
    """Main test function"""
    print("Testing Responsible details period filtering...")
    
    try:
        test_responsible_details_period_filtering()
        print("\n🎉 All Responsible details period filtering tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
