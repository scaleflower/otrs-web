#!/usr/bin/env python3
"""
Database initialization script for PostgreSQL
This script can be used to initialize the database tables when using PostgreSQL.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set database configuration for PostgreSQL
os.environ['DATABASE_TYPE'] = 'postgresql'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'heyake'
os.environ['DB_USER'] = 'heyake'
os.environ['DB_PASSWORD'] = ''

# Import after setting environment variables
from app import app
from models import db
import importlib

# Reload config to ensure environment variables are used
import config
importlib.reload(config)

def init_database():
    """Initialize the database tables"""
    print("Initializing database...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    try:
        with app.app_context():
            # Create all tables
            print("Creating all tables...")
            db.create_all()
            print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    if not success:
        sys.exit(1)