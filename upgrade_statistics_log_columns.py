#!/usr/bin/env python3
"""
Database migration script to add missing columns to statistics_log table
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def upgrade_database():
    """Add missing columns to statistics_log table"""
    
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
                
                # Check if columns already exist
                cursor.execute("PRAGMA table_info(statistics_log)")
                columns = [row[1] for row in cursor.fetchall()]
                
                columns_to_add = [
                    'opening_balance',
                    'new_tickets', 
                    'resolved_tickets',
                    'closing_balance',
                    'age_lt_24h',
                    'age_gt_96h'
                ]
                
                existing_columns = []
                missing_columns = []
                
                for column in columns_to_add:
                    if column in columns:
                        existing_columns.append(column)
                    else:
                        missing_columns.append(column)
                
                if existing_columns:
                    print(f"  ✓ Existing columns: {existing_columns}")
                
                if missing_columns:
                    print(f"  Adding missing columns to statistics_log table: {missing_columns}")
                    
                    # Add each missing column with default value 0
                    for column in missing_columns:
                        cursor.execute(f"""
                            ALTER TABLE statistics_log 
                            ADD COLUMN {column} INTEGER DEFAULT 0
                        """)
                        print(f"    ✓ Added column: {column}")
                    
                    conn.commit()
                    print(f"  ✓ Successfully added {len(missing_columns)} columns to {db_path}")
                    updated_databases.append(db_path)
                else:
                    print(f"  ✓ All columns already exist in {db_path}")
                
                # Verify the columns were added
                cursor.execute("PRAGMA table_info(statistics_log)")
                columns_after = [row[1] for row in cursor.fetchall()]
                print(f"  Current columns: {columns_after}")
                
                # Show sample data
                cursor.execute("SELECT id, execution_time, statistic_date, opening_balance, new_tickets, resolved_tickets, closing_balance FROM statistics_log LIMIT 3")
                sample_data = cursor.fetchall()
                if sample_data:
                    print(f"  Sample data:")
                    for row in sample_data:
                        print(f"    ID: {row[0]}, Time: {row[1]}, Date: {row[2]}, Opening: {row[3]}, New: {row[4]}, Resolved: {row[5]}, Closing: {row[6]}")
                else:
                    print(f"  No statistics log data found in {db_path}")
                
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
    print("=== Database Migration: Adding Missing Columns to statistics_log Table ===\n")
    upgrade_database()
