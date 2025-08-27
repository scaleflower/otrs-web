#!/usr/bin/env python3
"""
Debug script to check Statistic model definition
"""

from app import app, db, Statistic
from sqlalchemy import inspect

def debug_statistic_model():
    """Debug Statistic model definition"""
    with app.app_context():
        # Check model definition
        print("Statistic model columns:")
        for column in Statistic.__table__.columns:
            print(f"  - {column.name}: {column.type}")
        
        # Check database table
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nDatabase tables: {tables}")
        
        if 'statistic' in tables:
            print("\nDatabase statistic table columns:")
            columns = inspector.get_columns('statistic')
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        
        # Check if there are any differences
        model_columns = [col.name for col in Statistic.__table__.columns]
        if 'statistic' in tables:
            db_columns = [col['name'] for col in inspector.get_columns('statistic')]
            print(f"\nModel columns: {model_columns}")
            print(f"Database columns: {db_columns}")
            
            missing_in_db = set(model_columns) - set(db_columns)
            missing_in_model = set(db_columns) - set(model_columns)
            
            if missing_in_db:
                print(f"Columns missing in database: {missing_in_db}")
            if missing_in_model:
                print(f"Columns missing in model: {missing_in_model}")

if __name__ == '__main__':
    debug_statistic_model()
