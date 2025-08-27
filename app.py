"""
OTRS Ticket Analysis Web Application
基于Flask的工单数据分析Web应用
"""

from flask import Flask, render_template, request, send_file, jsonify
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

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量存储上传的数据
uploaded_data = {}

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

def analyze_otrs_tickets(df):
    """Main function for OTRS ticket data analysis"""
    # Check for common OTRS column name variants
    possible_columns = {
        'created': ['Created', 'CreateTime', 'Create Time', 'Date Created', 'created', 'creation_date'],
        'closed': ['Closed', 'CloseTime', 'Close Time', 'Date Closed', 'closed', 'close_date'],
        'state': ['State', 'Status', 'Ticket State', 'state', 'status'],
        'ticket_number': ['Ticket Number', 'TicketNumber', 'Number', 'ticket_number', 'id'],
        'priority': ['Priority', 'priority'],
        'firstresponse': ['FirstResponse', 'First Response', 'firstresponse']
    }
    
    # Find actual column names using case-insensitive matching
    actual_columns = {}
    for key, possible_names in possible_columns.items():
        for col in df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                actual_columns[key] = col
                break
    
    # Execute ticket statistical analysis with identified columns
    return analyze_ticket_statistics(df, actual_columns)

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
        
        # Exclude Closed and Resolved states
        if 'state' in columns:
            # Filter out Closed and Resolved states
            not_closed_resolved = ~df[columns['state']].isin(['Closed', 'Resolved'])
            empty_firstresponse = df[(nan_empty | empty_strings) & not_closed_resolved]
        else:
            empty_firstresponse = df[nan_empty | empty_strings]
            
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

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Store the uploaded data
            session_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            uploaded_data[session_id] = df
            
            # Perform analysis
            stats = analyze_otrs_tickets(df)
            
            # Prepare response data
            response_data = {
                'success': True,
                'total_records': len(df),
                'stats': stats,
                'session_id': session_id
            }
            
            return jsonify(response_data)
            
        except Exception as e:
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
            
            # Add age details sheets if session_id is provided
            if 'session_id' in data:
                session_id = data['session_id']
                if session_id in uploaded_data:
                    df = uploaded_data[session_id]
                    
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
                        
                        # Exclude Closed and Resolved states
                        if 'state' in actual_columns:
                            not_closed_resolved = ~df[actual_columns['state']].isin(['Closed', 'Resolved'])
                            empty_firstresponse = df[(nan_empty | empty_strings) & not_closed_resolved]
                        else:
                            empty_firstresponse = df[nan_empty | empty_strings]
                        
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
        if not data or 'age_segment' not in data or 'analysis_data' not in data or 'session_id' not in data:
            return jsonify({'error': 'Missing required data'}), 400
        
        age_segment = data['age_segment']
        session_id = data['session_id']
        
        # Get the stored DataFrame
        if session_id not in uploaded_data:
            return jsonify({'error': 'Session expired or invalid session ID'}), 400
        
        df = uploaded_data[session_id]
        
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
        data = request.get_json()
        if not data or 'session_id' not in data:
            return jsonify({'error': 'Missing session ID'}), 400
        
        session_id = data['session_id']
        
        # Get the stored DataFrame
        if session_id not in uploaded_data:
            return jsonify({'error': 'Session expired or invalid session ID'}), 400
        
        df = uploaded_data[session_id]
        
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
            
            # Exclude Closed and Resolved states
            if 'state' in actual_columns:
                # Filter out Closed and Resolved states
                not_closed_resolved = ~df[actual_columns['state']].isin(['Closed', 'Resolved'])
                empty_firstresponse = df[(nan_empty | empty_strings) & not_closed_resolved]
            else:
                empty_firstresponse = df[nan_empty | empty_strings]
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
        
        # Add age details and empty first response details if session_id is provided
        if 'session_id' in data:
            session_id = data['session_id']
            if session_id in uploaded_data:
                df = uploaded_data[session_id]
                
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
                    
                    # Exclude Closed and Resolved states
                    if 'state' in actual_columns:
                        not_closed_resolved = ~df[actual_columns['state']].isin(['Closed', 'Resolved'])
                        empty_firstresponse = df[(nan_empty | empty_strings) & not_closed_resolved]
                    else:
                        empty_firstresponse = df[nan_empty | empty_strings]
                    
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
