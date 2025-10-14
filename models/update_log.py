"""Update log model for tracking detailed update operations"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from . import db


class UpdateLogStatus(Enum):
    """Update log status enumeration"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UpdateLogStep(Enum):
    """Update log step enumeration"""
    BACKUP_DATABASE = "backup_database"
    FETCH_REPOSITORY = "fetch_repository"
    CHECKOUT_VERSION = "checkout_version"
    PULL_CHANGES = "pull_changes"
    INSTALL_DEPENDENCIES = "install_dependencies"
    RUN_MIGRATIONS = "run_migrations"
    RESTART_APPLICATION = "restart_application"


class UpdateLog(db.Model):
    """Model for tracking detailed update operations"""
    
    __tablename__ = 'update_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    update_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    target_version = db.Column(db.String(50), nullable=False)
    current_version = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=UpdateLogStatus.STARTED.value)
    force_reinstall = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(20), nullable=True)  # 更新源 (github, yunxiao)
    
    # Timing information
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Execution details
    total_steps = db.Column(db.Integer, default=0)
    completed_steps = db.Column(db.Integer, default=0)
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)
    
    # File changes
    files_added = db.Column(db.Text, nullable=True)  # JSON string of added files
    files_modified = db.Column(db.Text, nullable=True)  # JSON string of modified files
    files_deleted = db.Column(db.Text, nullable=True)  # JSON string of deleted files
    
    # Git information
    commit_hash = db.Column(db.String(64), nullable=True)
    commit_message = db.Column(db.Text, nullable=True)
    commit_author = db.Column(db.String(255), nullable=True)
    commit_date = db.Column(db.DateTime, nullable=True)
    
    # System information
    system_platform = db.Column(db.String(50), nullable=True)
    python_version = db.Column(db.String(20), nullable=True)
    
    def __init__(self, update_id: str, target_version: str, **kwargs):
        super().__init__(**kwargs)
        self.update_id = update_id
        self.target_version = target_version
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'update_id': self.update_id,
            'target_version': self.target_version,
            'current_version': self.current_version,
            'status': self.status,
            'force_reinstall': self.force_reinstall,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'progress_percentage': self._calculate_progress_percentage(),
            'error_message': self.error_message,
            'error_details': self.error_details,
            'files_added': self._parse_json_field(self.files_added),
            'files_modified': self._parse_json_field(self.files_modified),
            'files_deleted': self._parse_json_field(self.files_deleted),
            'commit_hash': self.commit_hash,
            'commit_message': self.commit_message,
            'commit_author': self.commit_author,
            'commit_date': self.commit_date.isoformat() if self.commit_date else None,
            'system_platform': self.system_platform,
            'python_version': self.python_version,
            'duration_seconds': self._calculate_duration_seconds()
        }
    
    def _calculate_progress_percentage(self) -> int:
        """Calculate progress percentage"""
        if self.total_steps == 0:
            return 0
        return min(100, int((self.completed_steps / self.total_steps) * 100))
    
    def _calculate_duration_seconds(self) -> Optional[int]:
        """Calculate duration in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())
    
    def _parse_json_field(self, field_value: Optional[str]) -> List:
        """Parse JSON field to list"""
        import json
        if not field_value:
            return []
        try:
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_files_changed(self, added: List[str], modified: List[str], deleted: List[str]):
        """Set file change information"""
        import json
        self.files_added = json.dumps(added) if added else None
        self.files_modified = json.dumps(modified) if modified else None
        self.files_deleted = json.dumps(deleted) if deleted else None
    
    def set_commit_info(self, commit_hash: str, message: str, author: str, date: datetime):
        """Set commit information"""
        self.commit_hash = commit_hash
        self.commit_message = message
        self.commit_author = author
        self.commit_date = date
    
    def mark_completed(self):
        """Mark update as completed"""
        self.status = UpdateLogStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.completed_steps = self.total_steps
    
    def mark_failed(self, error_message: str, error_details: Optional[str] = None):
        """Mark update as failed"""
        self.status = UpdateLogStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details


class UpdateStepLog(db.Model):
    """Model for tracking individual update steps"""
    
    __tablename__ = 'update_step_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    update_log_id = db.Column(db.Integer, db.ForeignKey('update_logs.id'), nullable=False, index=True)
    step_name = db.Column(db.String(50), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    
    # Timing information
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Execution details
    status = db.Column(db.String(20), nullable=False, default=UpdateLogStatus.STARTED.value)
    output = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Relationship
    update_log = db.relationship('UpdateLog', backref=db.backref('steps', lazy=True, order_by='UpdateStepLog.step_order'))
    
    def __init__(self, update_log_id: int, step_name: str, step_order: int, **kwargs):
        super().__init__(**kwargs)
        self.update_log_id = update_log_id
        self.step_name = step_name
        self.step_order = step_order
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'update_log_id': self.update_log_id,
            'step_name': self.step_name,
            'step_order': self.step_order,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output': self.output,
            'error_message': self.error_message,
            'duration_seconds': self._calculate_duration_seconds()
        }
    
    def _calculate_duration_seconds(self) -> Optional[int]:
        """Calculate duration in seconds"""
        if not self.started_at or not self.completed_at:
            return None
        return int((self.completed_at - self.started_at).total_seconds())
    
    def mark_completed(self, output: Optional[str] = None):
        """Mark step as completed"""
        self.status = UpdateLogStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.output = output
    
    def mark_failed(self, error_message: str):
        """Mark step as failed"""
        self.status = UpdateLogStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.error_message = error_message


def init_update_log_models(app):
    """Initialize update log models with Flask app"""
    # Database is already initialized in main init_db function
    # This function is kept for backward compatibility
    pass
