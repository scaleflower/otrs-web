#!/usr/bin/env python3
"""
Test script for database statistics API
"""

import requests
import json

def test_database_stats():
    try:
        # Test the database stats API endpoint
        response = requests.get('http://127.0.0.1:5000/database-stats')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Database stats API test successful!")
            print(f"Total records: {data.get('total_records', 0)}")
            print(f"Data sources: {data.get('data_sources_count', 0)}")
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success'):
                stats = data.get('stats', {})
                print(f"Open tickets: {stats.get('current_open_count', 0)}")
                print(f"Empty first response: {stats.get('empty_firstresponse_count', 0)}")
                
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Flask app is running.")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_database_stats()
