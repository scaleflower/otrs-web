"""
OTRS Ticket Analysis Web Application
基于Flask的工单数据分析Web应用
"""

from flask import Flask, render_template, request, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
from datetime import datetime
import re
import os
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///otrs_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量存储上传的数据
uploaded_data = {}

# 数据库模型 - 简化为单表结构
class OtrsTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(100), unique=True, nullable=False)
    created_date = db.Column(db.DateTime)
    closed_date = db.Column(db.DateTime)
    state = db.Column(db.String(100))
    priority = db.Column(db.String(50))
    first_response = db.Column(db.String(255))
    age = db.Column(db.String(50))
    age_hours = db.Column(db.Float)
    
    # Excel中的其他常见字段
    queue = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    customer_id = db.Column(db.String(255))
    customer_realname = db.Column(db.String(255))
    title = db.Column(db.Text)
    service = db.Column(db.String(255))
    type = db.Column(db.String(100))
    category = db.Column(db.String(255))
    sub_category = db.Column(db.String(255))
    
    # 元数据
    import_time = db.Column(db.DateTime, default=datetime.utcnow)
    data_source = db.Column(db.String(255))  # 原始文件名
    raw_data = db.Column(db.Text)  # 存储完整的原始JSON数据

# 创建数据库表
with app.app_context():
    db.create_all()

def parse_age_to_hours(age_str):
    """Parse Age string to total hours"""
    if pd.isna(age_str):
        return 0
    
    age_str = str(age_str).lower()
    days = 0
    hours = 0
    minutes = 0
    
    day_match = re.search(r'(\d+)\s*d', age_str)
    if day_match:
        days = int(day_match.group(1))
    
    hour_match = re.search(r'(\d+)\s*h', age_str)
    if hour_match:
        hours = int(hour_match.group(1))
    
    minute_match = re.search(r'(\d+)\s*m', age_str)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    return (days * 24) + hours + (minutes / 60)

def analyze_otrs_tickets_from_db():
    """Main function for OTRS ticket data analysis from database"""
    # Get all tickets from database
    tickets = OtrsTicket.query.all()
    
    if not tickets:
        return {}
    
    # Convert tickets to DataFrame for analysis
    ticket_data = []
    for ticket in tickets:
        ticket_data.append({
            'TicketNumber': ticket.ticket_number,
            'Created': ticket.created_date,
            'Closed': ticket.closed_date,
            'State': ticket.state,
            'Priority': ticket.priority,
            'FirstResponse': ticket.first_response,
            'Age': ticket.age,
            'AgeHours': ticket.age_hours
        })
    
    df = pd.DataFrame(ticket_data)
    
    # Execute ticket statistical analysis
    return analyze_ticket_statistics(df, {
        'ticket_number': 'TicketNumber',
        'created': 'Created',
        'closed': 'Closed',
        'state': 'State',
        'priority': 'Priority',
        'firstresponse': 'FirstResponse',
        'age': 'Age'
    })

