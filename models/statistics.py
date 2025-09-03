"""
Statistics-related database models
"""

from datetime import datetime, date
from . import db

class Statistic(db.Model):
    """Statistics query record table"""
    __tablename__ = 'statistic'
    
    id = db.Column(db.Integer, primary_key=True)
    query_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    query_type = db.Column(db.String(50), index=True)  # Query type: main_analysis, age_details, empty_firstresponse, export_excel, export_txt
    total_records = db.Column(db.Integer)
    current_open_count = db.Column(db.Integer)
    empty_firstresponse_count = db.Column(db.Integer)
    daily_new_count = db.Column(db.Integer)  # Total new tickets count
    daily_closed_count = db.Column(db.Integer)  # Total closed tickets count
    age_segment = db.Column(db.String(50))  # Age segment (only for age_details queries)
    record_count = db.Column(db.Integer)  # Query result record count
    upload_id = db.Column(db.Integer, db.ForeignKey('upload_detail.id'))
    
    def __repr__(self):
        return f'<Statistic {self.query_type}>'
    
    def to_dict(self):
        """Convert statistic to dictionary"""
        return {
            'id': self.id,
            'query_time': self.query_time.isoformat() if self.query_time else None,
            'query_type': self.query_type,
            'total_records': self.total_records,
            'current_open_count': self.current_open_count,
            'empty_firstresponse_count': self.empty_firstresponse_count,
            'daily_new_count': self.daily_new_count,
            'daily_closed_count': self.daily_closed_count,
            'age_segment': self.age_segment,
            'record_count': self.record_count,
            'upload_id': self.upload_id
        }


class DailyStatistics(db.Model):
    """Daily statistics table"""
    __tablename__ = 'daily_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    statistic_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    opening_balance = db.Column(db.Integer, default=0)  # 00:00的Open数量
    new_tickets = db.Column(db.Integer, default=0)      # 当天新增
    resolved_tickets = db.Column(db.Integer, default=0) # 当天解决
    closing_balance = db.Column(db.Integer, default=0)  # 23:59的Open数量
    
    # Open单年龄分布
    age_lt_24h = db.Column(db.Integer, default=0)
    age_24_48h = db.Column(db.Integer, default=0)
    age_48_72h = db.Column(db.Integer, default=0)
    age_72_96h = db.Column(db.Integer, default=0)
    age_gt_96h = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DailyStatistics {self.statistic_date}>'
    
    def to_dict(self):
        """Convert daily statistics to dictionary"""
        return {
            'id': self.id,
            'date': str(self.statistic_date),
            'opening_balance': self.opening_balance,
            'new_tickets': self.new_tickets,
            'resolved_tickets': self.resolved_tickets,
            'closing_balance': self.closing_balance,
            'age_lt_24h': self.age_lt_24h,
            'age_24_48h': self.age_24_48h,
            'age_48_72h': self.age_48_72h,
            'age_72_96h': self.age_72_96h,
            'age_gt_96h': self.age_gt_96h,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StatisticsConfig(db.Model):
    """Statistics configuration table"""
    __tablename__ = 'statistics_config'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_time = db.Column(db.String(5), default='23:59')  # Format: HH:MM
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StatisticsConfig {self.schedule_time}>'
    
    def to_dict(self):
        """Convert statistics config to dictionary"""
        return {
            'id': self.id,
            'schedule_time': self.schedule_time,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_config(cls):
        """Get current statistics configuration"""
        return cls.query.first() or cls(schedule_time='23:59', enabled=True)


class StatisticsLog(db.Model):
    """Statistics execution log table"""
    __tablename__ = 'statistics_log'
    
    id = db.Column(db.Integer, primary_key=True)
    execution_time = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    statistic_date = db.Column(db.Date, index=True)
    
    # Consistent with DailyStatistics
    opening_balance = db.Column(db.Integer, default=0)
    new_tickets = db.Column(db.Integer, default=0)
    resolved_tickets = db.Column(db.Integer, default=0)
    closing_balance = db.Column(db.Integer, default=0)
    
    age_lt_24h = db.Column(db.Integer, default=0)
    age_24_48h = db.Column(db.Integer, default=0)
    age_48_72h = db.Column(db.Integer, default=0)
    age_72_96h = db.Column(db.Integer, default=0)
    age_gt_96h = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(20), default='success')  # success, error
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StatisticsLog {self.execution_time}>'
    
    def to_dict(self):
        """Convert statistics log to dictionary"""
        return {
            'id': self.id,
            'execution_time': self.execution_time.isoformat() if self.execution_time else None,
            'statistic_date': str(self.statistic_date) if self.statistic_date else None,
            'opening_balance': self.opening_balance,
            'new_tickets': self.new_tickets,
            'resolved_tickets': self.resolved_tickets,
            'closing_balance': self.closing_balance,
            'age_lt_24h': self.age_lt_24h,
            'age_24_48h': self.age_24_48h,
            'age_48_72h': self.age_48_72h,
            'age_72_96h': self.age_72_96h,
            'age_gt_96h': self.age_gt_96h,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
