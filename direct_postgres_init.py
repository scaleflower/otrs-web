#!/usr/bin/env python3
"""
Direct PostgreSQL database initialization script
This script directly connects to PostgreSQL and creates tables.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models after setting up path
from models.ticket import OtrsTicket, UploadDetail
from models.statistics import Statistic, DailyStatistics, StatisticsConfig, StatisticsLog
from models.user import ResponsibleConfig, DatabaseLog
from models.update import AppUpdateStatus
from models.update_log import UpdateLog, UpdateStepLog
from models.system_config import SystemConfig

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

def init_database():
    """Initialize the PostgreSQL database tables directly"""
    # Database configuration
    db_host = 'localhost'
    db_port = '5432'
    db_name = 'heyake'
    db_user = 'heyake'
    db_password = ''
    
    # Create database URI
    db_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    print(f"Connecting to database: {db_uri}")
    
    try:
        # Create engine
        engine = create_engine(db_uri, echo=True)
        
        # Create all tables
        print("Creating all tables...")
        OtrsTicket.metadata.create_all(engine)
        UploadDetail.metadata.create_all(engine)
        Statistic.metadata.create_all(engine)
        DailyStatistics.metadata.create_all(engine)
        StatisticsConfig.metadata.create_all(engine)
        StatisticsLog.metadata.create_all(engine)
        ResponsibleConfig.metadata.create_all(engine)
        DatabaseLog.metadata.create_all(engine)
        AppUpdateStatus.metadata.create_all(engine)
        UpdateLog.metadata.create_all(engine)
        UpdateStepLog.metadata.create_all(engine)
        SystemConfig.metadata.create_all(engine)
        
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    if not success:
        sys.exit(1)