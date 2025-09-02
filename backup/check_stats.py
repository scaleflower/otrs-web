#!/usr/bin/env python3
"""
Script to check daily statistics and logs in the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, DailyStatistics, StatisticsLog

with app.app_context():
    print("=== Daily Statistics ===")
    stats = DailyStatistics.query.order_by(DailyStatistics.statistic_date.desc()).all()
    for s in stats:
        print(f"Date: {s.statistic_date}, Opening: {s.opening_balance}, New: {s.new_tickets}, "
              f"Resolved: {s.resolved_tickets}, Closing: {s.closing_balance}")
        print(f"  Age Distribution: <24h: {s.age_lt_24h}, 24-48h: {s.age_24_48h}, "
              f"48-72h: {s.age_48_72h}, 72-96h: {s.age_72_96h}, >96h: {s.age_gt_96h}")
    
    print("\n=== Statistics Logs ===")
    logs = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).all()
    for log in logs:
        print(f"Time: {log.execution_time}, Status: {log.status}, Total Open: {log.total_open}")
        if log.error_message:
            print(f"  Error: {log.error_message}")
