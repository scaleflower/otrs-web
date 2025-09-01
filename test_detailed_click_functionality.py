#!/usr/bin/env python3
"""
Detailed test script to verify click functionality shows correct number of tickets
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket
from datetime import datetime, timedelta
import json

def create_test_tickets():
    """Create test tickets for a specific responsible person"""
    print("Creating test tickets for 张三...")
    
    with app.app_context():
        # Clear existing test tickets
        OtrsTicket.query.filter(OtrsTicket.data_source == 'detailed_test').delete()
        db.session.commit()
        
        # Create 3 test tickets for the same date
        test_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(3):
            ticket = OtrsTicket(
                ticket_number=f"DETAILED-TEST-{i+1:03d}",
                created_date=test_date + timedelta(hours=i+9),  # 9AM, 10AM, 11AM
                state=['new', 'open', 'closed'][i],
                priority=['1 very low', '2 low', '3 normal'][i],
                first_response=f'Test response {i+1}',
                age=f'{i+1}d {i*2}h',
                age_hours=(i+1)*24 + i*2,
                queue='Test Queue',
                owner=f'test_owner_{i}',
                customer_id=f'CUST-TEST-{i:03d}',
                customer_realname=f'Test Customer {i+1}',
                title=f'Detailed Test Ticket {i+1}',
                service='Test Service',
                type='Incident',
                category='Test Category',
                sub_category='Test Sub Category',
                responsible='张三',
                data_source='detailed_test',
                raw_data=json.dumps({"test": "detailed_data", "index": i})
            )
            db.session.add(ticket)
        
        db.session.commit()
        print("Created 3 test tickets for 张三")

def test_detailed_click_functionality():
    """Test that click functionality shows correct number of tickets"""
    print("Testing detailed click functionality...")
    
    with app.app_context():
        # Create test data
        create_test_tickets()
        
        # Test the API endpoints
        from flask import Flask
        from flask.testing import FlaskClient
        
        with app.test_client() as client:
            # First get statistics
            response = client.post('/api/responsible-stats', json={
                'period': 'day',
                'selectedResponsibles': ['张三']
            })
            stats_data = response.get_json()
            
            if not stats_data['success']:
                print(f"❌ Failed to get stats: {stats_data.get('error', 'Unknown error')}")
                return False
            
            print(f"Found stats for {len(stats_data['stats'])} responsibles")
            
            # Check if 张三 has stats
            if '张三' in stats_data['stats']:
                periods = stats_data['stats']['张三']
                if periods:
                    # Get today's date
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    if today in periods:
                        count = periods[today]
                        print(f"Found {count} tickets for 张三 on {today}")
                        
                        # Test clicking on the count
                        response = client.post('/api/responsible-details', json={
                            'responsible': '张三',
                            'period': 'day',
                            'timeValue': today
                        })
                        details_data = response.get_json()
                        
                        if details_data['success']:
                            actual_count = details_data['count']
                            print(f"API returned {actual_count} tickets")
                            
                            # Verify the count matches
                            if actual_count == count:
                                print(f"✓ Count matches! Expected {count}, got {actual_count}")
                                
                                # Verify all tickets have correct fields
                                if actual_count > 0:
                                    for i, ticket in enumerate(details_data['details']):
                                        print(f"\nTicket {i+1}:")
                                        print(f"  Number: {ticket['ticket_number']}")
                                        print(f"  Created: {ticket['created']}")
                                        print(f"  State: {ticket['state']}")
                                        print(f"  Priority: {ticket['priority']}")
                                        print(f"  Title: {ticket['title']}")
                                    
                                    # Check if we have exactly 3 tickets
                                    if actual_count == 3:
                                        print("✓ Correctly found 3 tickets as expected!")
                                        return True
                                    else:
                                        print(f"❌ Expected 3 tickets, but found {actual_count}")
                                        return False
                                else:
                                    print("❌ No tickets found in details")
                                    return False
                            else:
                                print(f"❌ Count mismatch! Expected {count}, but API returned {actual_count}")
                                return False
                        else:
                            print(f"❌ Details API failed: {details_data.get('error', 'Unknown error')}")
                            return False
                    else:
                        print(f"❌ Today's date {today} not found in periods: {list(periods.keys())}")
                        return False
                else:
                    print("❌ No periods found for responsible 张三")
                    return False
            else:
                print("❌ Responsible 张三 not found in stats")
                return False

def main():
    """Main function"""
    print("=" * 60)
    print("Detailed Click Functionality Test")
    print("=" * 60)
    print("This test verifies that clicking on a count number shows")
    print("the correct number of ticket details.")
    print("=" * 60)
    
    try:
        success = test_detailed_click_functionality()
        
        if success:
            print("\n🎉 Detailed click functionality test completed successfully!")
            print("The feature correctly shows 3 ticket details when clicking on count 3.")
        else:
            print("\n❌ Detailed click functionality test failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
