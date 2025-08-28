#!/usr/bin/env python3
"""
Script to recreate the database with the correct schema
"""

from app import app, db
import os

def recreate_database():
    """Recreate the database with the correct schema"""
    # Remove existing database file if it exists
    db_path = 'otrs_data.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create new database with app context
    with app.app_context():
        db.create_all()
        print("Database created successfully with new schema")
        
        # Verify the tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables created: {tables}")

if __name__ == '__main__':
    recreate_database()
