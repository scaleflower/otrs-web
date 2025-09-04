"""
Database backup service for OTRS Web Application
"""

import os
import shutil
import sqlite3
import gzip
from datetime import datetime, timedelta
from pathlib import Path


class BackupService:
    """Service for database backup operations"""
    
    def __init__(self, app=None):
        self.app = app
        self.backup_folder = None
        self.db_path = None
        self.retention_days = 30  # Keep backups for 30 days by default
        
        if app:
            self.backup_folder = app.config.get('BACKUP_FOLDER', 'database_backups')
            self.retention_days = app.config.get('BACKUP_RETENTION_DAYS', 30)
            # Extract database path from SQLALCHEMY_DATABASE_URI
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///'):
                raw_path = db_uri.replace('sqlite:///', '')
                # Handle relative paths properly
                if raw_path.startswith('../'):
                    self.db_path = raw_path.replace('../', '')
                else:
                    self.db_path = raw_path
    
    def create_backup(self, compress=True, include_timestamp=True):
        """
        Create a database backup
        
        Args:
            compress (bool): Whether to compress the backup file
            include_timestamp (bool): Whether to include timestamp in filename
            
        Returns:
            tuple: (success, message, backup_path)
        """
        try:
            # Ensure backup directory exists
            os.makedirs(self.backup_folder, exist_ok=True)
            
            if not self.db_path or not os.path.exists(self.db_path):
                return False, "Database file not found", None
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') if include_timestamp else 'latest'
            base_filename = f"otrs_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_folder, base_filename)
            
            # Create backup using SQLite backup API for consistency
            success, message = self._create_sqlite_backup(backup_path)
            
            if not success:
                return False, message, None
            
            # Compress if requested
            if compress:
                compressed_path = backup_path + '.gz'
                success, message = self._compress_backup(backup_path, compressed_path)
                
                if success:
                    # Remove uncompressed file
                    os.remove(backup_path)
                    backup_path = compressed_path
                else:
                    return False, f"Backup created but compression failed: {message}", backup_path
            
            # Get backup file size
            backup_size = os.path.getsize(backup_path)
            size_mb = round(backup_size / (1024 * 1024), 2)
            
            return True, f"Backup created successfully ({size_mb} MB)", backup_path
            
        except Exception as e:
            return False, f"Error creating backup: {str(e)}", None
    
    def _create_sqlite_backup(self, backup_path):
        """Create SQLite backup using the backup API"""
        try:
            # Connect to source database
            source_conn = sqlite3.connect(self.db_path)
            
            # Connect to backup database
            backup_conn = sqlite3.connect(backup_path)
            
            # Perform backup
            source_conn.backup(backup_conn)
            
            # Close connections
            backup_conn.close()
            source_conn.close()
            
            return True, "SQLite backup completed"
            
        except Exception as e:
            return False, f"SQLite backup failed: {str(e)}"
    
    def _compress_backup(self, source_path, compressed_path):
        """Compress backup file using gzip"""
        try:
            with open(source_path, 'rb') as source_file:
                with gzip.open(compressed_path, 'wb') as compressed_file:
                    shutil.copyfileobj(source_file, compressed_file)
            
            return True, "Compression completed"
            
        except Exception as e:
            return False, f"Compression failed: {str(e)}"
    
    def list_backups(self):
        """
        List all available backups
        
        Returns:
            list: List of backup information dictionaries
        """
        try:
            if not os.path.exists(self.backup_folder):
                return []
            
            backups = []
            backup_files = [f for f in os.listdir(self.backup_folder) 
                          if f.startswith('otrs_backup_') and (f.endswith('.db') or f.endswith('.db.gz'))]
            
            for filename in sorted(backup_files, reverse=True):
                file_path = os.path.join(self.backup_folder, filename)
                file_stat = os.stat(file_path)
                
                # Parse timestamp from filename
                try:
                    if filename.endswith('.db.gz'):
                        timestamp_str = filename.replace('otrs_backup_', '').replace('.db.gz', '')
                    else:
                        timestamp_str = filename.replace('otrs_backup_', '').replace('.db', '')
                    
                    if timestamp_str == 'latest':
                        created_date = datetime.fromtimestamp(file_stat.st_mtime)
                    else:
                        created_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                except:
                    created_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                backup_info = {
                    'filename': filename,
                    'path': file_path,
                    'size_bytes': file_stat.st_size,
                    'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                    'created_date': created_date,
                    'age_days': (datetime.now() - created_date).days,
                    'compressed': filename.endswith('.gz')
                }
                
                backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            print(f"Error listing backups: {str(e)}")
            return []
    
    def cleanup_old_backups(self, retention_days=None):
        """
        Clean up old backup files
        
        Args:
            retention_days (int): Number of days to keep backups (default: self.retention_days)
            
        Returns:
            tuple: (success, message, deleted_count)
        """
        try:
            if retention_days is None:
                retention_days = self.retention_days
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            backups = self.list_backups()
            
            deleted_count = 0
            deleted_files = []
            
            for backup in backups:
                if backup['created_date'] < cutoff_date:
                    try:
                        os.remove(backup['path'])
                        deleted_files.append(backup['filename'])
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting backup {backup['filename']}: {str(e)}")
            
            if deleted_count > 0:
                message = f"Deleted {deleted_count} old backup(s): {', '.join(deleted_files)}"
            else:
                message = "No old backups to delete"
            
            return True, message, deleted_count
            
        except Exception as e:
            return False, f"Error cleaning up backups: {str(e)}", 0
    
    def restore_backup(self, backup_filename):
        """
        Restore database from backup
        
        Args:
            backup_filename (str): Name of backup file to restore
            
        Returns:
            tuple: (success, message)
        """
        try:
            backup_path = os.path.join(self.backup_folder, backup_filename)
            
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Create a backup of current database before restore
            current_backup_success, current_backup_msg, _ = self.create_backup(
                compress=True, 
                include_timestamp=True
            )
            
            if not current_backup_success:
                return False, f"Failed to backup current database before restore: {current_backup_msg}"
            
            # Determine if backup is compressed
            is_compressed = backup_filename.endswith('.gz')
            
            # Prepare temporary file for decompression if needed
            temp_backup_path = backup_path
            if is_compressed:
                temp_backup_path = backup_path.replace('.gz', '_temp')
                success, message = self._decompress_backup(backup_path, temp_backup_path)
                if not success:
                    return False, f"Failed to decompress backup: {message}"
            
            # Restore the database
            try:
                # Close any existing connections (if possible)
                if self.app:
                    with self.app.app_context():
                        from models import db
                        db.engine.dispose()
                
                # Copy backup to database location
                shutil.copy2(temp_backup_path, self.db_path)
                
                # Clean up temporary file if it was created
                if is_compressed and os.path.exists(temp_backup_path):
                    os.remove(temp_backup_path)
                
                return True, f"Database restored successfully from {backup_filename}"
                
            except Exception as e:
                # Clean up temporary file if it was created
                if is_compressed and os.path.exists(temp_backup_path):
                    os.remove(temp_backup_path)
                return False, f"Failed to restore database: {str(e)}"
            
        except Exception as e:
            return False, f"Error restoring backup: {str(e)}"
    
    def _decompress_backup(self, compressed_path, output_path):
        """Decompress a gzipped backup file"""
        try:
            with gzip.open(compressed_path, 'rb') as compressed_file:
                with open(output_path, 'wb') as output_file:
                    shutil.copyfileobj(compressed_file, output_file)
            
            return True, "Decompression completed"
            
        except Exception as e:
            return False, f"Decompression failed: {str(e)}"
    
    def get_backup_stats(self):
        """
        Get backup statistics
        
        Returns:
            dict: Backup statistics
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size_mb': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'compressed_count': 0,
                    'retention_days': self.retention_days
                }
            
            total_size_mb = sum(backup['size_mb'] for backup in backups)
            compressed_count = sum(1 for backup in backups if backup['compressed'])
            
            # Sort by date to find oldest and newest
            sorted_backups = sorted(backups, key=lambda x: x['created_date'])
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size_mb, 2),
                'oldest_backup': sorted_backups[0]['created_date'],
                'newest_backup': sorted_backups[-1]['created_date'],
                'compressed_count': compressed_count,
                'retention_days': self.retention_days
            }
            
        except Exception as e:
            print(f"Error getting backup stats: {str(e)}")
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'compressed_count': 0,
                'retention_days': self.retention_days,
                'error': str(e)
            }
    
    def verify_backup(self, backup_filename):
        """
        Verify backup file integrity
        
        Args:
            backup_filename (str): Name of backup file to verify
            
        Returns:
            tuple: (success, message)
        """
        try:
            backup_path = os.path.join(self.backup_folder, backup_filename)
            
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Check if file is compressed
            is_compressed = backup_filename.endswith('.gz')
            
            # Prepare file for verification
            verify_path = backup_path
            if is_compressed:
                # Create temporary decompressed file
                verify_path = backup_path.replace('.gz', '_verify_temp')
                success, message = self._decompress_backup(backup_path, verify_path)
                if not success:
                    return False, f"Failed to decompress for verification: {message}"
            
            # Try to open and query the database
            try:
                conn = sqlite3.connect(verify_path)
                cursor = conn.cursor()
                
                # Try a simple query to verify database structure
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if not tables:
                    return False, "Backup appears to be empty (no tables found)"
                
                # Try to count records in main table
                table_names = [table[0] for table in tables]
                if 'ticket' in table_names:
                    cursor.execute("SELECT COUNT(*) FROM ticket;")
                    ticket_count = cursor.fetchone()[0]
                    message = f"Backup verified successfully. Found {len(table_names)} tables, {ticket_count} tickets."
                else:
                    message = f"Backup verified successfully. Found {len(table_names)} tables."
                
                conn.close()
                
                # Clean up temporary file if created
                if is_compressed and os.path.exists(verify_path):
                    os.remove(verify_path)
                
                return True, message
                
            except Exception as e:
                # Clean up temporary file if created
                if is_compressed and os.path.exists(verify_path):
                    os.remove(verify_path)
                return False, f"Database verification failed: {str(e)}"
            
        except Exception as e:
            return False, f"Error verifying backup: {str(e)}"
