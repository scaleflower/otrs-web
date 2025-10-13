"""
Ticket service for handling ticket-related business logic
"""

import pandas as pd
import os
from datetime import datetime
from flask import request
from werkzeug.utils import secure_filename
from models import db, OtrsTicket, UploadDetail, DatabaseLog
from utils import (
    validate_file, validate_excel_columns, parse_age_to_hours, 
    clean_string_value, get_user_info, update_processing_status
)

class TicketService:
    """Service for ticket operations"""
    
    def __init__(self):
        self.possible_columns = {
            'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id', 'Ticket', 'Ticket ID'],
            'created': ['Created', 'CreateTime', 'Create Time', 'Date Created', 'created', 'creation_date', 'Create Date'],
            'closed': ['Closed', 'CloseTime', 'Close Time', 'Date Closed', 'closed', 'close_date', 'Close Date'],
            'state': ['State', 'Status', 'Ticket State', 'state', 'status', 'Ticket Status'],
            'priority': ['Priority', 'priority', 'Ticket Priority'],
            'firstresponse': ['FirstResponse', 'First Response', 'firstresponse', 'First Reply', 'First Reply Time'],
            'age': ['Age', 'age', 'Ticket Age', 'Age of Ticket'],
            'queue': ['Queue', 'queue', 'Ticket Queue'],
            'owner': ['Owner', 'owner', 'Ticket Owner', 'Assigned To'],
            'customer_id': ['CustomerID', 'Customer ID', 'customer_id', 'Customer'],
            'customer_realname': ['Customer Realname', 'Customer Name', 'Customer Real Name'],
            'title': ['Title', 'title', 'Ticket Title', 'Subject'],
            'service': ['Service', 'service', 'Ticket Service'],
            'type': ['Type', 'type', 'Ticket Type'],
            'category': ['Category', 'category', 'Ticket Category'],
            'sub_category': ['Sub Category', 'SubCategory', 'sub_category', 'Ticket Sub Category'],
            'responsible': ['Responsible', 'responsible', 'Assignee', 'assignee', '处理人', '负责人']
        }
        self.app = None
    
    def initialize(self, app):
        """Initialize service with Flask app"""
        self.app = app
    
    def process_upload(self, file, clear_existing=True):
        """Process uploaded Excel file and import tickets"""
        try:
            # Step 1: Validate file
            update_processing_status(1, 'Start processing Excel file', 'Validating file...')
            is_valid, error_msg = validate_file(file)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Step 1.5: Save uploaded file to uploads directory
            update_processing_status(1, 'Saving uploaded file', 'Saving Excel file to uploads directory...')
            saved_filename = self._save_uploaded_file(file)
            
            # Step 2: Read Excel file
            update_processing_status(2, 'Reading Excel file', 'Loading data into memory...')
            # Reset file pointer to beginning after saving
            file.seek(0)
            
            # Try to read Excel file with different engines and options to handle various Excel issues
            try:
                df = pd.read_excel(file)
            except ValueError as e:
                if "match pattern" in str(e).lower():
                    # This error often occurs when Excel file has filters or other formatting issues
                    # Try with openpyxl engine explicitly
                    file.seek(0)
                    df = pd.read_excel(file, engine='openpyxl')
                else:
                    raise e
            except Exception as e:
                # Try with xlrd engine for older Excel files
                file.seek(0)
                df = pd.read_excel(file, engine='xlrd')
            
            total_records = len(df)
            update_processing_status(2, 'Excel file read completed', f'Found {total_records} records in total')
            
            # Step 3: Validate columns
            is_valid, found_columns = validate_excel_columns(df)
            if not is_valid:
                raise ValueError(found_columns)  # found_columns contains error message
            
            # Step 4: Map column names
            update_processing_status(3, 'Analyzing Excel column structure', 'Identifying ticket data columns...')
            actual_columns = self._map_columns(df.columns)
            
            # Step 5: Clear existing data if requested
            if clear_existing:
                update_processing_status(4, 'Clearing existing data', 'Deleting old records from database...')
                existing_count = self._clear_existing_tickets(file.filename)
            
            # Step 6: Import tickets
            update_processing_status(5, 'Importing data to database', 'Saving ticket records...')
            new_records_count = self._import_tickets(df, actual_columns, file.filename, clear_existing)
            
            # Step 7: Get total database count after import
            total_database_count = OtrsTicket.query.count()
            
            # Step 8: Create upload record
            update_processing_status(6, 'Creating upload record', 'Saving upload details...')
            upload_record = self._create_upload_record(
                file.filename,
                saved_filename,
                new_records_count,
                total_database_count,
                clear_existing
            )
            
            update_processing_status(7, 'Processing completed!', f'Successfully imported {new_records_count} records')
            
            return {
                'success': True,
                'total_records': total_records,
                'new_records_count': new_records_count,
                'total_database_count': total_database_count,
                'upload_id': upload_record.id,
                'filename': file.filename
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _map_columns(self, df_columns):
        """Map DataFrame columns to standard field names"""
        actual_columns = {}
        for key, possible_names in self.possible_columns.items():
            for col in df_columns:
                if any(name.lower() in col.lower() for name in possible_names):
                    actual_columns[key] = col
                    break
        return actual_columns
    
    def _clear_existing_tickets(self, filename):
        """Clear existing tickets and log the operation"""
        existing_count = OtrsTicket.query.count()
        OtrsTicket.query.delete()
        
        # Log operation
        user_ip, user_agent = get_user_info()
        DatabaseLog.log_operation(
            operation_type='clear_tickets',
            table_name='otrs_ticket',
            records_affected=existing_count,
            operation_details='Cleared existing data when uploading file',
            user_info=f"IP: {user_ip}, Browser: {user_agent}",
            filename=filename
        )
        
        return existing_count
    
    def _import_tickets(self, df, actual_columns, filename, clear_existing):
        """Import tickets from DataFrame to database using optimized batch processing"""
        total_records = len(df)
        
        # Prepare data for batch processing
        update_processing_status(5, 'Preparing data for batch import', f'Processing {total_records} records...')
        
        # Process all data at once using vectorized operations
        ticket_data = []
        existing_ticket_numbers = set()
        
        # If incremental import, get existing ticket numbers in one query
        if not clear_existing:
            existing_tickets = OtrsTicket.query.with_entities(OtrsTicket.ticket_number).all()
            existing_ticket_numbers = {ticket.ticket_number for ticket in existing_tickets if ticket.ticket_number}
        
        # Process data using pandas vectorized operations
        for index, (_, row) in enumerate(df.iterrows()):
            # Parse dates
            created_date = self._parse_datetime(row.get(actual_columns.get('created')))
            closed_date = self._parse_datetime(row.get(actual_columns.get('closed')))
            
            # Parse age to hours
            age_hours = 0
            if 'age' in actual_columns:
                age_hours = parse_age_to_hours(row[actual_columns['age']])
            
            # Check if ticket already exists (for incremental import)
            ticket_number = clean_string_value(row.get(actual_columns.get('ticket_number')))
            
            if not clear_existing and ticket_number in existing_ticket_numbers:
                continue  # Skip existing tickets in incremental mode
            
            # Prepare ticket data for batch insert
            ticket_dict = {
                'ticket_number': ticket_number,
                'created_date': created_date,
                'closed_date': closed_date,
                'state': clean_string_value(row.get(actual_columns.get('state'))),
                'priority': clean_string_value(row.get(actual_columns.get('priority'))),
                'first_response': clean_string_value(row.get(actual_columns.get('firstresponse'))),
                'age': clean_string_value(row.get(actual_columns.get('age'))),
                'age_hours': age_hours,
                'queue': clean_string_value(row.get(actual_columns.get('queue'))),
                'owner': clean_string_value(row.get(actual_columns.get('owner'))),
                'customer_id': clean_string_value(row.get(actual_columns.get('customer_id'))),
                'customer_realname': clean_string_value(row.get(actual_columns.get('customer_realname'))),
                'title': clean_string_value(row.get(actual_columns.get('title'))),
                'service': clean_string_value(row.get(actual_columns.get('service'))),
                'type': clean_string_value(row.get(actual_columns.get('type'))),
                'category': clean_string_value(row.get(actual_columns.get('category'))),
                'sub_category': clean_string_value(row.get(actual_columns.get('sub_category'))),
                'responsible': clean_string_value(row.get(actual_columns.get('responsible'))),
                'data_source': filename,
                'raw_data': row.to_json()
            }
            
            ticket_data.append(ticket_dict)
            
            # Update progress less frequently (every 1000 records) for better performance
            if index % 1000 == 0 and index > 0:
                update_processing_status(5, 'Preparing data for import', 
                                       f'Processed {index}/{total_records} records ({int(index / total_records * 100)}%)')
        
        new_records_count = len(ticket_data)
        
        if new_records_count > 0:
            # Batch insert all records at once - much faster than individual inserts
            update_processing_status(5, 'Performing batch database insert', f'Inserting {new_records_count} records...')
            
            # Use bulk_insert_mappings for maximum performance
            db.session.bulk_insert_mappings(OtrsTicket, ticket_data)
            db.session.commit()
            
            update_processing_status(5, 'Database import completed', f'Successfully imported {new_records_count} records')
        else:
            update_processing_status(5, 'No new records to import', 'All records already exist in database')
        
        # Log operation
        user_ip, user_agent = get_user_info()
        DatabaseLog.log_operation(
            operation_type='upload',
            table_name='otrs_ticket',
            records_affected=new_records_count,
            operation_details=f'Imported tickets from Excel file (batch import)',
            user_info=f"IP: {user_ip}, Browser: {user_agent}",
            filename=filename
        )
        
        return new_records_count
    
    def _create_upload_record(self, filename, stored_filename, new_records_count, total_database_count, clear_existing):
        """Create upload detail record with both new and total counts"""
        import_mode = 'clear_existing' if clear_existing else 'incremental'
        safe_stored_filename = stored_filename[:255] if stored_filename else None

        upload_record = UploadDetail(
            filename=filename,
            stored_filename=safe_stored_filename,
            record_count=total_database_count,      # Total records in database after import
            new_records_count=new_records_count,    # Only newly imported records
            import_mode=import_mode
        )
        db.session.add(upload_record)
        db.session.commit()
        return upload_record
    
    def _save_uploaded_file(self, file):
        """Save uploaded file to uploads directory"""
        try:
            # Ensure uploads directory exists
            uploads_dir = 'uploads'
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate safe filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = secure_filename(file.filename)
            
            # Create unique filename
            name, ext = os.path.splitext(safe_filename)
            saved_filename = f"{timestamp}_{name}{ext}"
            
            # Save file
            file_path = os.path.join(uploads_dir, saved_filename)
            file.save(file_path)
            
            print(f"✓ File saved to: {file_path}")
            return saved_filename
            
        except Exception as e:
            print(f"✗ Error saving file: {str(e)}")
            # Don't fail the entire upload if file saving fails
            return file.filename
    
    def _parse_datetime(self, date_value):
        """Parse datetime value safely"""
        if pd.isna(date_value) or date_value is None:
            return None
        
        try:
            parsed_date = pd.to_datetime(date_value, errors='coerce')
            if pd.isna(parsed_date):
                return None
            return parsed_date.to_pydatetime()
        except:
            return None
    
    def get_tickets_by_age_segment(self, age_segment):
        """Get tickets filtered by age segment"""
        open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).all()
        
        filtered_tickets = []
        for ticket in open_tickets:
            if ticket.age_hours is not None:
                if age_segment == '24h' and ticket.age_hours <= 24:
                    filtered_tickets.append(ticket)
                elif age_segment == '24_48h' and 24 < ticket.age_hours <= 48:
                    filtered_tickets.append(ticket)
                elif age_segment == '48_72h' and 48 < ticket.age_hours <= 72:
                    filtered_tickets.append(ticket)
                elif age_segment == '72h' and ticket.age_hours > 72:
                    filtered_tickets.append(ticket)
        
        return filtered_tickets
    
    def get_empty_firstresponse_tickets(self):
        """Get tickets with empty first response"""
        return OtrsTicket.query.filter(
            (OtrsTicket.first_response.is_(None) | 
             (OtrsTicket.first_response == '') |
             (OtrsTicket.first_response == 'nan') |
             (OtrsTicket.first_response == 'NaN')),
            ~OtrsTicket.state.in_(['Closed', 'Resolved'])
        ).all()
    
    def clear_all_tickets(self):
        """Clear all tickets from database"""
        ticket_count = OtrsTicket.query.count()
        if ticket_count == 0:
            return 0, '数据库已经是空的，无需清除'
        
        # Delete all tickets
        OtrsTicket.query.delete()
        db.session.commit()
        
        # Log operation
        user_ip, user_agent = get_user_info()
        DatabaseLog.log_operation(
            operation_type='clear_tickets',
            table_name='otrs_ticket',
            records_affected=ticket_count,
            operation_details='清除所有工单数据',
            user_info=f"IP: {user_ip}, Browser: {user_agent}",
            filename='manual_clear'
        )
        
        return ticket_count, f'成功清除 {ticket_count} 条工单记录'
