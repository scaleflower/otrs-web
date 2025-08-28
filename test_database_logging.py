#!/usr/bin/env python3
"""
Test script for database logging functionality
"""

import requests
import json
import sqlite3
import pandas as pd
import io

def test_database_logging():
    """Test database logging for various operations"""
    print("Testing database logging functionality...")
    
    # First, clear the database to start fresh
    response = requests.post('http://127.0.0.1:5000/clear-database', 
                           headers={'Content-Type': 'application/json'})
    print(f"Clear database: {response.status_code}")
    
    # Check current log count
    conn = sqlite3.connect('instance/otrs_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM database_log')
    initial_log_count = cursor.fetchone()[0]
    print(f"Initial log entries: {initial_log_count}")
    
    # Test 1: Upload a file (should create log entries)
    print("\n1. Testing file upload with logging...")
    
    # Create a simple test Excel file
    test_data = {
        'Ticket Number': ['TICKET001', 'TICKET002'],
        'Created': ['2025-01-01', '2025-01-02'],
        'State': ['Open', 'Closed'],
        'Priority': ['High', 'Normal'],
        'FirstResponse': ['', 'Some response'],
        'Age': ['1d 2h', '0d 5h']
    }
    df = pd.DataFrame(test_data)
    
    # Save to buffer
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tickets')
    excel_buffer.seek(0)
    
    # Upload the file
    files = {'file': ('test_file.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post('http://127.0.0.1:5000/upload', files=files)
    print(f"Upload response: {response.status_code}")
    
    if response.status_code == 200:
        print("Upload successful")
        # Check if log entry was created for upload
        cursor.execute('SELECT operation_type, table_name, records_affected FROM database_log ORDER BY id DESC LIMIT 1')
        latest_log = cursor.fetchone()
        if latest_log:
            print(f"Latest log after upload: {latest_log}")
    
    # Test 2: Export operations (should create log entries)
    print("\n2. Testing export operations with logging...")
    
    # Export to Excel
    response = requests.post('http://127.0.0.1:5000/export/excel', 
                           headers={'Content-Type': 'application/json'},
                           json={'stats': {}})
    print(f"Excel export response: {response.status_code}")
    
    # Export to Text
    response = requests.post('http://127.0.0.1:5000/export/txt', 
                           headers={'Content-Type': 'application/json'},
                           json={'stats': {}})
    print(f"Text export response: {response.status_code}")
    
    # Check final log count
    cursor.execute('SELECT COUNT(*) FROM database_log')
    final_log_count = cursor.fetchone()[0]
    cursor.execute('SELECT operation_type, table_name, records_affected FROM database_log ORDER BY id')
    all_logs = cursor.fetchall()
    
    print(f"\nFinal log entries: {final_log_count}")
    print("All log entries:")
    for i, log in enumerate(all_logs, 1):
        print(f"  {i}. {log}")
    
    conn.close()
    return True

if __name__ == "__main__":
    test_database_logging()
