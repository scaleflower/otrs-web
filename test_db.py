from app import app, db

def test_database():
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Try to create tables
        try:
            db.create_all()
            print("Database tables created successfully!")
            
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
        except Exception as e:
            print(f"Error creating tables: {e}")

if __name__ == "__main__":
    test_database()
