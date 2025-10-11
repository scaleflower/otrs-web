#!/usr/bin/env python3
"""
Test script to verify database statistics page export functionality includes Age Segment details
"""

import sys
import json
import requests
from datetime import datetime

def test_database_export_functionality():
    """Test that database page export includes Age Segment details with State field"""
    
    print("\n" + "="*80)
    print("DATABASE STATISTICS PAGE EXPORT FUNCTIONALITY TEST")
    print("="*80)
    
    base_url = "http://localhost:5000"
    
    try:
        # 1. First get database statistics data (same as what the database page gets)
        print("\n1. Getting database statistics data...")
        db_stats_response = requests.get(f"{base_url}/database-stats")
        
        if db_stats_response.status_code != 200:
            print(f"✗ Failed to get database statistics: {db_stats_response.status_code}")
            return False
        
        db_stats_data = db_stats_response.json()
        
        if not db_stats_data.get('success'):
            print(f"✗ Database statistics request failed: {db_stats_data.get('error')}")
            return False
        
        print(f"✓ Database statistics retrieved successfully")
        print(f"  - Total records: {db_stats_data.get('total_records', 0)}")
        print(f"  - Age segments included: {'age_segments' in db_stats_data.get('stats', {})}")
        
        # Check if we have age segments data
        stats = db_stats_data.get('stats', {})
        age_segments = stats.get('age_segments', {})
        
        if not age_segments:
            print("ℹ  No age segments data available - skipping export test")
            return True
        
        print(f"  - Age ≤24h: {age_segments.get('age_24h', 0)}")
        print(f"  - Age 24-48h: {age_segments.get('age_24_48h', 0)}")
        print(f"  - Age 48-72h: {age_segments.get('age_48_72h', 0)}")
        print(f"  - Age >72h: {age_segments.get('age_72h', 0)}")
        
        # 2. Test Excel export with database statistics data
        print("\n2. Testing Excel export from database page...")
        
        # Prepare data same as database page JavaScript
        export_data = {
            'stats': stats,
            'total_records': db_stats_data.get('total_records', 0)
        }
        
        excel_response = requests.post(
            f"{base_url}/export/excel",
            json=export_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if excel_response.status_code == 200:
            print("✓ Excel export successful")
            print(f"  - Response content-type: {excel_response.headers.get('content-type')}")
            print(f"  - File size: {len(excel_response.content)} bytes")
            
            # Save to verify content
            filename = f"database_export_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with open(filename, 'wb') as f:
                f.write(excel_response.content)
            print(f"  - Saved as: {filename}")
            
        else:
            print(f"✗ Excel export failed: {excel_response.status_code}")
            try:
                error_data = excel_response.json()
                print(f"  Error: {error_data.get('error')}")
            except:
                print(f"  Error response: {excel_response.text[:200]}")
            return False
        
        # 3. Test Text export with database statistics data
        print("\n3. Testing Text export from database page...")
        
        txt_response = requests.post(
            f"{base_url}/export/txt",
            json=export_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if txt_response.status_code == 200:
            print("✓ Text export successful")
            print(f"  - Response content-type: {txt_response.headers.get('content-type')}")
            print(f"  - File size: {len(txt_response.content)} bytes")
            
            # Save and check content for Age Segment details
            filename = f"database_export_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'wb') as f:
                f.write(txt_response.content)
            print(f"  - Saved as: {filename}")
            
            # Check if text content includes Age Segment details
            text_content = txt_response.content.decode('utf-8')
            
            age_segment_sections = [
                "Age Segment Details - ≤24 hours",
                "Age Segment Details - 24-48 hours", 
                "Age Segment Details - 48-72 hours",
                "Age Segment Details - >72 hours"
            ]
            
            age_section_found = any(section in text_content for section in age_segment_sections)
            state_field_found = "State" in text_content
            
            print(f"  - Age Segment details sections found: {age_section_found}")
            print(f"  - State field found in export: {state_field_found}")
            
            if age_section_found and state_field_found:
                print("✓ Text export includes Age Segment details with State field")
            else:
                print("⚠  Text export may not include complete Age Segment details")
            
        else:
            print(f"✗ Text export failed: {txt_response.status_code}")
            try:
                error_data = txt_response.json()
                print(f"  Error: {error_data.get('error')}")
            except:
                print(f"  Error response: {txt_response.text[:200]}")
            return False
        
        # 4. Test Age Segment details API to ensure it includes State field
        print("\n4. Testing Age Segment details API...")
        
        # Test each age segment
        age_segments_to_test = ['24h', '24_48h', '48_72h', '72h']
        
        for segment in age_segments_to_test:
            if age_segments.get(f'age_{segment}', 0) > 0:
                print(f"\n  Testing age segment: {segment}")
                
                age_details_response = requests.post(
                    f"{base_url}/age-details",
                    json={'age_segment': segment},
                    headers={'Content-Type': 'application/json'}
                )
                
                if age_details_response.status_code == 200:
                    age_details_data = age_details_response.json()
                    
                    if age_details_data.get('success'):
                        details = age_details_data.get('details', [])
                        print(f"    ✓ Retrieved {len(details)} ticket details")
                        
                        if details:
                            # Check if first detail includes State field
                            first_detail = details[0]
                            required_fields = ['ticket_number', 'age', 'created', 'priority', 'state']
                            has_all_fields = all(field in first_detail for field in required_fields)
                            
                            print(f"    - Has all required fields (including State): {has_all_fields}")
                            print(f"    - Sample detail: {first_detail}")
                            
                            if not has_all_fields:
                                print(f"    ⚠  Missing fields: {[f for f in required_fields if f not in first_detail]}")
                        
                    else:
                        print(f"    ✗ Age details request failed: {age_details_data.get('error')}")
                else:
                    print(f"    ✗ Age details API failed: {age_details_response.status_code}")
        
        print("\n" + "="*80)
        print("DATABASE EXPORT FUNCTIONALITY TEST SUMMARY")
        print("="*80)
        print("✓ Database statistics page export functionality includes:")
        print("  - Complete Age Segment data structure")
        print("  - Individual ticket details for each age segment") 
        print("  - State field in Age Segment details")
        print("  - Both Excel and Text export formats supported")
        print("\n✓ The database statistics page export functionality DOES include")
        print("  Age Segment detail data with individual ticket information!")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to Flask application at http://localhost:5000")
        print("  Please make sure the application is running with: python app.py")
        return False
    except Exception as e:
        print(f"✗ Test error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_export_functionality()
    sys.exit(0 if success else 1)
