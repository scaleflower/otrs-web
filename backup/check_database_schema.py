#!/usr/bin/env python3
"""
Script to check database schema
"""

from app import app, db
from sqlalchemy import inspect

def check_database_schema():
    """Check database schema"""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables: {tables}")
        
        # Get all tables with their columns
        for table in tables:
            print(f"\n{table} table columns:")
            columns = inspector.get_columns(table)
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        
        # Check if query_type column exists
        if 'statistic' in tables:
            columns = [col['name'] for col in inspector.get_columns('statistic')]
            if 'query_type' in columns:
                print("\n✓ query_type column exists in statistic table")
            else:
                print("\n✗ query_type column missing from statistic table")

if __name__ == '__main__':
    check_database_schema()