def analyze_ticket_statistics(df, columns):
    """Perform ticket statistical analysis"""
    stats = {}
    
    # Convert date columns to datetime format
    if 'created' in columns:
        df['created_date'] = pd.to_datetime(df[columns['created']], errors='coerce')
        daily_new = df['created_date'].dt.date.value_counts().sort_index()
        # Convert date keys to string for JSON serialization
        stats['daily_new'] = {str(date): count for date, count in daily_new.items()}
    
    if 'closed' in columns:
        df['closed_date'] = pd.to_datetime(df[columns['closed']], errors='coerce')
        closed_tickets = df[df['closed_date'].notna()]
        if not closed_tickets.empty:
            daily_closed = closed_tickets['closed_date'].dt.date.value_counts().sort_index()
            # Convert date keys to string for JSON serialization
            stats['daily_closed'] = {str(date): count for date, count in daily_closed.items()}
            
            # Calculate cumulative open tickets if both daily_new and daily_closed exist
            if 'daily_new' in stats and 'daily_closed' in stats:
                daily_open = {}
                cumulative_open = 0
                
                # Get all dates and sort them
                all_dates = sorted(set(stats['daily_new'].keys()) | set(stats['daily_closed'].keys()))
                
                for date in all_dates:
                    new_count = stats['daily_new'].get(date, 0)
                    closed_count = stats['daily_closed'].get(date, 0)
                    cumulative_open = cumulative_open + new_count - closed_count
                    daily_open[date] = cumulative_open
                
                stats['daily_open'] = daily_open
    
    # Current open tickets analysis
    if 'closed' in columns:
        current_open = df[df['closed_date'].isna()]
        stats['current_open_count'] = len(current_open)
        
        # State distribution
        if 'state' in columns:
            state_counts = df[columns['state']].value_counts().to_dict()
            stats['state_distribution'] = state_counts
    
    # Priority distribution
    if 'priority' in columns:
        priority_counts = df[columns['priority']].value_counts().to_dict()
        stats['priority_distribution'] = priority_counts
    
        # FirstResponse empty analysis - exclude Closed and Resolved states
        if 'firstresponse' in columns:
            firstresponse_col = columns['firstresponse']
            nan_empty = df[firstresponse_col].isna()
            empty_strings = df[firstresponse_col] == ''
            nan_strings = df[firstresponse_col].astype(str).str.lower() == 'nan'
            
            # Exclude Closed and Resolved states
            if 'state' in columns:
                # Filter out Closed and Resolved states
                not_closed_resolved = ~df[columns['state']].isin(['Closed', 'Resolved'])
                empty_firstresponse = df[(nan_empty | empty_strings | nan_strings) & not_closed_resolved]
            else:
                empty_firstresponse = df[nan_empty | empty_strings | nan_strings]
                
            stats['empty_firstresponse_count'] = len(empty_firstresponse)
            
            if 'priority' in columns:
                priority_empty_counts = empty_firstresponse[columns['priority']].value_counts().to_dict()
                stats['empty_firstresponse_by_priority'] = priority_empty_counts
    
    # Age analysis if Age column exists
    if 'Age' in df.columns:
        df['age_hours'] = df['Age'].apply(parse_age_to_hours)
        
        # Age分段统计（只统计Open工单）
        if 'closed' in columns:
            open_tickets = df[df['closed_date'].isna()]
            age_segments = {
                'age_24h': len(open_tickets[open_tickets['age_hours'] <= 24]),
                'age_24_48h': len(open_tickets[(open_tickets['age_hours'] > 24) & (open_tickets['age_hours'] <= 48)]),
                'age_48_72h': len(open_tickets[(open_tickets['age_hours'] > 48) & (open_tickets['age_hours'] <= 72)]),
                'age_72h': len(open_tickets[open_tickets['age_hours'] > 72])
            }
            stats['age_segments'] = age_segments
        
        stats['age_analysis'] = {
            'total_tickets': len(df),
            'tickets_with_age': len(df[df['Age'].notna()]),
            'avg_age_hours': df['age_hours'].mean() if not df['age_hours'].empty else 0
        }
    
    return stats

