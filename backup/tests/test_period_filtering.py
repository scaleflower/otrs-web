#!/usr/bin/env python3
"""
Test script to verify period filtering functionality for responsible statistics
"""

import requests
import json
from datetime import datetime

def test_period_filtering():
    """Test period filtering functionality"""
    base_url = "http://localhost:5000"
    
    # First, get list of available responsibles
    print("1. Getting responsible list...")
    response = requests.get(f"{base_url}/api/responsible-list")
    
    if response.status_code != 200:
        print(f"❌ Failed to get responsible list: {response.status_code}")
        return False
    
    data = response.json()
    if not data.get('success'):
        print(f"❌ Error getting responsible list: {data.get('error')}")
        return False
    
    responsibles = data.get('responsibles', [])
    if not responsibles:
        print("❌ No responsibles found in database")
        return False
    
    print(f"✓ Found {len(responsibles)} responsibles")
    
    # Test with first few responsibles
    test_responsibles = responsibles[:3]
    print(f"Testing with: {test_responsibles}")
    
    # Test different periods
    periods = ['total', 'day', 'week', 'month']
    
    for period in periods:
        print(f"\n2. Testing period: {period}")
        
        test_data = {
            'selected_responsibles': test_responsibles,
            'period': period
        }
        
        response = requests.post(
            f"{base_url}/api/responsible-stats",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_data)
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get stats for period {period}: {response.status_code}")
            continue
        
        result = response.json()
        if not result.get('success'):
            print(f"❌ Error getting stats for period {period}: {result.get('error')}")
            continue
        
        stats = result.get('stats', {})
        total_by_responsible = stats.get('total_by_responsible', {})
        
        print(f"✓ Period {period} results:")
        for responsible, count in total_by_responsible.items():
            print(f"  - {responsible}: {count} tickets")
        
        # Check if period_stats exists for non-total periods
        if period != 'total' and 'period_stats' in stats:
            print(f"  ✓ Period-specific breakdown available")
        
        print(f"  Total tickets across all responsibles: {sum(total_by_responsible.values())}")
    
    print("\n3. Comparing periods...")
    
    # Compare total vs day to see if filtering works
    total_response = requests.post(
        f"{base_url}/api/responsible-stats",
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'selected_responsibles': test_responsibles,
            'period': 'total'
        })
    )
    
    day_response = requests.post(
        f"{base_url}/api/responsible-stats",
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'selected_responsibles': test_responsibles,
            'period': 'day'
        })
    )
    
    if total_response.status_code == 200 and day_response.status_code == 200:
        total_data = total_response.json()
        day_data = day_response.json()
        
        if total_data.get('success') and day_data.get('success'):
            total_count = sum(total_data['stats']['total_by_responsible'].values())
            day_count = sum(day_data['stats']['total_by_responsible'].values())
            
            print(f"Total period: {total_count} tickets")
            print(f"Day period: {day_count} tickets")
            
            if day_count <= total_count:
                print("✓ Period filtering appears to be working (day count <= total count)")
            else:
                print("❌ Period filtering may not be working properly (day count > total count)")
    
    print("\n✓ Period filtering test completed!")
    return True

if __name__ == "__main__":
    print("Testing Period Filtering Functionality")
    print("="*50)
    
    try:
        test_period_filtering()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Please make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
