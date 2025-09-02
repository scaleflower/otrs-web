"""
Export service for handling data export operations
"""

import io
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from models import db, OtrsTicket, StatisticsLog
from utils import generate_filename, get_user_info, parse_age_to_hours

class ExportService:
    """Service for export operations"""
    
    def __init__(self):
        pass
    
    def export_to_excel(self, analysis_data):
        """Export analysis results to Excel with histogram"""
        try:
            if not analysis_data or 'stats' not in analysis_data:
                raise ValueError('No data to export')
            
            stats = analysis_data['stats']
            
            # Create Excel file in memory
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': ['Total Records', 'Current Open Tickets', 'Empty FirstResponse'],
                    'Value': [
                        analysis_data.get('total_records', 0),
                        stats.get('current_open_count', 0),
                        stats.get('empty_firstresponse_count', 0)
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Daily statistics sheet
                if 'daily_new' in stats and 'daily_closed' in stats:
                    daily_data = self._prepare_daily_data(stats)
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
                        {'Age Segment': '≤24 hours', 'Count': stats['age_segments']['age_24h']},
                        {'Age Segment': '24-48 hours', 'Count': stats['age_segments']['age_24_48h']},
                        {'Age Segment': '48-72 hours', 'Count': stats['age_segments']['age_48_72h']},
                        {'Age Segment': '>72 hours', 'Count': stats['age_segments']['age_72h']}
                    ]
                    pd.DataFrame(age_data).to_excel(writer, sheet_name='Age Segments', index=False)
                
                # Add detailed data sheets
                self._add_detailed_sheets(writer)
            
            # Generate histogram if daily data exists
            if 'daily_new' in stats and 'daily_closed' in stats:
                img_buffer = self._generate_histogram(stats['daily_new'], stats['daily_closed'])
                
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
            
            # Log export operation
            from .analysis_service import AnalysisService
            analysis_service = AnalysisService()
            analysis_service.log_statistic_query('export_excel', record_count=1)
            
            return output, generate_filename('otrs_analysis', 'xlsx')
            
        except Exception as e:
            raise Exception(f'Error exporting Excel: {str(e)}')
    
    def export_to_text(self, analysis_data):
        """Export analysis results to text file"""
        try:
            if not analysis_data or 'stats' not in analysis_data:
                raise ValueError('No data to export')
            
            stats = analysis_data['stats']
            
            # Create text content
            content = []
            content.append("=" * 60)
            content.append("OTRS TICKET ANALYSIS REPORT")
            content.append("=" * 60)
            content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            content.append("")
            
            # Summary
            content.append("SUMMARY")
            content.append("-" * 40)
            content.append(f"Total Records: {analysis_data.get('total_records', 0)}")
            content.append(f"Current Open Tickets: {stats.get('current_open_count', 0)}")
            content.append(f"Empty FirstResponse: {stats.get('empty_firstresponse_count', 0)}")
            content.append("")
            
            # Daily statistics
            if 'daily_new' in stats and 'daily_closed' in stats:
                content.append("DAILY STATISTICS")
                content.append("-" * 40)
                all_dates = sorted(set(stats['daily_new'].keys()) | set(stats['daily_closed'].keys()), reverse=True)
                for date in all_dates:
                    new_count = stats['daily_new'].get(date, 0)
                    closed_count = stats['daily_closed'].get(date, 0)
                    content.append(f"{date}: New={new_count}, Closed={closed_count}")
                content.append("")
            
            # Priority distribution
            if 'priority_distribution' in stats:
                content.append("PRIORITY DISTRIBUTION")
                content.append("-" * 40)
                for priority, count in stats['priority_distribution'].items():
                    content.append(f"{priority}: {count}")
                content.append("")
            
            # State distribution
            if 'state_distribution' in stats:
                content.append("STATE DISTRIBUTION")
                content.append("-" * 40)
                for state, count in stats['state_distribution'].items():
                    content.append(f"{state}: {count}")
                content.append("")
            
            # Age segments
            if 'age_segments' in stats:
                content.append("AGE SEGMENTS (Open Tickets)")
                content.append("-" * 40)
                content.append(f"≤24 hours: {stats['age_segments']['age_24h']}")
                content.append(f"24-48 hours: {stats['age_segments']['age_24_48h']}")
                content.append(f"48-72 hours: {stats['age_segments']['age_48_72h']}")
                content.append(f">72 hours: {stats['age_segments']['age_72h']}")
                content.append("")
            
            # Convert to text
            text_content = "\n".join(content)
            
            # Create text file in memory
            output = io.BytesIO()
            output.write(text_content.encode('utf-8'))
            output.seek(0)
            
            # Log export operation
            from .analysis_service import AnalysisService
            analysis_service = AnalysisService()
            analysis_service.log_statistic_query('export_txt', record_count=1)
            
            return output, generate_filename('otrs_analysis', 'txt')
            
        except Exception as e:
            raise Exception(f'Error exporting text file: {str(e)}')
    
    def export_execution_logs(self):
        """Export all execution logs to Excel"""
        try:
            # Get all execution logs
            logs = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).all()

            # Create Excel file in memory
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Create logs data
                logs_data = []
                for log in logs:
                    logs_data.append({
                        'Execution Time': log.execution_time.isoformat() if log.execution_time else '',
                        'Statistic Date': str(log.statistic_date) if log.statistic_date else '',
                        'Age <24h': log.age_24h,
                        'Age 24-48h': log.age_24_48h,
                        'Age 48-72h': log.age_48_72h,
                        'Age 72-96h': log.age_72_96h,
                        'Total Open': log.total_open,
                        'Status': log.status,
                        'Error Message': log.error_message or '',
                        'Created At': log.created_at.isoformat() if log.created_at else ''
                    })

                # Write to Excel
                pd.DataFrame(logs_data).to_excel(writer, sheet_name='Execution Logs', index=False)

            output.seek(0)
            
            return output, generate_filename('execution_logs_export', 'xlsx')

        except Exception as e:
            raise Exception(f'Error exporting execution logs: {str(e)}')
    
    def _prepare_daily_data(self, stats):
        """Prepare daily statistics data for Excel export"""
        daily_data = []
        # Sort dates in ascending order for calculation (starting from earliest)
        all_dates_asc = sorted(set(stats['daily_new'].keys()) | set(stats['daily_closed'].keys()))
        
        # Calculate cumulative Open Tickets in chronological order (starting from earliest date)
        cumulative_open = 0
        daily_open_calculated = {}
        for date in all_dates_asc:
            new_count = stats['daily_new'].get(date, 0)
            closed_count = stats['daily_closed'].get(date, 0)
            cumulative_open = cumulative_open + new_count - closed_count
            daily_open_calculated[date] = cumulative_open
        
        # Sort dates in descending order for output (latest date first)
        all_dates_desc = sorted(set(stats['daily_new'].keys()) | set(stats['daily_closed'].keys()), reverse=True)
        
        for date in all_dates_desc:
            new_count = stats['daily_new'].get(date, 0)
            closed_count = stats['daily_closed'].get(date, 0)
            open_count = daily_open_calculated.get(date, 0)
            
            daily_data.append({
                'Date': date,
                'New Tickets': new_count,
                'Closed Tickets': closed_count,
                'Open Tickets': open_count
            })
        
        return daily_data
    
    def _add_detailed_sheets(self, writer):
        """Add detailed data sheets to Excel export"""
        # Get all tickets from database
        tickets = OtrsTicket.query.all()
        
        if not tickets:
            return
        
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
        
        # Age details sheets
        open_tickets = df[df['Closed'].isna()]
        if not open_tickets.empty:
            open_tickets = open_tickets.copy()
            open_tickets['age_hours'] = open_tickets['Age'].apply(parse_age_to_hours)
            
            # Age segments details
            age_segments_details = {
                '24h': open_tickets[open_tickets['age_hours'] <= 24],
                '24_48h': open_tickets[(open_tickets['age_hours'] > 24) & (open_tickets['age_hours'] <= 48)],
                '48_72h': open_tickets[(open_tickets['age_hours'] > 48) & (open_tickets['age_hours'] <= 72)],
                '72h': open_tickets[open_tickets['age_hours'] > 72]
            }
            
            for segment_name, segment_data in age_segments_details.items():
                if not segment_data.empty:
                    segment_details = segment_data[['TicketNumber', 'Age', 'Created', 'Priority']].copy()
                    sheet_name = f"Age {segment_name.replace('_', '-')} Details"
                    segment_details.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        
        # Empty first response details
        empty_firstresponse = df[
            (df['FirstResponse'].isna() | 
             (df['FirstResponse'] == '') |
             (df['FirstResponse'].astype(str).str.lower() == 'nan')) &
            (~df['State'].isin(['Closed', 'Resolved']))
        ]
        
        if not empty_firstresponse.empty:
            empty_details = empty_firstresponse[['TicketNumber', 'Age', 'Created', 'Priority']].copy()
            empty_details.to_excel(writer, sheet_name='Empty FirstResponse Details', index=False)
    
    def _generate_histogram(self, daily_new, daily_closed, daily_open=None):
        """Generate histogram for daily ticket statistics"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Prepare data
            all_dates = sorted(set(daily_new.keys()) | set(daily_closed.keys()))
            new_counts = [daily_new.get(date, 0) for date in all_dates]
            closed_counts = [daily_closed.get(date, 0) for date in all_dates]
            
            # Calculate open counts if provided
            if daily_open:
                open_counts = [daily_open.get(date, 0) for date in all_dates]
                bar_width = 0.25
                x_pos = range(len(all_dates))
                
                ax.bar([x - bar_width for x in x_pos], new_counts, bar_width, label='New Tickets', alpha=0.8, color='#2ecc71')
                ax.bar(x_pos, closed_counts, bar_width, label='Closed Tickets', alpha=0.8, color='#e74c3c')
                ax.bar([x + bar_width for x in x_pos], open_counts, bar_width, label='Open Tickets', alpha=0.8, color='#3498db')
            else:
                bar_width = 0.4
                x_pos = range(len(all_dates))
                
                ax.bar([x - bar_width/2 for x in x_pos], new_counts, bar_width, label='New Tickets', alpha=0.8, color='#2ecc71')
                ax.bar([x + bar_width/2 for x in x_pos], closed_counts, bar_width, label='Closed Tickets', alpha=0.8, color='#e74c3c')
            
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
        except Exception as e:
            print(f"Warning: Could not generate histogram: {str(e)}")
            return None
