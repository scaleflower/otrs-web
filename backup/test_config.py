#!/usr/bin/env python3
"""
Test script to verify database configuration
"""

from app import app, db, StatisticsConfig

def test_config():
    """Test if StatisticsConfig is properly initialized"""
    with app.app_context():
        config = StatisticsConfig.query.first()
        if config:
            print(f"✓ Default config found: schedule_time={config.schedule_time}, enabled={config.enabled}")
        else:
            print("✗ No StatisticsConfig found")
            return False
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        expected_tables = ['daily_statistics', 'database_log', 'otrs_ticket', 'responsible_config', 
                          'statistic', 'statistics_config', 'statistics_log', 'upload_detail']
        
        print(f"✓ Tables created: {len(tables)} tables")
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (missing)")
                return False
        
        return True

if __name__ == '__main__':
    if test_config():
        print("\n✓ Database configuration test passed!")
    else:
        print("\n✗ Database configuration test failed!")
        exit(1)
