#!/usr/bin/env python3
"""
Database migration script to add new_records_count column to upload_detail table
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def upgrade_database():
    """Add new_records_count column to upload_detail table"""
    
    # Database paths to check
    db_paths = [
        'instance/otrs_data.db',
        'db/otrs_data.db'
    ]
    
    updated_databases = []
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Found database: {db_path}")
            
            try:
                # Connect to database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if new_records_count column already exists
                cursor.execute("PRAGMA table_info(upload_detail)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'new_records_count' in columns:
                    print(f"  ✓ Column 'new_records_count' already exists in {db_path}")
                else:
                    print(f"  Adding 'new_records_count' column to upload_detail table...")
                    
                    # Add the new column with default value 0
                    cursor.execute("""
                        ALTER TABLE upload_detail 
                        ADD COLUMN new_records_count INTEGER DEFAULT 0
                    """)
                    
                    # Update existing records: set new_records_count = record_count for backward compatibility
                    cursor.execute("""
                        UPDATE upload_detail 
                        SET new_records_count = record_count 
                        WHERE new_records_count IS NULL OR new_records_count = 0
                    """)
                    
                    conn.commit()
                    print(f"  ✓ Successfully added 'new_records_count' column to {db_path}")
                    updated_databases.append(db_path)
                
                # Verify the column was added
                cursor.execute("PRAGMA table_info(upload_detail)")
                columns_after = [row[1] for row in cursor.fetchall()]
                print(f"  Current columns: {columns_after}")
                
                # Show sample data
                cursor.execute("SELECT id, filename, record_count, new_records_count, import_mode FROM upload_detail LIMIT 3")
                sample_data = cursor.fetchall()
                if sample_data:
                    print(f"  Sample data:")
                    for row in sample_data:
                        print(f"    ID: {row[0]}, File: {row[1]}, Total: {row[2]}, New: {row[3]}, Mode: {row[4]}")
                else:
                    print(f"  No upload data found in {db_path}")
                
                conn.close()
                
            except Exception as e:
                print(f"  ✗ Error updating database {db_path}: {e}")
                if 'conn' in locals():
                    conn.close()
    
    if updated_databases:
        print(f"\n✓ Successfully updated {len(updated_databases)} database(s)")
        for db_path in updated_databases:
            print(f"  - {db_path}")
    else:
        print(f"\n✓ All databases are already up to date")
    
    print(f"\nMigration completed at {datetime.now()}")

if __name__ == '__main__':
    print("=== Database Migration: Adding new_records_count Column ===\n")
    upgrade_database()
