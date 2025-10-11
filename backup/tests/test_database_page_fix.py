#!/usr/bin/env python3
"""
Test script to verify the database statistics page Age Segments fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, OtrsTicket
import json

def test_database_page_api():
    """Test the database page API endpoints"""
    
    with app.app_context():
        print("🔍 Testing Database Statistics Page API")
        print("=" * 60)
        
        # 1. Check if we have data in database
        total_tickets = OtrsTicket.query.count()
        print(f"📊 Total tickets in database: {total_tickets}")
        
        if total_tickets == 0:
            print("❌ No data in database. Please upload some data first.")
            return False
        
        # 2. Test /age-details API endpoint
        print("\n🔍 Testing /age-details API:")
        
        with app.test_client() as client:
            # Test different age segments
            age_segments = ['24h', '24_48h', '48_72h', '72h']
            
            for segment in age_segments:
                response = client.post('/age-details', 
                                     data=json.dumps({'age_segment': segment}),
                                     content_type='application/json')
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    if data.get('success'):
                        details = data.get('details', [])
                        print(f"✅ {segment} segment API: {len(details)} tickets")
                        
                        # Check if State field is included
                        if details:
                            sample_detail = details[0]
                            if 'state' in sample_detail:
                                print(f"   ✅ State field found: {sample_detail['state']}")
                            else:
                                print(f"   ❌ State field missing in response!")
                                return False
                        else:
                            print(f"   ℹ️  No tickets in {segment} segment")
                    else:
                        print(f"❌ {segment} segment API failed: {data.get('error')}")
                        return False
                else:
                    print(f"❌ {segment} segment API HTTP error: {response.status_code}")
                    return False
        
        # 3. Test /database-stats API endpoint
        print("\n🔍 Testing /database-stats API:")
        
        with app.test_client() as client:
            response = client.get('/database-stats')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                if data.get('success'):
                    print("✅ Database stats API successful")
                    
                    # Check if empty_firstresponse_details includes state
                    empty_details = data.get('empty_firstresponse_details', [])
                    print(f"   Empty FirstResponse details: {len(empty_details)} tickets")
                    
                    if empty_details:
                        sample_detail = empty_details[0]
                        if 'state' in sample_detail:
                            print(f"   ✅ State field found in empty FirstResponse: {sample_detail['state']}")
                        else:
                            print(f"   ❌ State field missing in empty FirstResponse details!")
                            return False
                    
                    # Check age segments data
                    age_segments = data.get('stats', {}).get('age_segments', {})
                    print(f"   Age segments: {age_segments}")
                    
                else:
                    print(f"❌ Database stats API failed: {data.get('error')}")
                    return False
            else:
                print(f"❌ Database stats API HTTP error: {response.status_code}")
                return False
        
        return True

def test_template_structure():
    """Test if the template structure is correct"""
    
    print("\n🔍 Testing Template Structure:")
    
    # Read the database_stats.html template
    template_path = "templates/database_stats.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Check if Age Details table has State column
        if '<th>State</th>' in template_content:
            print("✅ Age Details table has State column header")
        else:
            print("❌ Age Details table missing State column header!")
            return False
        
        # Check if Empty FirstResponse table has State column (it should already have it)
        empty_fr_state_count = template_content.count('<th>State</th>')
        if empty_fr_state_count >= 2:  # One for Age Details, one for Empty FirstResponse
            print("✅ Both Age Details and Empty FirstResponse tables have State columns")
        else:
            print(f"⚠️  Found {empty_fr_state_count} State column headers, expected at least 2")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Database Statistics Page Fix Verification")
    print("=" * 60)
    
    api_test = test_database_page_api()
    template_test = test_template_structure()
    
    if api_test and template_test:
        print("\n🎉 DATABASE PAGE FIX TEST: PASSED")
        print("✅ Database statistics page Age Segments now include State field!")
        print("✅ Both API responses and template structure are correct")
    else:
        print("\n❌ DATABASE PAGE FIX TEST: FAILED")
        print("❌ There are still issues with the database page fixes.")
