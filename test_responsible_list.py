#!/usr/bin/env python3
"""
Test script to verify responsible list functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket

def test_responsible_list():
    """Test responsible list functionality"""
    print("Testing responsible list functionality...")
    
    with app.app_context():
        # Get all unique Responsible values directly from database
        responsibles = db.session.query(OtrsTicket.responsible).distinct().all()
        responsible_list = [r[0] for r in responsibles if r[0] is not None and r[0] != '']
        
        print(f"Total unique responsibles found: {len(responsible_list)}")
        print(f"Responsible list: {sorted(responsible_list)}")
        
        # Test the API endpoint
        from flask import Flask
        from flask.testing import FlaskClient
        
        with app.test_client() as client:
            response = client.get('/api/responsible-list')
            data = response.get_json()
            
            if data['success']:
                api_responsibles = data['responsibles']
                print(f"API returned {len(api_responsibles)} responsibles")
                print(f"API responsibles: {api_responsibles}")
                
                # Check if both lists match
                if set(responsible_list) == set(api_responsibles):
                    print("✓ Direct query and API results match!")
                    return True
                else:
                    print("✗ Direct query and API results don't match!")
                    print(f"Missing in API: {set(responsible_list) - set(api_responsibles)}")
                    print(f"Extra in API: {set(api_responsibles) - set(responsible_list)}")
                    return False
            else:
                print(f"API error: {data.get('error', 'Unknown error')}")
                return False

def check_responsible_data():
    """Check actual responsible data in database"""
    print("\nChecking responsible data in database...")
    
    with app.app_context():
        # Get all tickets with responsible field
        tickets_with_responsible = OtrsTicket.query.filter(
            OtrsTicket.responsible.isnot(None),
            OtrsTicket.responsible != ''
        ).all()
        
        print(f"Total tickets with responsible field: {len(tickets_with_responsible)}")
        
        # Count by responsible
        responsible_counts = {}
        for ticket in tickets_with_responsible:
            if ticket.responsible:
                responsible_counts[ticket.responsible] = responsible_counts.get(ticket.responsible, 0) + 1
        
        print("Responsible counts:")
        for responsible, count in sorted(responsible_counts.items()):
            print(f"  {responsible}: {count} tickets")

def main():
    """Main function"""
    print("=" * 60)
    print("Responsible List Verification Test")
    print("=" * 60)
    
    try:
        # Test responsible list functionality
        success = test_responsible_list()
        
        # Check actual data
        check_responsible_data()
        
        if success:
            print("\n🎉 Responsible list verification completed successfully!")
        else:
            print("\n❌ Responsible list verification failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
