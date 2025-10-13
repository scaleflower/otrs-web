"""
Database models for OTRS Web Application
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

# Initialize database instance
db = SQLAlchemy()

# Import all models
from .ticket import OtrsTicket, UploadDetail
from .statistics import Statistic, DailyStatistics, StatisticsConfig, StatisticsLog
from .user import ResponsibleConfig, DatabaseLog
from .update import AppUpdateStatus
from .update_log import UpdateLog, UpdateStepLog, init_update_log_models
from .system_config import SystemConfig

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
    'DatabaseLog',
    'AppUpdateStatus',
    'UpdateLog',
    'UpdateStepLog',
    'SystemConfig',
    'init_update_log_models'
]

def _ensure_upload_detail_schema():
    """Ensure upload_detail table has expected columns"""
    try:
        inspector = inspect(db.engine)
        columns = {column['name'] for column in inspector.get_columns('upload_detail')}
        if 'stored_filename' not in columns:
            with db.engine.connect() as connection:
                connection.execute(text('ALTER TABLE upload_detail ADD COLUMN stored_filename TEXT'))
            print('✓ Added stored_filename column to upload_detail table')
    except Exception as exc:
        print(f"⚠️  Unable to verify upload_detail schema: {exc}")


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()

        # Initialize update log models
        init_update_log_models(app)

        # Ensure schema updates for upload_detail table
        _ensure_upload_detail_schema()

        created_items = []

        # Initialize default configurations if not exists
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

        print("✓ Database initialized successfully")
