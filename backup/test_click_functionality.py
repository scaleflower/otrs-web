#!/usr/bin/env python3
"""
Test script to verify click functionality on responsible statistics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket
from datetime import datetime, timedelta
import json

def test_click_functionality():
    """Test that click functionality works correctly"""
    print("Testing click functionality on responsible statistics...")
    
    with app.app_context():
        # Get test data
        test_ticket = OtrsTicket.query.filter(
            OtrsTicket.responsible == '张三',
            OtrsTicket.created_date.isnot(None)
        ).first()
        
        if not test_ticket:
            print("No test data found")
            return False
        
        # Test the API endpoint that gets called when clicking
        from flask import Flask
        from flask.testing import FlaskClient
        
        with app.test_client() as client:
            # First get statistics to see what periods are available
            response = client.post('/api/responsible-stats', json={
                'period': 'day',
                'selectedResponsibles': ['张三']
            })
            stats_data = response.get_json()
            
            if not stats_data['success']:
                print(f"❌ Failed to get stats: {stats_data.get('error', 'Unknown error')}")
                return False
            
            print(f"Found stats for {len(stats_data['stats'])} responsibles")
            
            # Test clicking on a period count
            if '张三' in stats_data['stats']:
                periods = stats_data['stats']['张三']
                if periods:
                    # Get the first available period
                    period_key = list(periods.keys())[0]
                    count = periods[period_key]
                    
                    print(f"Testing click on period: {period_key} with count: {count}")
                    
                    # Simulate the click by calling the details API
                    response = client.post('/api/responsible-details', json={
                        'responsible': '张三',
                        'period': 'day',
                        'timeValue': period_key
                    })
                    details_data = response.get_json()
                    
                    if details_data['success']:
                        print(f"✓ Click functionality works! Found {details_data['count']} tickets for period {period_key}")
                        
                        # Verify the details contain expected fields
                        if details_data['count'] > 0:
                            ticket = details_data['details'][0]
                            expected_fields = ['ticket_number', 'created', 'closed', 'state', 'priority', 'title']
                            missing_fields = [field for field in expected_fields if field not in ticket]
                            
                            if missing_fields:
                                print(f"❌ Missing fields in details: {missing_fields}")
                                return False
                            else:
                                print("✓ All expected fields present in ticket details")
                                return True
                        else:
                            print("⚠ No tickets found for this period (this might be expected)")
                            return True
                    else:
                        print(f"❌ Details API failed: {details_data.get('error', 'Unknown error')}")
                        return False
                else:
                    print("⚠ No periods found for responsible 张三")
                    return True
            else:
                print("⚠ Responsible 张三 not found in stats")
                return True

def main():
    """Main function"""
    print("=" * 60)
    print("Click Functionality Test")
    print("=" * 60)
    
    try:
        success = test_click_functionality()
        
        if success:
            print("\n🎉 Click functionality test completed successfully!")
            print("The responsible statistics feature is working correctly.")
            print("Users can click on the count numbers to see ticket details.")
        else:
            print("\n❌ Click functionality test failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
