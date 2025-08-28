#!/usr/bin/env python3
"""
Database Manager for OTRS Web Application
统一管理数据库创建、迁移和备份的脚本
"""

import os
import sys
from datetime import datetime
from app import app, db
from sqlalchemy import inspect

class DatabaseManager:
    """Database management class for OTRS application"""
    
    def __init__(self):
        self.db_path = 'otrs_data.db'
        self.backup_dir = 'database_backups'
        
    def create_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"Created backup directory: {self.backup_dir}")
    
    def backup_database(self):
        """Create a backup of the current database"""
        self.create_backup_directory()
        
        if os.path.exists(self.db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"otrs_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"Database backup created: {backup_path}")
            return backup_path
        else:
            print("No database file found to backup")
            return None
    
    def recreate_database(self, backup=True):
        """Recreate the database with current schema"""
        if backup:
            self.backup_database()
        
        # Remove existing database file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"Removed existing database: {self.db_path}")
        
        # Create new database
        with app.app_context():
            db.create_all()
            print("Database created successfully with new schema")
            
            # Verify tables were created
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables created: {tables}")
            
            # Verify Statistic table has all columns
            if 'statistic' in tables:
                columns = [col['name'] for col in inspector.get_columns('statistic')]
                expected_columns = ['id', 'query_time', 'query_type', 'total_records', 
                                  'current_open_count', 'empty_firstresponse_count', 
                                  'daily_new_count', 'daily_closed_count', 'age_segment', 
                                  'record_count', 'upload_id']
                
                missing_columns = set(expected_columns) - set(columns)
                if missing_columns:
                    print(f"Warning: Missing columns in statistic table: {missing_columns}")
                else:
                    print("✓ Statistic table has all expected columns")
    
    def check_database_schema(self):
        """Check database schema consistency"""
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Database tables: {tables}")
            
            # Check each table structure
            for table_name in tables:
                print(f"\n{table_name} table columns:")
                columns = inspector.get_columns(table_name)
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
    
    def migrate_database(self):
        """Migrate database to new schema (if needed)"""
        print("Database migration functionality would be implemented here")
        print("This would handle schema changes between versions")
    
    def list_backups(self):
        """List all available database backups"""
        self.create_backup_directory()
        
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db') and filename.startswith('otrs_backup_'):
                backup_path = os.path.join(self.backup_dir, filename)
                file_time = os.path.getmtime(backup_path)
                file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                file_size = os.path.getsize(backup_path)
                backups.append({
                    'filename': filename,
                    'path': backup_path,
                    'date': file_date,
                    'size': file_size
                })
        
        if backups:
            print("Available backups:")
            for backup in sorted(backups, key=lambda x: x['date'], reverse=True):
                print(f"  {backup['filename']} - {backup['date']} - {backup['size']} bytes")
        else:
            print("No backups found")
        
        return backups

def main():
    """Main function for database management"""
    manager = DatabaseManager()
    
    if len(sys.argv) < 2:
        print("Usage: python database_manager.py [command]")
        print("Commands:")
        print("  create    - Create new database")
        print("  backup    - Create database backup")
        print("  check     - Check database schema")
        print("  list      - List available backups")
        print("  migrate   - Migrate database schema")
        return
    
    command = sys.argv[1]
    
    if command == 'create':
        backup = len(sys.argv) > 2 and sys.argv[2] == 'nobackup'
        manager.recreate_database(backup=not backup)
    
    elif command == 'backup':
        manager.backup_database()
    
    elif command == 'check':
        manager.check_database_schema()
    
    elif command == 'list':
        manager.list_backups()
    
    elif command == 'migrate':
        manager.migrate_database()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == '__main__':
    main()
