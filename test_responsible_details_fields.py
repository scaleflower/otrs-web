#!/usr/bin/env python3
"""
Test script to verify responsible details API returns correct fields
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket
from datetime import datetime, timedelta
import json

def test_responsible_details_fields():
    """Test that responsible details API returns correct fields"""
    print("Testing responsible details API fields...")
    
    with app.app_context():
        # Create test data if needed
        test_ticket = OtrsTicket.query.filter(
            OtrsTicket.responsible == '张三',
            OtrsTicket.created_date.isnot(None)
        ).first()
        
        if not test_ticket:
            print("No test data found, creating test ticket...")
            # Create a test ticket
            ticket = OtrsTicket(
                ticket_number="TEST-DETAILS-001",
                created_date=datetime.now() - timedelta(days=1),
                state='open',
                priority='3 normal',
                first_response='Test response',
                age='1d 2h',
                age_hours=26,
                queue='Test Queue',
                owner='test_owner',
                customer_id='CUST-TEST',
                customer_realname='Test Customer',
                title='Test Ticket for Details API',
                service='Test Service',
                type='Incident',
                category='Test Category',
                sub_category='Test Sub Category',
                responsible='张三',
                data_source='test_details',
                raw_data=json.dumps({"test": "details_data"})
            )
            db.session.add(ticket)
            db.session.commit()
            test_ticket = ticket
        
        # Test the API endpoint
        from flask import Flask
        from flask.testing import FlaskClient
        
        with app.test_client() as client:
            # Get a valid date from the test ticket
            test_date = test_ticket.created_date.strftime('%Y-%m-%d')
            
            response = client.post('/api/responsible-details', json={
                'responsible': '张三',
                'period': 'day',
                'timeValue': test_date
            })
            data = response.get_json()
            
            if data['success']:
                print(f"API returned {data['count']} tickets")
                
                if data['count'] > 0:
                    # Check the first ticket has all required fields
                    ticket = data['details'][0]
                    required_fields = ['ticket_number', 'created', 'closed', 'state', 'priority', 'title']
                    
                    print("Checking required fields...")
                    missing_fields = []
                    for field in required_fields:
                        if field in ticket:
                            print(f"✓ {field}: {ticket[field]}")
                        else:
                            print(f"✗ {field}: MISSING")
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"❌ Missing fields: {missing_fields}")
                        return False
                    else:
                        print("✓ All required fields are present!")
                        return True
                else:
                    print("❌ No tickets found in response")
                    return False
            else:
                print(f"❌ API error: {data.get('error', 'Unknown error')}")
                return False

def main():
    """Main function"""
    print("=" * 60)
    print("Responsible Details Fields Verification Test")
    print("=" * 60)
    
    try:
        success = test_responsible_details_fields()
        
        if success:
            print("\n🎉 Responsible details fields verification completed successfully!")
        else:
            print("\n❌ Responsible details fields verification failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
