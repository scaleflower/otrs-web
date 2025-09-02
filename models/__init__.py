"""
Database models for OTRS Web Application
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize database instance
db = SQLAlchemy()

# Import all models
from .ticket import OtrsTicket, UploadDetail
from .statistics import Statistic, DailyStatistics, StatisticsConfig, StatisticsLog
from .user import ResponsibleConfig, DatabaseLog

# Export all models for easy import
__all__ = [
    'db',
    'OtrsTicket',
    'UploadDetail', 
    'Statistic',
    'DailyStatistics',
    'StatisticsConfig',
    'StatisticsLog',
    'ResponsibleConfig',
    'DatabaseLog'
]

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize default configurations if not exists
        if not StatisticsConfig.query.first():
            default_config = StatisticsConfig(schedule_time='23:59', enabled=True)
            db.session.add(default_config)
            db.session.commit()
            print("✓ Default statistics configuration created")
        
        print("✓ Database initialized successfully")
