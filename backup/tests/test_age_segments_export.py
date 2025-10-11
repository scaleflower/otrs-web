#!/usr/bin/env python3
"""
Test script to verify Age Segments export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, OtrsTicket
from services.export_service import ExportService
from services.analysis_service import AnalysisService
import tempfile
import pandas as pd

def test_age_segments_export():
    """Test Age Segments export functionality"""
    
    with app.app_context():
        print("🔍 Testing Age Segments Export Functionality")
        print("=" * 50)
        
        # 1. Check if we have data in database
        total_tickets = OtrsTicket.query.count()
        print(f"📊 Total tickets in database: {total_tickets}")
        
        if total_tickets == 0:
            print("❌ No data in database. Please upload some data first.")
            return False
        
        # 2. Check open tickets
        open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).all()
        print(f"📊 Open tickets: {len(open_tickets)}")
        
        if len(open_tickets) == 0:
            print("❌ No open tickets found. Age segments will be empty.")
            return False
        
        # 3. Check age hours calculation
        tickets_with_age_hours = [t for t in open_tickets if t.age_hours is not None]
        print(f"📊 Open tickets with age_hours: {len(tickets_with_age_hours)}")
        
        if len(tickets_with_age_hours) == 0:
            print("❌ No tickets have age_hours calculated. This is the problem!")
            
            # Let's check a few tickets manually
            print("\n🔍 Checking sample tickets:")
            for i, ticket in enumerate(open_tickets[:5]):
                print(f"  Ticket {i+1}:")
                print(f"    - Number: {ticket.ticket_number}")
                print(f"    - Age: {ticket.age}")
                print(f"    - Age Hours: {ticket.age_hours}")
                print(f"    - Created: {ticket.created_date}")
            
            return False
        
        # 4. Test analysis service age segments calculation
        print("\n🔍 Testing Analysis Service Age Segments:")
        analysis_service = AnalysisService()
        age_segments = analysis_service._calculate_age_segments()
        print(f"  Age Segments: {age_segments}")
        
        total_age_segments = sum(age_segments.values())
        print(f"  Total in age segments: {total_age_segments}")
        
        if total_age_segments == 0:
            print("❌ Age segments calculation returns zero. This confirms the problem!")
            return False
        
        # 5. Test full analysis
        print("\n🔍 Testing Full Analysis:")
        full_stats = analysis_service.analyze_tickets_from_database()
        if 'age_segments' in full_stats:
            print(f"  Age Segments in full stats: {full_stats['age_segments']}")
        else:
            print("❌ No age_segments in full stats!")
            return False
        
        # 6. Test export functionality
        print("\n🔍 Testing Export Functionality:")
        export_service = ExportService()
        
        # Prepare analysis data for export
        analysis_data = {
            'total_records': total_tickets,
            'stats': full_stats
        }
        
        try:
            output, filename = export_service.export_to_excel(analysis_data)
            print(f"✅ Export successful! Filename: {filename}")
            
            # Save to temp file and check contents
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                tmp.write(output.getvalue())
                temp_path = tmp.name
            
            print(f"📁 Saved to temporary file: {temp_path}")
            
            # Check Excel file contents
            print("\n🔍 Checking Excel file contents:")
            xl_file = pd.ExcelFile(temp_path)
            sheet_names = xl_file.sheet_names
            print(f"  Sheet names: {sheet_names}")
            
            # Look for age segment sheets
            age_sheets = [name for name in sheet_names if 'Age' in name and 'Details' in name]
            print(f"  Age segment detail sheets: {age_sheets}")
            
            if not age_sheets:
                print("❌ No Age segment detail sheets found in export!")
                
                # Check if _add_detailed_sheets was called
                print("\n🔍 Checking if detailed sheets logic works...")
                
                # Import the logic directly
                tickets_data = []
                for ticket in OtrsTicket.query.all():
                    tickets_data.append({
                        'TicketNumber': ticket.ticket_number,
                        'Created': ticket.created_date,
                        'Closed': ticket.closed_date,
                        'State': ticket.state,
                        'Priority': ticket.priority,
                        'FirstResponse': ticket.first_response,
                        'Age': ticket.age,
                        'AgeHours': ticket.age_hours
                    })
                
                df = pd.DataFrame(tickets_data)
                open_tickets_df = df[df['Closed'].isna()]
                print(f"  Open tickets in DataFrame: {len(open_tickets_df)}")
                
                if not open_tickets_df.empty:
                    # Check age_hours parsing
                    from utils.helpers import parse_age_to_hours
                    try:
                        open_tickets_df = open_tickets_df.copy()
                        open_tickets_df['parsed_age_hours'] = open_tickets_df['Age'].apply(parse_age_to_hours)
                        print(f"  Tickets with parsed age hours: {open_tickets_df['parsed_age_hours'].notna().sum()}")
                        
                        # Check segments
                        age_24h = open_tickets_df[open_tickets_df['parsed_age_hours'] <= 24]
                        age_24_48h = open_tickets_df[(open_tickets_df['parsed_age_hours'] > 24) & (open_tickets_df['parsed_age_hours'] <= 48)]
                        age_48_72h = open_tickets_df[(open_tickets_df['parsed_age_hours'] > 48) & (open_tickets_df['parsed_age_hours'] <= 72)]
                        age_72h = open_tickets_df[open_tickets_df['parsed_age_hours'] > 72]
                        
                        print(f"    ≤24h: {len(age_24h)} tickets")
                        print(f"    24-48h: {len(age_24_48h)} tickets")
                        print(f"    48-72h: {len(age_48_72h)} tickets")
                        print(f"    >72h: {len(age_72h)} tickets")
                        
                    except Exception as e:
                        print(f"❌ Error in age parsing: {e}")
                        return False
                
                return False
            else:
                print(f"✅ Found {len(age_sheets)} age segment detail sheets!")
                
                # Check content of age sheets
                for sheet_name in age_sheets:
                    df_sheet = pd.read_excel(temp_path, sheet_name=sheet_name)
                    print(f"  {sheet_name}: {len(df_sheet)} rows")
                
                return True
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    success = test_age_segments_export()
    if success:
        print("\n✅ Age Segments Export Test: PASSED")
    else:
        print("\n❌ Age Segments Export Test: FAILED")
        print("\n💡 The issue is likely in the age_hours calculation or the export logic.")
        print("   Please check:")
        print("   1. Are age_hours being calculated correctly for tickets?")
        print("   2. Is the parse_age_to_hours function working properly?")
        print("   3. Is the _add_detailed_sheets method being called in export?")
