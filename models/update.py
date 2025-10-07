"""Application update tracking models."""

from datetime import datetime
from . import db


class AppUpdateStatus(db.Model):
    """Track application update status and notifications"""

    __tablename__ = 'app_update_status'

    id = db.Column(db.Integer, primary_key=True)
    current_version = db.Column(db.String(64), nullable=False)
    latest_version = db.Column(db.String(64))
    release_name = db.Column(db.String(255))
    release_body = db.Column(db.Text)
    release_url = db.Column(db.String(512))
    published_at = db.Column(db.DateTime)
    status = db.Column(db.String(32), default='idle')
    notified_at = db.Column(db.DateTime)
    last_checked_at = db.Column(db.DateTime)
    last_update_started_at = db.Column(db.DateTime)
    last_update_completed_at = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Serialize status for API responses"""
        return {
            'current_version': self.current_version,
            'latest_version': self.latest_version,
            'release_name': self.release_name,
            'release_notes': self.release_body,
            'release_url': self.release_url,
            'published_at': self._format_dt(self.published_at),
            'status': self.status,
            'notified_at': self._format_dt(self.notified_at),
            'last_checked_at': self._format_dt(self.last_checked_at),
            'last_update_started_at': self._format_dt(self.last_update_started_at),
            'last_update_completed_at': self._format_dt(self.last_update_completed_at),
            'last_error': self.last_error,
        }

    @staticmethod
    def _format_dt(value):
        if not value:
            return None
        return value.isoformat()
