#!/usr/bin/env python3
"""
Test script for Daily Statistics Opening Balance calculation logic
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, OtrsTicket, DailyStatistics
from services.analysis_service import AnalysisService

def create_test_tickets():
    """Create test tickets with different states"""
    
    # Create some test tickets with different states
    test_tickets = [
        # Open tickets (should be counted in opening balance)
        {'ticket_number': 'TST001', 'state': 'Open', 'created_date': datetime.now() - timedelta(days=5)},
        {'ticket_number': 'TST002', 'state': 'Pending', 'created_date': datetime.now() - timedelta(days=4)},
        {'ticket_number': 'TST003', 'state': 'In Progress', 'created_date': datetime.now() - timedelta(days=3)},
        
        # Closed tickets (should NOT be counted in opening balance)
        {'ticket_number': 'TST004', 'state': 'Closed', 'created_date': datetime.now() - timedelta(days=2), 'closed_date': datetime.now() - timedelta(days=1)},
        {'ticket_number': 'TST005', 'state': 'Resolved', 'created_date': datetime.now() - timedelta(days=2), 'closed_date': datetime.now() - timedelta(days=1)},
        {'ticket_number': 'TST006', 'state': 'Cancelled', 'created_date': datetime.now() - timedelta(days=2), 'closed_date': datetime.now() - timedelta(days=1)},
        
        # More open tickets
        {'ticket_number': 'TST007', 'state': 'New', 'created_date': datetime.now() - timedelta(days=1)},
        {'ticket_number': 'TST008', 'state': 'Waiting', 'created_date': datetime.now()},
    ]
    
    for ticket_data in test_tickets:
        ticket = OtrsTicket(
            ticket_number=ticket_data['ticket_number'],
            state=ticket_data['state'],
            created_date=ticket_data['created_date'],
            closed_date=ticket_data.get('closed_date'),
            priority='Normal',
            title=f"Test ticket {ticket_data['ticket_number']}",
            age_hours=24,  # Set default age
            data_source='test_opening_balance.xlsx'
        )
        db.session.add(ticket)
    
    db.session.commit()
    return test_tickets

def test_opening_balance_calculation():
    """Test the Opening Balance calculation logic"""
    
    with app.app_context():
        print("=== Testing Daily Statistics Opening Balance Calculation ===\n")
        
        # Clear existing data completely to ensure we test the first record logic
        print("1. Clearing ALL existing data...")
        from models.statistics import StatisticsLog
        OtrsTicket.query.delete()
        DailyStatistics.query.delete()
        StatisticsLog.query.delete()
        db.session.commit()
        
        # Verify tables are empty
        daily_stats_count = DailyStatistics.query.count()
        print(f"   Daily statistics records after clearing: {daily_stats_count}")
        if daily_stats_count > 0:
            print("   ✗ ERROR: daily_statistics table is not empty!")
            return
        else:
            print("   ✓ daily_statistics table is completely empty - ready for first record test")
        
        # Create test tickets
        print("2. Creating test tickets...")
        test_tickets = create_test_tickets()
        
        # Calculate expected opening balance using closed_date IS NULL (new logic)
        open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).count()
        
        print(f"   Total tickets created: {OtrsTicket.query.count()}")
        print(f"   Open tickets (closed_date IS NULL): {open_tickets}")
        print(f"   Expected opening balance (for first record): {open_tickets}")
        
        # Test first calculation (no previous day data)
        print("\n3. Testing first daily statistics calculation...")
        analysis_service = AnalysisService()
        
        success, message = analysis_service.calculate_daily_age_distribution()
        print(f"   Calculation result: {success} - {message}")
        
        # Get today's statistics
        today = date.today()
        today_stat = DailyStatistics.query.filter_by(statistic_date=today).first()
        
        if today_stat:
            print(f"   Opening Balance (calculated): {today_stat.opening_balance}")
            print(f"   Expected Opening Balance: {open_tickets}")
            print(f"   ✓ Opening balance calculation is {'CORRECT' if today_stat.opening_balance == open_tickets else 'INCORRECT'}")
            print(f"   New tickets: {today_stat.new_tickets}")
            print(f"   Resolved tickets: {today_stat.resolved_tickets}")
            print(f"   Closing Balance: {today_stat.closing_balance}")
        else:
            print("   ✗ No daily statistics created!")
            return
        
        # Test second calculation (should use previous day's closing balance)
        print("\n4. Testing second daily statistics calculation...")
        
        # Create statistics for yesterday manually
        yesterday = today - timedelta(days=1)
        yesterday_stat = DailyStatistics(
            statistic_date=yesterday,
            opening_balance=15,  # Mock value
            closing_balance=20,  # This should become today's new opening balance
            new_tickets=5,
            resolved_tickets=0
        )
        db.session.add(yesterday_stat)
        db.session.commit()
        
        print(f"   Created yesterday's statistics with closing balance: {yesterday_stat.closing_balance}")
        
        # Calculate today's statistics again
        success, message = analysis_service.calculate_daily_age_distribution()
        print(f"   Second calculation result: {success} - {message}")
        
        # Get updated today's statistics
        today_stat = DailyStatistics.query.filter_by(statistic_date=today).first()
        
        if today_stat:
            print(f"   Opening Balance (updated): {today_stat.opening_balance}")
            print(f"   Expected Opening Balance: {yesterday_stat.closing_balance}")
            print(f"   ✓ Opening balance calculation is {'CORRECT' if today_stat.opening_balance == yesterday_stat.closing_balance else 'INCORRECT'}")
        
        # Summary of the logic
        print("\n=== Summary of Opening Balance Logic ===")
        print("✓ First record: Opening Balance = Tickets where closed_date IS NULL")
        print("✓ Subsequent records: Opening Balance = Previous day's Closing Balance")
        
        # Verify the logic with actual data
        print("\n=== Verification ===")
        all_stats = DailyStatistics.query.order_by(DailyStatistics.statistic_date).all()
        
        for i, stat in enumerate(all_stats):
            record_type = "First record" if i == 0 else f"Record {i+1}"
            print(f"{record_type} ({stat.statistic_date}):")
            print(f"  Opening Balance: {stat.opening_balance}")
            print(f"  Closing Balance: {stat.closing_balance}")
            
            if i > 0:
                prev_stat = all_stats[i-1]
                is_correct = stat.opening_balance == prev_stat.closing_balance
                print(f"  ✓ Uses previous closing balance: {'YES' if is_correct else 'NO'}")
        
        print("\n=== Test completed ===")

if __name__ == '__main__':
    test_opening_balance_calculation()
