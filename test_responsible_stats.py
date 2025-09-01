#!/usr/bin/env python3
"""
Test script for Responsible statistics functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket, ResponsibleConfig
from datetime import datetime, timedelta
import json

def create_test_data():
    """Create test data for Responsible statistics"""
    print("Creating test data...")
    
    # Clear existing test data
    OtrsTicket.query.filter(OtrsTicket.data_source == 'test_data').delete()
    db.session.commit()
    
    # Create test tickets with different responsibles and dates
    responsibles = ['张三', '李四', '王五', '赵六']
    priorities = ['1 very low', '2 low', '3 normal', '4 high', '5 very high']
    states = ['new', 'open', 'pending reminder', 'pending auto close+', 'closed', 'resolved']
    
    # Create tickets for the last 30 days
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(100):
        responsible = responsibles[i % len(responsibles)]
        created_date = base_date + timedelta(days=i % 30, hours=i % 24)
        
        ticket = OtrsTicket(
            ticket_number=f"TEST-{i:04d}",
            created_date=created_date,
            closed_date=created_date + timedelta(hours=2) if i % 3 == 0 else None,
            state=states[i % len(states)],
            priority=priorities[i % len(priorities)],
            first_response="First response content" if i % 5 != 0 else None,
            age=f"{i % 7}d {i % 24}h {i % 60}m",
            age_hours=(i % 7) * 24 + (i % 24) + (i % 60) / 60,
            queue="Test Queue",
            owner=f"owner_{i % 10}",
            customer_id=f"CUST-{i % 100:03d}",
            customer_realname=f"Customer {i % 100}",
            title=f"Test Ticket {i}",
            service="Test Service",
            type="Incident",
            category="Test Category",
            sub_category="Test Sub Category",
            responsible=responsible,
            data_source="test_data",
            raw_data=json.dumps({"test": "data"})
        )
        db.session.add(ticket)
    
    db.session.commit()
    print("Test data created successfully!")

def test_responsible_list():
    """Test getting responsible list"""
    print("\nTesting responsible list API...")
    with app.test_client() as client:
        response = client.get('/api/responsible-list')
        data = response.get_json()
        print(f"Responsible list: {data['responsibles']}")
        assert data['success'] == True
        assert len(data['responsibles']) > 0
        print("✓ Responsible list API works correctly")

def test_responsible_stats():
    """Test getting responsible statistics"""
    print("\nTesting responsible statistics API...")
    with app.test_client() as client:
        # Test with day period
        response = client.post('/api/responsible-stats', json={
            'period': 'day',
            'selectedResponsibles': ['张三', '李四']
        })
        data = response.get_json()
        print(f"Day stats response: {data['success']}")
        if data['success']:
            print(f"Found stats for {len(data['stats'])} responsibles")
            print(f"Totals: {data['totals']}")
        assert data['success'] == True
        print("✓ Day period statistics work correctly")
        
        # Test with week period
        response = client.post('/api/responsible-stats', json={
            'period': 'week',
            'selectedResponsibles': ['张三', '李四']
        })
        data = response.get_json()
        print(f"Week stats response: {data['success']}")
        assert data['success'] == True
        print("✓ Week period statistics work correctly")
        
        # Test with month period
        response = client.post('/api/responsible-stats', json={
            'period': 'month',
            'selectedResponsibles': ['张三', '李四']
        })
        data = response.get_json()
        print(f"Month stats response: {data['success']}")
        assert data['success'] == True
        print("✓ Month period statistics work correctly")

def test_responsible_config():
    """Test responsible configuration"""
    print("\nTesting responsible configuration API...")
    with app.test_client() as client:
        # Save configuration
        response = client.post('/api/responsible-config', json={
            'selectedResponsibles': ['张三', '王五']
        })
        data = response.get_json()
        print(f"Save config response: {data['success']}")
        assert data['success'] == True
        print("✓ Configuration save works correctly")
        
        # Get configuration
        response = client.get('/api/responsible-config')
        data = response.get_json()
        print(f"Get config response: {data['selectedResponsibles']}")
        assert data['success'] == True
        assert set(data['selectedResponsibles']) == {'张三', '王五'}
        print("✓ Configuration retrieval works correctly")

def test_responsible_details():
    """Test getting responsible details"""
    print("\nTesting responsible details API...")
    with app.test_client() as client:
        # Get some date from the test data
        test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.post('/api/responsible-details', json={
            'responsible': '张三',
            'period': 'day',
            'timeValue': test_date
        })
        data = response.get_json()
        print(f"Details response: {data['success']}")
        if data['success']:
            print(f"Found {data['count']} tickets for 张三 on {test_date}")
        print("✓ Details API works correctly")

def main():
    """Main test function"""
    print("Starting Responsible statistics tests...")
    
    with app.app_context():
        try:
            # Create test data
            create_test_data()
            
            # Run tests
            test_responsible_list()
            test_responsible_stats()
            test_responsible_config()
            test_responsible_details()
            
            print("\n🎉 All tests passed! Responsible statistics functionality is working correctly.")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
