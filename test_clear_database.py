#!/usr/bin/env python3
"""
Test script for clearing database functionality
"""

import requests
import json

def test_clear_database():
    """Test the clear database endpoint"""
    try:
        # Test the clear database endpoint
        print("Testing clear database endpoint...")
        response = requests.post('http://127.0.0.1:5000/clear-database', 
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['message']}")
            print(f"Records cleared: {result['records_cleared']}")
            
            # Check if log entry was created
            import sqlite3
            conn = sqlite3.connect('instance/otrs_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM otrs_ticket')
            ticket_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM database_log')
            log_count = cursor.fetchone()[0]
            cursor.execute('SELECT operation_type, table_name, records_affected FROM database_log ORDER BY id DESC LIMIT 1')
            log_entry = cursor.fetchone()
            conn.close()
            
            print(f"Tickets after clear: {ticket_count}")
            print(f"Log entries: {log_count}")
            if log_entry:
                print(f"Latest log entry: {log_entry}")
            
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_clear_database()
