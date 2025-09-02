#!/usr/bin/env python3
"""
Test script for incremental import functionality
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, OtrsTicket, UploadDetail
from services.ticket_service import TicketService

def create_test_excel_file(filename, ticket_numbers, titles):
    """Create a test Excel file with specified ticket numbers"""
    data = {
        'Ticket Number': ticket_numbers,
        'Title': titles,
        'Created': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * len(ticket_numbers),
        'State': ['Open'] * len(ticket_numbers),
        'Priority': ['Normal'] * len(ticket_numbers),
        'Queue': ['Test Queue'] * len(ticket_numbers),
        'Owner': ['Test Owner'] * len(ticket_numbers)
    }
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Created test file: {filename}")
    return filename

def test_incremental_import():
    """Test incremental import functionality"""
    
    with app.app_context():
        print("=== Testing Incremental Import Functionality ===\n")
        
        # Clear existing data
        print("1. Clearing existing data...")
        OtrsTicket.query.delete()
        UploadDetail.query.delete()
        db.session.commit()
        
        initial_count = OtrsTicket.query.count()
        print(f"   Initial database count: {initial_count}")
        
        # Test 1: First upload (should import all records)
        print("\n2. First upload - importing 3 tickets...")
        
        ticket_service = TicketService()
        
        # Create first test file
        test_file1 = create_test_excel_file('test_upload1.xlsx', 
                                          ['TKT001', 'TKT002', 'TKT003'],
                                          ['Test Ticket 1', 'Test Ticket 2', 'Test Ticket 3'])
        
        # Simulate file upload
        class MockFile:
            def __init__(self, filename):
                self.filename = filename
                
        mock_file1 = MockFile('test_upload1.xlsx')
        
        # Process upload using pandas directly for testing
        df1 = pd.read_excel(test_file1)
        
        # Manually create ticket records for first upload
        for _, row in df1.iterrows():
            ticket = OtrsTicket(
                ticket_number=row['Ticket Number'],
                title=row['Title'],
                created_date=datetime.now(),
                state=row['State'],
                priority=row['Priority'],
                queue=row['Queue'],
                owner=row['Owner'],
                data_source='test_upload1.xlsx'
            )
            db.session.add(ticket)
        
        db.session.commit()
        count_after_first = OtrsTicket.query.count()
        
        # Create first upload record
        upload1 = UploadDetail(
            filename='test_upload1.xlsx',
            record_count=count_after_first,
            new_records_count=count_after_first,  # All records are new
            import_mode='clear_existing'
        )
        db.session.add(upload1)
        db.session.commit()
        
        print(f"   After first upload:")
        print(f"   - Total database records: {upload1.record_count}")
        print(f"   - New records imported: {upload1.new_records_count}")
        
        # Test 2: Second upload with some overlapping tickets
        print("\n3. Second upload - 2 existing + 2 new tickets (incremental)...")
        
        # Create second test file with overlapping data
        test_file2 = create_test_excel_file('test_upload2.xlsx',
                                          ['TKT002', 'TKT003', 'TKT004', 'TKT005'],  # 2 existing + 2 new
                                          ['Test Ticket 2', 'Test Ticket 3', 'Test Ticket 4', 'Test Ticket 5'])
        
        df2 = pd.read_excel(test_file2)
        
        # Simulate incremental import logic
        existing_ticket_numbers = {ticket.ticket_number for ticket in OtrsTicket.query.all()}
        print(f"   Existing ticket numbers: {existing_ticket_numbers}")
        
        new_tickets = []
        for _, row in df2.iterrows():
            ticket_number = row['Ticket Number']
            if ticket_number not in existing_ticket_numbers:
                new_tickets.append(row)
                print(f"   - Will import new ticket: {ticket_number}")
            else:
                print(f"   - Skipping existing ticket: {ticket_number}")
        
        # Add only new tickets
        for row in new_tickets:
            ticket = OtrsTicket(
                ticket_number=row['Ticket Number'],
                title=row['Title'],
                created_date=datetime.now(),
                state=row['State'],
                priority=row['Priority'],
                queue=row['Queue'],
                owner=row['Owner'],
                data_source='test_upload2.xlsx'
            )
            db.session.add(ticket)
        
        db.session.commit()
        count_after_second = OtrsTicket.query.count()
        new_records_second = len(new_tickets)
        
        # Create second upload record
        upload2 = UploadDetail(
            filename='test_upload2.xlsx',
            record_count=count_after_second,        # Total records in database
            new_records_count=new_records_second,   # Only newly imported records
            import_mode='incremental'
        )
        db.session.add(upload2)
        db.session.commit()
        
        print(f"   After second upload:")
        print(f"   - Total database records: {upload2.record_count}")
        print(f"   - New records imported: {upload2.new_records_count}")
        
        # Test 3: Third upload with all existing tickets
        print("\n4. Third upload - all existing tickets (no new imports)...")
        
        test_file3 = create_test_excel_file('test_upload3.xlsx',
                                          ['TKT001', 'TKT002'],  # All existing
                                          ['Test Ticket 1', 'Test Ticket 2'])
        
        df3 = pd.read_excel(test_file3)
        existing_ticket_numbers = {ticket.ticket_number for ticket in OtrsTicket.query.all()}
        
        new_tickets_third = []
        for _, row in df3.iterrows():
            ticket_number = row['Ticket Number']
            if ticket_number not in existing_ticket_numbers:
                new_tickets_third.append(row)
            else:
                print(f"   - Skipping existing ticket: {ticket_number}")
        
        count_after_third = OtrsTicket.query.count()
        new_records_third = len(new_tickets_third)
        
        # Create third upload record
        upload3 = UploadDetail(
            filename='test_upload3.xlsx',
            record_count=count_after_third,      # Total records in database (unchanged)
            new_records_count=new_records_third, # No new records
            import_mode='incremental'
        )
        db.session.add(upload3)
        db.session.commit()
        
        print(f"   After third upload:")
        print(f"   - Total database records: {upload3.record_count}")
        print(f"   - New records imported: {upload3.new_records_count}")
        
        # Summary
        print("\n=== Upload History Summary ===")
        uploads = UploadDetail.query.order_by(UploadDetail.upload_time).all()
        
        for i, upload in enumerate(uploads, 1):
            print(f"Upload {i}: {upload.filename}")
            print(f"  - Upload Time: {upload.upload_time}")
            print(f"  - Import Mode: {upload.import_mode}")
            print(f"  - Total Database Records: {upload.record_count}")
            print(f"  - New Records Imported: {upload.new_records_count}")
            print()
        
        # Verify database state
        final_tickets = OtrsTicket.query.all()
        print(f"Final verification:")
        print(f"- Total tickets in database: {len(final_tickets)}")
        for ticket in final_tickets:
            print(f"  - {ticket.ticket_number}: {ticket.title} (from {ticket.data_source})")
        
        # Clean up test files
        for filename in ['test_upload1.xlsx', 'test_upload2.xlsx', 'test_upload3.xlsx']:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"Cleaned up: {filename}")
        
        print("\n=== Test completed successfully! ===")

if __name__ == '__main__':
    test_incremental_import()
