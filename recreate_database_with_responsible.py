#!/usr/bin/env python3
"""
Script to completely recreate database with Responsible field included
This will delete existing data and create a fresh database with the latest schema
"""

from app import app, db
import os
import shutil
from datetime import datetime

def recreate_database():
    """Recreate database with latest schema including Responsible field"""
    print("Recreating database with latest schema...")
    
    # Create backup directory if it doesn't exist
    backup_dir = 'database_backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Backup existing database if it exists
    db_path = 'instance/otrs_data.db'
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"otrs_backup_before_recreate_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backup created: {backup_path}")
    
    # Remove existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✓ Removed existing database file")
    
    # Create new database with latest schema
    with app.app_context():
        db.create_all()
        print("✓ New database created with latest schema")
        
        # Verify the responsible column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('otrs_ticket')]
        
        if 'responsible' in columns:
            print("✓ Responsible column successfully created in otrs_ticket table")
        else:
            print("✗ ERROR: Responsible column not found in otrs_ticket table")
            return False
        
        # List all tables
        tables = inspector.get_table_names()
        print(f"✓ Database tables created: {tables}")
        
        return True

def main():
    """Main function"""
    print("=" * 60)
    print("OTRS Database Recreation Script")
    print("=" * 60)
    print("WARNING: This will delete all existing data and create a new database!")
    print("A backup will be created before proceeding.")
    print("=" * 60)
    
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    success = recreate_database()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Database recreation completed successfully!")
        print("The database has been recreated with the latest schema including the Responsible field.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Database recreation failed!")
        print("Please check the error messages above.")
        print("=" * 60)
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
