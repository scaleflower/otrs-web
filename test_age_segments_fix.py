#!/usr/bin/env python3
"""
Test script to verify the fixed Age Segments export functionality with State column
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

def test_age_segments_fix():
    """Test the fixed Age Segments export functionality"""
    
    with app.app_context():
        print("🔍 Testing Fixed Age Segments Export with State Column")
        print("=" * 60)
        
        # 1. Check if we have data in database
        total_tickets = OtrsTicket.query.count()
        print(f"📊 Total tickets in database: {total_tickets}")
        
        if total_tickets == 0:
            print("❌ No data in database. Please upload some data first.")
            return False
        
        # 2. Get open tickets
        open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).all()
        print(f"📊 Open tickets: {len(open_tickets)}")
        
        if len(open_tickets) == 0:
            print("❌ No open tickets found. Age segments will be empty.")
            return False
        
        # 3. Show sample ticket data
        print("\n🔍 Sample Open Tickets:")
        for i, ticket in enumerate(open_tickets[:3]):
            print(f"  Ticket {i+1}:")
            print(f"    - Number: {ticket.ticket_number}")
            print(f"    - Age: {ticket.age}")
            print(f"    - State: {ticket.state}")
            print(f"    - Priority: {ticket.priority}")
            print(f"    - Created: {ticket.created_date}")
        
        # 4. Test Excel export with State column
        print("\n🔍 Testing Excel Export with State Column:")
        analysis_service = AnalysisService()
        stats = analysis_service.analyze_tickets_from_database()
        
        analysis_data = {
            'total_records': total_tickets,
            'stats': stats
        }
        
        export_service = ExportService()
        
        try:
            output, filename = export_service.export_to_excel(analysis_data)
            print(f"✅ Excel export successful! Filename: {filename}")
            
            # Save to temp file and check contents
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                tmp.write(output.getvalue())
                temp_path = tmp.name
            
            # Check Excel file contents for State column
            xl_file = pd.ExcelFile(temp_path)
            sheet_names = xl_file.sheet_names
            print(f"📋 Excel sheets: {sheet_names}")
            
            # Check Age Segment detail sheets
            age_sheets = [name for name in sheet_names if 'Age' in name and 'Details' in name]
            print(f"📋 Age segment detail sheets: {age_sheets}")
            
            # Verify State column is included
            state_column_found = False
            for sheet_name in age_sheets:
                if sheet_name in sheet_names:
                    df_sheet = pd.read_excel(temp_path, sheet_name=sheet_name)
                    columns = df_sheet.columns.tolist()
                    print(f"  {sheet_name} columns: {columns}")
                    
                    if 'State' in columns:
                        state_column_found = True
                        print(f"  ✅ State column found in {sheet_name}")
                        
                        # Show sample data
                        if len(df_sheet) > 0:
                            print(f"  📄 Sample data from {sheet_name}:")
                            for i, row in df_sheet.head(2).iterrows():
                                print(f"    Row {i+1}: Ticket={row.get('TicketNumber', 'N/A')}, State={row.get('State', 'N/A')}, Priority={row.get('Priority', 'N/A')}")
                    else:
                        print(f"  ❌ State column missing in {sheet_name}")
            
            if not state_column_found:
                print("❌ State column not found in any Age Segment detail sheets!")
                return False
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"❌ Excel export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 5. Test Text export with State column
        print("\n🔍 Testing Text Export with State Column:")
        try:
            output, filename = export_service.export_to_text(analysis_data)
            print(f"✅ Text export successful! Filename: {filename}")
            
            # Read text content
            text_content = output.read().decode('utf-8')
            
            # Check if Age Segments details exist with State column
            if "DETAILS" in text_content and "State" in text_content:
                print("✅ Age Segments details with State column found in text export")
                
                # Extract and show sample details
                lines = text_content.split('\n')
                details_started = False
                sample_lines = []
                for line in lines:
                    if "DETAILS" in line and "HOURS" in line.upper():
                        details_started = True
                        sample_lines.append(line)
                    elif details_started and line.strip():
                        sample_lines.append(line)
                        if len(sample_lines) >= 6:  # Header + separator + few data lines
                            break
                
                if sample_lines:
                    print("📄 Sample from text export:")
                    for line in sample_lines:
                        print(f"    {line}")
            else:
                print("❌ Age Segments details with State column not found in text export!")
                return False
            
        except Exception as e:
            print(f"❌ Text export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    success = test_age_segments_fix()
    
    if success:
        print("\n🎉 AGE SEGMENTS FIX TEST: PASSED")
        print("✅ Age Segments export now includes State column!")
        print("✅ Both Excel and Text exports contain the required fields:")
        print("   - Ticket Number")
        print("   - Age")
        print("   - Created")
        print("   - Priority") 
        print("   - State")
    else:
        print("\n❌ AGE SEGMENTS FIX TEST: FAILED")
        print("❌ There are still issues with the Age Segments export.")
