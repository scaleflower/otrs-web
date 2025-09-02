#!/usr/bin/env python3
"""
Script to recreate the database with the correct schema
"""

from app import app, db
import os

def recreate_database():
    """Recreate the database with the correct schema"""
    # Ensure db directory exists
    os.makedirs('db', exist_ok=True)
    
    # Note: Database file will be created/updated by db.create_all()
    print("Database directory ready")
    
    # Create new database with app context
    with app.app_context():
        db.create_all()
        print("Database created successfully with new schema")
        
        # Initialize default configuration if not exists
        from app import StatisticsConfig
        if not StatisticsConfig.query.first():
            default_config = StatisticsConfig(schedule_time='23:59', enabled=True)
            db.session.add(default_config)
            db.session.commit()
            print("Default statistics configuration created")
        
        # Verify the tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables created: {tables}")

if __name__ == '__main__':
    recreate_database()
