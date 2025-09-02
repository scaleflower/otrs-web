"""
User and system-related database models
"""

from datetime import datetime
from . import db

class ResponsibleConfig(db.Model):
    """Responsible configuration table for storing user selections"""
    __tablename__ = 'responsible_config'
    
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(255), index=True)  # User IP address for identification
    selected_responsibles = db.Column(db.Text)  # JSON array of selected responsible names
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ResponsibleConfig {self.user_identifier}>'
    
    def to_dict(self):
        """Convert responsible config to dictionary"""
        return {
            'id': self.id,
            'user_identifier': self.user_identifier,
            'selected_responsibles': self.selected_responsibles,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_config(cls, user_identifier):
        """Get user configuration by identifier"""
        return cls.query.filter_by(user_identifier=user_identifier).first()
    
    def get_selected_responsibles_list(self):
        """Get selected responsibles as a list"""
        if self.selected_responsibles:
            try:
                return eval(self.selected_responsibles)
            except:
                return []
        return []


class DatabaseLog(db.Model):
    """Database operation log table"""
    __tablename__ = 'database_log'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    operation_type = db.Column(db.String(50), index=True)  # Operation type: clear_tickets, upload, delete, update, etc.
    table_name = db.Column(db.String(50), index=True)  # Table name
    records_affected = db.Column(db.Integer)  # Records affected
    operation_details = db.Column(db.Text)  # Operation details
    user_info = db.Column(db.String(255))  # User information (IP, browser, etc.)
    filename = db.Column(db.String(255))  # Related filename (if any)
    
    def __repr__(self):
        return f'<DatabaseLog {self.operation_type}>'
    
    def to_dict(self):
        """Convert database log to dictionary"""
        return {
            'id': self.id,
            'operation_time': self.operation_time.isoformat() if self.operation_time else None,
            'operation_type': self.operation_type,
            'table_name': self.table_name,
            'records_affected': self.records_affected,
            'operation_details': self.operation_details,
            'user_info': self.user_info,
            'filename': self.filename
        }
    
    @classmethod
    def log_operation(cls, operation_type, table_name, records_affected=0, 
                     operation_details='', user_info='', filename=''):
        """Create a new database log entry"""
        log_entry = cls(
            operation_type=operation_type,
            table_name=table_name,
            records_affected=records_affected,
            operation_details=operation_details,
            user_info=user_info,
            filename=filename
        )
        
        try:
            db.session.add(log_entry)
            db.session.commit()
            print(f"✓ Database operation logged: {operation_type} on {table_name}, affected {records_affected} records")
            return log_entry
        except Exception as e:
            print(f"✗ Error logging database operation: {str(e)}")
            db.session.rollback()
            return None
