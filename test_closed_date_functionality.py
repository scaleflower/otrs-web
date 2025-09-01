#!/usr/bin/env python3
"""
Test script to verify responsible statistics now use closed_date for workload calculation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket
from datetime import datetime, timedelta
import json

def create_test_tickets_with_closed_dates():
    """Create test tickets with specific closed dates for testing"""
    print("Creating test tickets with closed dates for 张三...")
    
    with app.app_context():
        # Clear existing test tickets
        OtrsTicket.query.filter(OtrsTicket.data_source == 'closed_date_test').delete()
        db.session.commit()
        
        # Create test tickets with different closed dates
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Ticket 1: Closed today
        ticket1 = OtrsTicket(
            ticket_number="CLOSED-TEST-001",
            created_date=today - timedelta(days=2),
            closed_date=today,  # Closed today
            state='closed',
            priority='3 normal',
            first_response='Test response 1',
            age='2d 5h',
            age_hours=53,
            queue='Test Queue',
            owner='test_owner_1',
            customer_id='CUST-TEST-001',
            customer_realname='Test Customer 1',
            title='Test Ticket Closed Today',
            service='Test Service',
            type='Incident',
            category='Test Category',
            sub_category='Test Sub Category',
            responsible='张三',
            data_source='closed_date_test',
            raw_data=json.dumps({"test": "closed_date_data", "index": 1})
        )
        
        # Ticket 2: Closed yesterday
        ticket2 = OtrsTicket(
            ticket_number="CLOSED-TEST-002",
            created_date=today - timedelta(days=3),
            closed_date=today - timedelta(days=1),  # Closed yesterday
            state='closed',
            priority='2 low',
            first_response='Test response 2',
            age='3d 2h',
            age_hours=74,
            queue='Test Queue',
            owner='test_owner_2',
            customer_id='CUST-TEST-002',
            customer_realname='Test Customer 2',
            title='Test Ticket Closed Yesterday',
            service='Test Service',
            type='Incident',
            category='Test Category',
            sub_category='Test Sub Category',
            responsible='张三',
            data_source='closed_date_test',
            raw_data=json.dumps({"test": "closed_date_data", "index": 2})
        )
        
        # Ticket 3: Closed 2 days ago
        ticket3 = OtrsTicket(
            ticket_number="CLOSED-TEST-003",
            created_date=today - timedelta(days=4),
            closed_date=today - timedelta(days=2),  # Closed 2 days ago
            state='closed',
            priority='1 very low',
            first_response='Test response 3',
            age='4d 8h',
            age_hours=104,
            queue='Test Queue',
            owner='test_owner_3',
            customer_id='CUST-TEST-003',
            customer_realname='Test Customer 3',
            title='Test Ticket Closed 2 Days Ago',
            service='Test Service',
            type='Incident',
            category='Test Category',
            sub_category='Test Sub Category',
            responsible='张三',
            data_source='closed_date_test',
            raw_data=json.dumps({"test": "closed_date_data", "index": 3})
        )
        
        db.session.add(ticket1)
        db.session.add(ticket2)
        db.session.add(ticket3)
        db.session.commit()
        print("Created 3 test tickets with closed dates for 张三")

def test_closed_date_functionality():
    """Test that responsible statistics now use closed_date for workload calculation"""
    print("Testing closed_date functionality for responsible statistics...")
    
    with app.app_context():
        # Create test data
        create_test_tickets_with_closed_dates()
        
        # Test the API endpoints
        from flask import Flask
        from flask.testing import FlaskClient
        
        with app.test_client() as client:
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            
            print(f"Testing dates: Today={today}, Yesterday={yesterday}, 2 Days Ago={two_days_ago}")
            
            # Test statistics for today
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
                print(f"Periods found: {list(periods.keys())}")
                
                # Verify that statistics are based on closed_date
                if today in periods:
                    print(f"✓ Found {periods[today]} tickets closed today")
                else:
                    print(f"❌ No tickets found for today ({today})")
                
                if yesterday in periods:
                    print(f"✓ Found {periods[yesterday]} tickets closed yesterday")
                else:
                    print(f"❌ No tickets found for yesterday ({yesterday})")
                
                if two_days_ago in periods:
                    print(f"✓ Found {periods[two_days_ago]} tickets closed 2 days ago")
                else:
                    print(f"❌ No tickets found for 2 days ago ({two_days_ago})")
                
                # Test clicking on today's count
                if today in periods:
                    count = periods[today]
                    print(f"Testing click on today's count: {count}")
                    
                    response = client.post('/api/responsible-details', json={
                        'responsible': '张三',
                        'period': 'day',
                        'timeValue': today
                    })
                    details_data = response.get_json()
                    
                    if details_data['success']:
                        actual_count = details_data['count']
                        print(f"API returned {actual_count} tickets closed today")
                        
                        if actual_count == count:
                            print("✓ Count matches! Statistics and details are consistent")
                            
                            # Verify the details show tickets closed today
                            if actual_count > 0:
                                for i, ticket in enumerate(details_data['details']):
                                    print(f"Ticket {i+1}: {ticket['ticket_number']} - Closed: {ticket['closed']}")
                                
                                # Check if we have exactly 1 ticket closed today (as expected)
                                if actual_count == 1:
                                    print("✓ Correctly found 1 ticket closed today!")
                                    return True
                                else:
                                    print(f"❌ Expected 1 ticket closed today, but found {actual_count}")
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
                    print("❌ Today's date not found in periods")
                    return False
            else:
                print("❌ Responsible 张三 not found in stats")
                return False

def main():
    """Main function"""
    print("=" * 60)
    print("Closed Date Functionality Test")
    print("=" * 60)
    print("This test verifies that responsible statistics now use")
    print("closed_date instead of created_date for workload calculation.")
    print("=" * 60)
    
    try:
        success = test_closed_date_functionality()
        
        if success:
            print("\n🎉 Closed date functionality test completed successfully!")
            print("The responsible statistics feature now correctly uses closed_date")
            print("for workload calculation instead of created_date.")
        else:
            print("\n❌ Closed date functionality test failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
