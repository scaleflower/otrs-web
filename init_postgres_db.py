#!/usr/bin/env python3
"""
Database initialization script for PostgreSQL
This script can be used to initialize the database tables when using PostgreSQL.
"""

import os
import sys
import importlib

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables if .env file exists
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Reload config to ensure environment variables are loaded
import config
importlib.reload(config)
from config import Config

from app import app
from models import init_db

def init_database():
    """Initialize the database tables"""
    print("Initializing database...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    try:
        # Initialize the database
        init_db(app)
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    # Set the database type to postgresql if not already set
    os.environ.setdefault('DATABASE_TYPE', 'postgresql')
    
    success = init_database()
    if not success:
        sys.exit(1)