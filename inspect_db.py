from app import app, db
from sqlalchemy import inspect

def inspect_database():
    with app.app_context():
        print("=" * 60)
        print("DATABASE INSPECTION")
        print("=" * 60)
        
        # Get database engine info
        engine = db.engine
        print(f"Database URL: {engine.url}")
        
        # Check if database file exists
        import os
        db_path = 'otrs_data.db'
        if os.path.exists(db_path):
            print(f"Database file exists: {db_path}")
            print(f"Database file size: {os.path.getsize(db_path)} bytes")
        else:
            print(f"Database file does not exist: {db_path}")
        
        # Inspect tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        if tables:
            for table_name in tables:
                print(f"\nTable: {table_name}")
                columns = inspector.get_columns(table_name)
                for column in columns:
                    print(f"  Column: {column['name']} ({column['type']})")
        
        # Check if we can query the tables
        try:
            if 'upload_session' in tables:
                result = db.session.execute(db.select(db.text('SELECT COUNT(*) FROM upload_session'))).scalar()
                print(f"\nUpload sessions count: {result}")
            else:
                print("\nUpload_session table does not exist")
                
            if 'ticket' in tables:
                result = db.session.execute(db.select(db.text('SELECT COUNT(*) FROM ticket'))).scalar()
                print(f"Tickets count: {result}")
            else:
                print("Ticket table does not exist")
                
        except Exception as e:
            print(f"Error querying database: {e}")

if __name__ == "__main__":
    inspect_database()