def generate_histogram(daily_new, daily_closed, daily_open=None):
    """Generate histogram for daily ticket statistics"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Prepare data
    all_dates = sorted(set(daily_new.keys()) | set(daily_closed.keys()))
    new_counts = [daily_new.get(date, 0) for date in all_dates]
    closed_counts = [daily_closed.get(date, 0) for date in all_dates]
    
    # Calculate open counts if provided
    if daily_open:
        open_counts = [daily_open.get(date, 0) for date in all_dates]
        bar_width = 0.25
        x_pos = np.arange(len(all_dates))
        
        ax.bar(x_pos - bar_width, new_counts, bar_width, label='New Tickets', alpha=0.8, color='#2ecc71')
        ax.bar(x_pos, closed_counts, bar_width, label='Closed Tickets', alpha=0.8, color='#e74c3c')
        ax.bar(x_pos + bar_width, open_counts, bar_width, label='Open Tickets', alpha=0.8, color='#3498db')
    else:
        bar_width = 0.4
        x_pos = np.arange(len(all_dates))
        
        ax.bar(x_pos - bar_width/2, new_counts, bar_width, label='New Tickets', alpha=0.8, color='#2ecc71')
        ax.bar(x_pos + bar_width/2, closed_counts, bar_width, label='Closed Tickets', alpha=0.8, color='#e74c3c')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Tickets')
    ax.set_title('Daily Ticket Statistics')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(date) for date in all_dates], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/uploads')
def view_uploads():
    """View all uploaded data sources"""
    data_sources = OtrsTicket.query.with_entities(OtrsTicket.data_source, db.func.count(OtrsTicket.id)).group_by(OtrsTicket.data_source).all()
    return render_template('uploads.html', data_sources=data_sources)

@app.route('/upload/<filename>')
def view_upload_details(filename):
    """View details of a specific upload file"""
    tickets = OtrsTicket.query.filter_by(data_source=filename).all()
    return render_template('upload_details.html', filename=filename, tickets=tickets)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get clear existing option from form data
    clear_existing = request.form.get('clear_existing', 'false').lower() == 'true'
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Clear existing data if requested
            if clear_existing:
                OtrsTicket.query.delete()
                print(f"Cleared existing data, importing {len(df)} new records")
            
            # Find actual column names with more comprehensive mapping
            possible_columns = {
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
                'sub_category': ['Sub Category', 'SubCategory', 'sub_category', 'Ticket Sub Category']
            }
            
            actual_columns = {}
            for key, possible_names in possible_columns.items():
                for col in df.columns:
                    if any(name.lower() in col.lower() for name in possible_names):
                        actual_columns[key] = col
                        break
            
            # Save each ticket to database
            new_records_count = 0
            for _, row in df.iterrows():
                # Parse dates
                created_date = None
                closed_date = None
                
                if 'created' in actual_columns:
                    try:
                        created_date = pd.to_datetime(row[actual_columns['created']], errors='coerce')
                        if pd.isna(created_date):
                            created_date = None
                    except:
                        created_date = None
                
                if 'closed' in actual_columns:
                    try:
                        closed_date = pd.to_datetime(row[actual_columns['closed']], errors='coerce')
                        if pd.isna(closed_date):
                            closed_date = None
                    except:
                        closed_date = None
                
                # Parse age to hours
                age_hours = 0
                if 'age' in actual_columns:
                    age_hours = parse_age_to_hours(row[actual_columns['age']])
                
                # Check if ticket already exists (for incremental import)
                ticket_number = str(row[actual_columns.get('ticket_number', '')]) if 'ticket_number' in actual_columns else None
                
                if not clear_existing and ticket_number:
                    existing_ticket = OtrsTicket.query.filter_by(ticket_number=ticket_number).first()
                    if existing_ticket:
                        continue  # Skip existing tickets in incremental mode
                
                # Create ticket record
                ticket = OtrsTicket(
                    ticket_number=ticket_number,
                    created_date=created_date,
                    closed_date=closed_date,
                    state=str(row[actual_columns.get('state', '')]) if 'state' in actual_columns else None,
                    priority=str(row[actual_columns.get('priority', '')]) if 'priority' in actual_columns else None,
                    first_response=str(row[actual_columns.get('firstresponse', '')]) if 'firstresponse' in actual_columns else None,
                    age=str(row[actual_columns.get('age', '')]) if 'age' in actual_columns else None,
                    age_hours=age_hours,
                    queue=str(row[actual_columns.get('queue', '')]) if 'queue' in actual_columns else None,
                    owner=str(row[actual_columns.get('owner', '')]) if 'owner' in actual_columns else None,
                    customer_id=str(row[actual_columns.get('customer_id', '')]) if 'customer_id' in actual_columns else None,
                    customer_realname=str(row[actual_columns.get('customer_realname', '')]) if 'customer_realname' in actual_columns else None,
                    title=str(row[actual_columns.get('title', '')]) if 'title' in actual_columns else None,
                    service=str(row[actual_columns.get('service', '')]) if 'service' in actual_columns else None,
                    type=str(row[actual_columns.get('type', '')]) if 'type' in actual_columns else None,
                    category=str(row[actual_columns.get('category', '')]) if 'category' in actual_columns else None,
                    sub_category=str(row[actual_columns.get('sub_category', '')]) if 'sub_category' in actual_columns else None,
                    data_source=file.filename,
                    raw_data=row.to_json()
                )
                db.session.add(ticket)
                new_records_count += 1
            
            # Commit all database changes
            db.session.commit()
            
            # Perform analysis from database
            stats = analyze_otrs_tickets_from_db()
            
            # Prepare response data
            response_data = {
                'success': True,
                'total_records': len(df),
                'new_records_count': new_records_count,
                'stats': stats,
                'filename': file.filename
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload Excel file (.xlsx or .xls)'}), 400

@app.route('/export/excel', methods=['POST'])
def export_excel():
    """Export analysis results to Excel with histogram"""
    try:
        data = request.get_json()
        if not data or 'stats' not in data:
            return jsonify({'error': 'No data to export'}), 400
        
        stats = data['stats']
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Records', 'Current Open Tickets', 'Empty FirstResponse'],
                'Value': [
                    data.get('total_records', 0),
                    stats.get('current_open_count', 0),
                    stats.get('empty_firstresponse_count', 0)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Daily statistics sheet
            if 'daily_new' in stats and 'daily_closed' in stats:
                daily_data = []
                all_dates = sorted(set(stats['daily_new'].keys()) | set(stats['daily_closed'].keys()), reverse=True)
                
                # Calculate cumulative open tickets
                cumulative_open = 0
                for date in all_dates:
                    new_count = stats['daily_new'].get(date, 0)
                    closed_count = stats['daily_closed'].get(date, 0)
                    cumulative_open = cumulative_open + new_count - closed_count
                    
                    daily_data.append({
                        'Date': date,
                        'New Tickets': new_count,
                        'Closed Tickets': closed_count,
                        'Open Tickets': cumulative_open
                    })
                
                pd.DataFrame(daily_data).to_excel(writer, sheet_name='Daily Statistics', index=False)
            
            # Priority distribution
            if 'priority_distribution' in stats:
                priority_data = [{'Priority': k, 'Count': v} for k, v in stats['priority_distribution'].items()]
                pd.DataFrame(priority_data).to_excel(writer, sheet_name='Priority Distribution', index=False)
            
            # State distribution
            if 'state_distribution' in stats:
                state_data = [{'State': k, 'Count': v} for k, v in stats['state_distribution'].items()]
                pd.DataFrame(state_data).to_excel(writer, sheet_name='State Distribution', index=False)
            
            # Age segments
            if 'age_segments' in stats:
                age_data = [
                    {'Age Segment': '≤24小时', 'Count': stats['age_segments']['age_24h']},
                    {'Age Segment': '24-48小时', 'Count': stats['age_segments']['age_24_48h']},
                    {'Age Segment': '48-72小时', 'Count': stats['age_segments']['age_48_72h']},
                    {'Age Segment': '>72小时', 'Count': stats['age_segments']['age_72h']}
                ]
                pd.DataFrame(age_data).to_excel(writer, sheet_name='Age Segments', index=False)
            
            # Add age details and empty first response details
            # Get all tickets from database
            tickets = OtrsTicket.query.all()
            
            if tickets:
                # Convert tickets to DataFrame
                ticket_data = []
                for ticket in tickets:
                    ticket_data.append({
                        'TicketNumber': ticket.ticket_number,
                        'Created': ticket.created_date,
                        'Closed': ticket.closed_date,
                        'State': ticket.state,
                        'Priority': ticket.priority,
                        'FirstResponse': ticket.first_response,
                        'Age': ticket.age,
                        'AgeHours': ticket.age_hours
                    })
                
                df = pd.DataFrame(ticket_data)
                
                # Find actual column names
                possible_columns = {
                    'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id'],
                    'age': ['Age', 'age'],
                    'created': ['Created', 'CreateTime', 'Create Time', 'Date Created', 'created', 'creation_date'],
                    'priority': ['Priority', 'priority'],
                    'closed': ['Closed', 'CloseTime', 'Close Time', 'Date Closed', 'closed', 'close_date'],
                    'firstresponse': ['FirstResponse', 'First Response', 'firstresponse'],
                    'state': ['State', 'Status', 'Ticket State', 'state', 'status']
                }
                
                actual_columns = {}
                for key, possible_names in possible_columns.items():
                    for col in df.columns:
                        if any(name.lower() in col.lower() for name in possible_names):
                            actual_columns[key] = col
                            break
                
                # Age details sheets
                if 'age' in actual_columns and 'closed' in actual_columns:
                    open_tickets = df[df[actual_columns['closed']].isna()]
                    open_tickets = open_tickets.copy()
                    open_tickets['age_hours'] = open_tickets[actual_columns['age']].apply(parse_age_to_hours)
                    
                    # Age segments details
                    age_segments_details = {
                        '24h': open_tickets[open_tickets['age_hours'] <= 24],
                        '24_48h': open_tickets[(open_tickets['age_hours'] > 24) & (open_tickets['age_hours'] <= 48)],
                        '48_72h': open_tickets[(open_tickets['age_hours'] > 48) & (open_tickets['age_hours'] <= 72)],
                        '72h': open_tickets[open_tickets['age_hours'] > 72]
                    }
                    
                    for segment_name, segment_data in age_segments_details.items():
                        if not segment_data.empty:
                            segment_details = segment_data[[
                                actual_columns.get('ticket_number', 'Ticket Number'),
                                actual_columns.get('age', 'Age'),
                                actual_columns.get('created', 'Created'),
                                actual_columns.get('priority', 'Priority')
                            ]].copy()
                            segment_details.columns = ['Ticket Number', 'Age', 'Created', 'Priority']
                            sheet_name = f"Age {segment_name.replace('_', '-')} Details"
                            pd.DataFrame(segment_details).to_excel(writer, sheet_name=sheet_name[:31], index=False)
                
                # Empty first response details
                if 'firstresponse' in actual_columns:
                    firstresponse_col = actual_columns['firstresponse']
                    nan_empty = df[firstresponse_col].isna()
                    empty_strings = df[firstresponse_col] == ''
                    nan_strings = df[firstresponse_col].astype(str).str.lower() == 'nan'
                    
                    # Exclude Closed and Resolved states
                    if 'state' in actual_columns:
                        not_closed_resolved = ~df[actual_columns['state']].isin(['Closed', 'Resolved'])
                        empty_firstresponse = df[(nan_empty | empty_strings | nan_strings) & not_closed_resolved]
                    else:
                        empty_firstresponse = df[nan_empty | empty_strings | nan_strings]
                    
                    if not empty_firstresponse.empty:
                        empty_details = empty_firstresponse[[
                            actual_columns.get('ticket_number', 'Ticket Number'),
                            actual_columns.get('age', 'Age'),
                            actual_columns.get('created', 'Created'),
                            actual_columns.get('priority', 'Priority')
                        ]].copy()
                        empty_details.columns = ['Ticket Number', 'Age', 'Created', 'Priority']
                        pd.DataFrame(empty_details).to_excel(writer, sheet_name='Empty FirstResponse Details', index=False)
        
        # Generate histogram if daily data exists
        if 'daily_new' in stats and 'daily_closed' in stats:
            img_buffer = generate_histogram(stats['daily_new'], stats['daily_closed'])
            
            # Add histogram to Excel
            from openpyxl import load_workbook
            from openpyxl.drawing.image import Image
            
            output.seek(0)
            wb = load_workbook(output)
            
            # Create new sheet for histogram
            if 'Histogram' in wb.sheetnames:
                ws_hist = wb['Histogram']
            else:
                ws_hist = wb.create_sheet('Histogram')
            
            # Add image
            img = Image(img_buffer)
            img.width = 600
            img.height = 300
            ws_hist.add_image(img, 'A1')
            
            output = io.BytesIO()
            wb.save(output)
        
        output.seek(0)
        filename = f"otrs_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error exporting Excel: {str(e)}'}), 500

@app.route('/age-details', methods=['POST'])
def get_age_details():
    """Get age segment details"""
    try:
        data = request.get_json()
        if not data or 'age_segment' not in data:
            return jsonify({'error': 'Missing required data'}), 400
        
        age_segment = data['age_segment']
        
        # Get all tickets from database
        tickets = OtrsTicket.query.all()
        
        if not tickets:
            return jsonify({'error': 'No tickets found in database'}), 400
        
        # Convert tickets to DataFrame
        ticket_data = []
        for ticket in tickets:
            ticket_data.append({
                'TicketNumber': ticket.ticket_number,
                'Created': ticket.created_date,
                'Closed': ticket.closed_date,
                'State': ticket.state,
                'Priority': ticket.priority,
                'FirstResponse': ticket.first_response,
                'Age': ticket.age,
                'AgeHours': ticket.age_hours
            })
        
        df = pd.DataFrame(ticket_data)
        
        # Find actual column names
        possible_columns = {
            'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id'],
            'age': ['Age', 'age'],
            'created': ['Created', 'CreateTime', 'Create Time', 'Date Created', 'created', 'creation_date'],
            'priority': ['Priority', 'priority'],
            'closed': ['Closed', 'CloseTime', 'Close Time', 'Date Closed', 'closed', 'close_date']
        }
        
        actual_columns = {}
        for key, possible_names in possible_columns.items():
            for col in df.columns:
                if any(name.lower() in col.lower() for name in possible_names):
                    actual_columns[key] = col
                    break
        
        # Filter open tickets
        if 'closed' in actual_columns:
            open_tickets = df[df[actual_columns['closed']].isna()]
        else:
            open_tickets = df
        
        # Filter by age segment
        if 'age' in actual_columns:
            open_tickets = open_tickets.copy()
            open_tickets['age_hours'] = open_tickets[actual_columns['age']].apply(parse_age_to_hours)
            
            if age_segment == '24h':
                filtered_tickets = open_tickets[open_tickets['age_hours'] <= 24]
            elif age_segment == '24_48h':
                filtered_tickets = open_tickets[(open_tickets['age_hours'] > 24) & (open_tickets['age_hours'] <= 48)]
            elif age_segment == '48_72h':
                filtered_tickets = open_tickets[(open_tickets['age_hours'] > 48) & (open_tickets['age_hours'] <= 72)]
            else:  # 72h+
                filtered_tickets = open_tickets[open_tickets['age_hours'] > 72]
        else:
            # If no age column, return empty
            filtered_tickets = pd.DataFrame()
        
        # Prepare details
        details = []
        for _, ticket in filtered_tickets.iterrows():
            detail = {
                'ticket_number': str(ticket[actual_columns.get('ticket_number', 'Ticket Number')]) if 'ticket_number' in actual_columns else 'N/A',
                'age': str(ticket[actual_columns.get('age', 'Age')]) if 'age' in actual_columns else 'N/A',
                'created': str(ticket[actual_columns.get('created', 'Created')]) if 'created' in actual_columns else 'N/A',
                'priority': str(ticket[actual_columns.get('priority', 'Priority')]) if 'priority' in actual_columns else 'N/A'
            }
            details.append(detail)
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting age details: {str(e)}'}), 500

@app.route('/empty-firstresponse-details', methods=['POST'])
def get_empty_firstresponse_details():
    """Get empty first response details"""
    try:
        # Get all tickets from database
        tickets = OtrsTicket.query.all()
        
        if not tickets:
            return jsonify({'error': 'No tickets found in database'}), 400
        
        # Convert tickets to DataFrame
        ticket_data = []
        for ticket in tickets:
            ticket_data.append({
                'TicketNumber': ticket.ticket_number,
                'Created': ticket.created_date,
                'Closed': ticket.closed_date,
                'State': ticket.state,
                'Priority': ticket.priority,
                'FirstResponse': ticket.first_response,
                'Age': ticket.age,
                'AgeHours': ticket.age_hours
            })
        
        df = pd.DataFrame(ticket_data)
        
        # Find actual column names
        possible_columns = {
            'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id'],
            'age': ['Age', 'age'],
            'created': ['Created', 'CreateTime', 'Create Time', 'Date Created', 'created', 'creation_date'],
            'priority': ['Priority', 'priority'],
            'firstresponse': ['FirstResponse', 'First Response', 'firstresponse'],
            'state': ['State', 'Status', 'Ticket State', 'state', 'status'],
            'closed': ['Closed', 'CloseTime', 'Close Time', 'Date Closed', 'closed', 'close_date']
        }
        
        actual_columns = {}
        for key, possible_names in possible_columns.items():
            for col in df.columns:
                if any(name.lower() in col.lower() for name in possible_names):
                    actual_columns[key] = col
                    break
        
        # Filter empty first response tickets
        if 'firstresponse' in actual_columns:
            firstresponse_col = actual_columns['firstresponse']
            nan_empty = df[firstresponse_col].isna()
            empty_strings = df[firstresponse_col] == ''
            nan_strings = df[firstresponse_col].astype(str).str.lower() == 'nan'
            
            # Exclude Closed and Resolved states
            if 'state' in actual_columns:
                # Filter out Closed and Resolved states
                not_closed_resolved = ~df[actual_columns['state']].isin(['Closed', 'Resolved'])
                empty_firstresponse = df[(nan_empty | empty_strings | nan_strings) & not_closed_resolved]
            else:
                empty_firstresponse = df[nan_empty | empty_strings | nan_strings]
        else:
            empty_firstresponse = pd.DataFrame()
        
        # Prepare details
        details = []
        for _, ticket in empty_firstresponse.iterrows():
            detail = {
                'ticket_number': str(ticket[actual_columns.get('ticket_number', 'Ticket Number')]) if 'ticket_number' in actual_columns else 'N/A',
                'age': str(ticket[actual_columns.get('age', 'Age')]) if 'age' in actual_columns else 'N/A',
                'created': str(ticket[actual_columns.get('created', 'Created')]) if 'created' in actual_columns else 'N/A',
                'priority': str(ticket[actual_columns.get('priority', 'Priority')]) if 'priority' in actual_columns else 'N/A'
            }
            details.append(detail)
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting empty first response details: {str(e)}'}), 500

@app.route('/export/txt', methods=['POST'])
def export_txt():
    """Export analysis results to text file"""
    try:
        data = request.get_json()
        if not data or 'stats' not in data:
            return jsonify({'error': 'No data to export'}), 400
        
        stats = data['stats']
        
        # Create text content
        content = []
        content.append("=" * 60)
        content.append("OTRS TICKET ANALYSIS REPORT")
        content.append("=" * 60)
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Total Records: {data.get('total_records', 0)}")
        content.append("")
        
        # Summary
        content.append("SUMMARY")
        content.append("-" * 30)
        content.append(f"Current Open Tickets: {stats.get('current_open_count', 0)}")
        content.append(f"Empty FirstResponse: {stats.get('empty_firstresponse_count', 0)}")
        content.append("")
        
        # Daily statistics
        if 'daily_new' in stats and 'daily_closed' in stats:
            content.append("DAILY STATISTICS")
            content.append("-" * 30)
            content.append("Date\t\tNew\tClosed\tOpen")
            content.append("-" * 30)
            
            all_dates = sorted(set(stats['daily_new'].keys()) | set(stats['daily_closed'].keys()), reverse=True)
            
            # Calculate cumulative open tickets
            cumulative_open = 0
            for date in all_dates:
                new_count = stats['daily_new'].get(date, 0)
                closed_count = stats['daily_closed'].get(date, 0)
                cumulative_open = cumulative_open + new_count - closed_count
                content.append(f"{date}\t{new_count}\t{closed_count}\t{cumulative_open}")
            content.append("")
        
        # Priority distribution
        if 'priority_distribution' in stats:
            content.append("PRIORITY DISTRIBUTION")
            content.append("-" * 30)
            for priority, count in stats['priority_distribution'].items():
                content.append(f"{priority}: {count}")
            content.append("")
        
        # State distribution
        if 'state_distribution' in stats:
            content.append("STATE DISTRIBUTION")
            content.append("-" * 30)
            for state, count in stats['state_distribution'].items():
                content.append(f"{state}: {count}")
            content.append("")
        
        # Empty FirstResponse by priority
        if 'empty_firstresponse_by_priority' in stats:
            content.append("EMPTY FIRSTRESPONSE BY PRIORITY")
            content.append("-" * 30)
            for priority, count in stats['empty_firstresponse_by_priority'].items():
                content.append(f"{priority}: {count}")
            content.append("")
        
        # Age segments
        if 'age_segments' in stats:
            content.append("OPEN工单AGE分段统计")
            content.append("-" * 30)
            content.append(f"≤24小时: {stats['age_segments']['age_24h']}")
            content.append(f"24-48小时: {stats['age_segments']['age_24_48h']}")
            content.append(f"48-72小时: {stats['age_segments']['age_48_72h']}")
            content.append(f">72小时: {stats['age_segments']['age_72h']}")
            content.append("")
        
        # Add age details and empty first response details
        # Get all tickets from database
        tickets = OtrsTicket.query.all()
        
        if tickets:
            # Convert tickets to DataFrame
            ticket_data = []
            for ticket in tickets:
                ticket_data.append({
                    'TicketNumber': ticket.ticket_number,
                    'Created': ticket.created_date,
                    'Closed': ticket.closed_date,
                    'State': ticket.state,
                    'Priority': ticket.priority,
                    'FirstResponse': ticket.first_response,
                    'Age': ticket.age,
                    'AgeHours': ticket.age_hours
                })
            
            df = pd.DataFrame(ticket_data)
            
            # Find actual column names
            possible_columns = {
                'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id'],
                'age': ['Age', 'age'],
                'created': ['Created', 'CreateTime', 'Create Time', 'Date Created', 'created', 'creation_date'],
                'priority': ['Priority', 'priority'],
                'closed': ['Closed', 'CloseTime', 'Close Time', 'Date Closed', 'closed', 'close_date'],
                'firstresponse': ['FirstResponse', 'First Response', 'firstresponse'],
                'state': ['State', 'Status', 'Ticket State', 'state', 'status']
            }
            
            actual_columns = {}
            for key, possible_names in possible_columns.items():
                for col in df.columns:
                    if any(name.lower() in col.lower() for name in possible_names):
                        actual_columns[key] = col
                        break
            
            # Age details
            if 'age' in actual_columns and 'closed' in actual_columns:
                open_tickets = df[df[actual_columns['closed']].isna()]
                open_tickets = open_tickets.copy()
                open_tickets['age_hours'] = open_tickets[actual_columns['age']].apply(parse_age_to_hours)
                
                # Age segments details
                age_segments_details = {
                    '≤24小时': open_tickets[open_tickets['age_hours'] <= 24],
                    '24-48小时': open_tickets[(open_tickets['age_hours'] > 24) & (open_tickets['age_hours'] <= 48)],
                    '48-72小时': open_tickets[(open_tickets['age_hours'] > 48) & (open_tickets['age_hours'] <= 72)],
                    '>72小时': open_tickets[open_tickets['age_hours'] > 72]
                }
                
                for segment_name, segment_data in age_segments_details.items():
                    if not segment_data.empty:
                        content.append(f"{segment_name}工单明细")
                        content.append("-" * 30)
                        content.append("Ticket Number\tAge\tCreated\tPriority")
                        content.append("-" * 30)
                        
                        for _, ticket in segment_data.iterrows():
                            ticket_number = str(ticket[actual_columns.get('ticket_number', 'Ticket Number')]) if 'ticket_number' in actual_columns else 'N/A'
                            age = str(ticket[actual_columns.get('age', 'Age')]) if 'age' in actual_columns else 'N/A'
                            created = str(ticket[actual_columns.get('created', 'Created')]) if 'created' in actual_columns else 'N/A'
                            priority = str(ticket[actual_columns.get('priority', 'Priority')]) if 'priority' in actual_columns else 'N/A'
                            content.append(f"{ticket_number}\t{age}\t{created}\t{priority}")
                        content.append("")
            
                # Empty first response details
                if 'firstresponse' in actual_columns:
                    firstresponse_col = actual_columns['firstresponse']
                    nan_empty = df[firstresponse_col].isna()
                    empty_strings = df[firstresponse_col] == ''
                    nan_strings = df[firstresponse_col].astype(str).str.lower() == 'nan'
                    
                    # Exclude Closed and Resolved states
                    if 'state' in actual_columns:
                        not_closed_resolved = ~df[actual_columns['state']].isin(['Closed', 'Resolved'])
                        empty_firstresponse = df[(nan_empty | empty_strings | nan_strings) & not_closed_resolved]
                    else:
                        empty_firstresponse = df[nan_empty | empty_strings | nan_strings]
                    
                    if not empty_firstresponse.empty:
                        content.append("空FirstResponse工单明细")
                        content.append("-" * 30)
                        content.append("Ticket Number\tAge\tCreated\tPriority")
                        content.append("-" * 30)
                        
                        for _, ticket in empty_firstresponse.iterrows():
                            ticket_number = str(ticket[actual_columns.get('ticket_number', 'Ticket Number')]) if 'ticket_number' in actual_columns else 'N/A'
                            age = str(ticket[actual_columns.get('age', 'Age')]) if 'age' in actual_columns else 'N/A'
                            created = str(ticket[actual_columns.get('created', 'Created')]) if 'created' in actual_columns else 'N/A'
                            priority = str(ticket[actual_columns.get('priority', 'Priority')]) if 'priority' in actual_columns else 'N/A'
                            content.append(f"{ticket_number}\t{age}\t{created}\t{priority}")
                        content.append("")
        
        # Convert to text file
        text_content = "\n".join(content)
        text_buffer = io.BytesIO()
        text_buffer.write(text_content.encode('utf-8'))
        text_buffer.seek(0)
        
        filename = f"otrs_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return send_file(
            text_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error exporting text: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
