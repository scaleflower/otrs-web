#!/usr/bin/env python3
"""
Force database re-initialization script for PostgreSQL
This script can be used to force re-initialize the database tables 
when using PostgreSQL, even if tables already exist.
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

# Set database type to postgresql if not already set
os.environ.setdefault('DATABASE_TYPE', 'postgresql')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'heyake')
os.environ.setdefault('DB_USER', 'heyake')
os.environ.setdefault('DB_PASSWORD', '')

# Reload config to ensure environment variables are loaded
import config
importlib.reload(config)
from config import Config

from app import app
from models import db, init_db

def force_init_database():
    """Force initialize the database tables"""
    print("Force initializing database...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    try:
        with app.app_context():
            # Drop all tables first
            print("Dropping all existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating all tables...")
            db.create_all()
            
            # Initialize update log models
            from models.update_log import init_update_log_models
            init_update_log_models(app)
            
            # Ensure schema updates for upload_detail table
            from models import _ensure_upload_detail_schema
            _ensure_upload_detail_schema()
            
            created_items = []
            
            # Initialize default configurations if not exists
            from models.statistics import StatisticsConfig
            from models.update import AppUpdateStatus
            
            if not StatisticsConfig.query.first():
                default_config = StatisticsConfig(schedule_time='23:59', enabled=True)
                db.session.add(default_config)
                created_items.append('statistics_config')
            
            # Ensure update status row exists for auto-update workflow
            if not AppUpdateStatus.query.first():
                initial_version = app.config.get('APP_VERSION', '0.0.0')
                update_status = AppUpdateStatus(current_version=initial_version)
                db.session.add(update_status)
                created_items.append('app_update_status')
            
            if created_items:
                db.session.commit()
                print(f"✓ Initialized database defaults: {', '.join(created_items)}")
            
            print("✅ Database force initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to force initialize database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set the database type to postgresql if not already set
    os.environ.setdefault('DATABASE_TYPE', 'postgresql')
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '5432')
    os.environ.setdefault('DB_NAME', 'heyake')
    os.environ.setdefault('DB_USER', 'heyake')
    os.environ.setdefault('DB_PASSWORD', '')
    
    success = force_init_database()
    if not success:
        sys.exit(1)