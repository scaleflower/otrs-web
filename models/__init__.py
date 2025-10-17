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
    'SystemConfig'
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


def _is_database_empty():
    """Check if the database is empty (no tables)"""
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        return len(tables) == 0
    except Exception:
        # If any error occurs, assume it needs initialization
        return True


def _tables_exist():
    """Check if the required tables already exist in the database"""
    try:
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        required_tables = {
            'otrs_ticket', 'upload_detail', 'statistic', 'daily_statistics',
            'statistics_config', 'statistics_log', 'responsible_config',
            'database_log', 'system_config'
        }
        return required_tables.issubset(existing_tables)
    except Exception:
        # If any error occurs, assume tables don't exist
        return False


def _create_missing_tables():
    """Create missing tables if any"""
    try:
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        required_tables = {
            'otrs_ticket', 'upload_detail', 'statistic', 'daily_statistics',
            'statistics_config', 'statistics_log', 'responsible_config',
            'database_log', 'system_config'
        }
        missing_tables = required_tables - existing_tables
        
        if missing_tables:
            print(f"🔧 Creating missing tables: {missing_tables}")
            # Create all tables (SQLAlchemy will skip existing ones)
            db.create_all()
            return True
        else:
            print("📋 All required tables already exist")
            return False
    except Exception as e:
        print(f"❌ Error checking/creating tables: {e}")
        return False


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Try to create missing tables instead of skipping all if some exist
        if _create_missing_tables():
            # Ensure schema updates for upload_detail table
            _ensure_upload_detail_schema()

            created_items = []

            # Initialize default configurations if not exists
            if not StatisticsConfig.query.first():
                default_config = StatisticsConfig(schedule_time='23:59', enabled=True)
                db.session.add(default_config)
                created_items.append('statistics_config')

            if created_items:
                db.session.commit()
                print(f"✓ Initialized database defaults: {', '.join(created_items)}")

            print("✓ Database initialized successfully")
        else:
            print("📋 Database tables already exist, skipping creation...")
            # Still ensure schema updates for upload_detail table
            _ensure_upload_detail_schema()

            # Ensure default configurations exist
            created_items = []

            if not StatisticsConfig.query.first():
                default_config = StatisticsConfig(schedule_time='23:59', enabled=True)
                db.session.add(default_config)
                created_items.append('statistics_config')

            if created_items:
                db.session.commit()
                print(f"✓ Added missing database defaults: {', '.join(created_items)}")
