#!/usr/bin/env python3
"""
Simple script to check database status
"""

from app import app, db, OtrsTicket

with app.app_context():
    total_records = OtrsTicket.query.count()
    print(f"Total records in database: {total_records}")
    
    if total_records > 0:
        # Get some basic info
        data_sources = OtrsTicket.query.with_entities(OtrsTicket.data_source).distinct().count()
        print(f"Number of data sources: {data_sources}")
        
        # Get last updated time
        last_ticket = OtrsTicket.query.order_by(OtrsTicket.import_time.desc()).first()
        if last_ticket and last_ticket.import_time:
            print(f"Last updated: {last_ticket.import_time}")
    else:
        print("Database is empty. Please upload an Excel file first.")
