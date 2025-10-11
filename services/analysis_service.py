"""
Analysis service for handling data analysis and statistics
"""

from datetime import datetime, date, timedelta
from models import db, OtrsTicket, Statistic, DailyStatistics, StatisticsLog
from utils import get_user_info

class AnalysisService:
    """Service for data analysis operations"""
    
    def __init__(self):
        self.app = None
    
    def initialize(self, app):
        """Initialize service with Flask app"""
        self.app = app
    
    def analyze_tickets_from_database(self):
        """Main function for OTRS ticket data analysis from database using SQL queries"""
        stats = {}
        
        # Total records
        total_records = OtrsTicket.query.count()
        stats['total_records'] = total_records
        
        if total_records == 0:
            return stats
        
        # Current open tickets (where closed_date is NULL)
        current_open_count = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).count()
        stats['current_open_count'] = current_open_count
        
        # Empty first response (where first_response is NULL or empty, and state is not Closed/Resolved)
        empty_firstresponse_count = OtrsTicket.query.filter(
            (OtrsTicket.first_response.is_(None) | 
             (OtrsTicket.first_response == '') |
             (OtrsTicket.first_response == 'nan') |
             (OtrsTicket.first_response == 'NaN')),
            ~OtrsTicket.state.in_(['Closed', 'Resolved'])
        ).count()
        stats['empty_firstresponse_count'] = empty_firstresponse_count
        
        # Daily new tickets count
        daily_new = db.session.query(
            db.func.date(OtrsTicket.created_date).label('date'),
            db.func.count(OtrsTicket.id).label('count')
        ).filter(OtrsTicket.created_date.isnot(None)).group_by(db.func.date(OtrsTicket.created_date)).all()
        
        stats['daily_new'] = {str(record.date): record.count for record in daily_new}
        
        # Daily closed tickets count
        daily_closed = db.session.query(
            db.func.date(OtrsTicket.closed_date).label('date'),
            db.func.count(OtrsTicket.id).label('count')
        ).filter(OtrsTicket.closed_date.isnot(None)).group_by(db.func.date(OtrsTicket.closed_date)).all()
        
        stats['daily_closed'] = {str(record.date): record.count for record in daily_closed}
        
        # Calculate cumulative open tickets
        if stats['daily_new'] and stats['daily_closed']:
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
        
        # Priority distribution
        priority_distribution = db.session.query(
            OtrsTicket.priority,
            db.func.count(OtrsTicket.id).label('count')
        ).filter(OtrsTicket.priority.isnot(None)).group_by(OtrsTicket.priority).all()
        
        stats['priority_distribution'] = {record.priority: record.count for record in priority_distribution}
        
        # State distribution
        state_distribution = db.session.query(
            OtrsTicket.state,
            db.func.count(OtrsTicket.id).label('count')
        ).filter(OtrsTicket.state.isnot(None)).group_by(OtrsTicket.state).all()
        
        stats['state_distribution'] = {record.state: record.count for record in state_distribution}
        
        # Age segments for open tickets
        age_segments = self._calculate_age_segments()
        stats['age_segments'] = age_segments
        
        # Empty first response by priority
        empty_fr_by_priority = db.session.query(
            OtrsTicket.priority,
            db.func.count(OtrsTicket.id).label('count')
        ).filter(
            (OtrsTicket.first_response.is_(None) | 
             (OtrsTicket.first_response == '') |
             (OtrsTicket.first_response == 'nan') |
             (OtrsTicket.first_response == 'NaN')),
            ~OtrsTicket.state.in_(['Closed', 'Resolved']),
            OtrsTicket.priority.isnot(None)
        ).group_by(OtrsTicket.priority).all()
        
        stats['empty_firstresponse_by_priority'] = {record.priority: record.count for record in empty_fr_by_priority}
        
        return stats
    
    def _calculate_age_segments(self):
        """Calculate age segments for open tickets"""
        open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).all()
        
        age_segments = {
            'age_24h': 0,
            'age_24_48h': 0,
            'age_48_72h': 0,
            'age_72h': 0
        }
        
        for ticket in open_tickets:
            if ticket.age_hours is not None:
                if ticket.age_hours <= 24:
                    age_segments['age_24h'] += 1
                elif ticket.age_hours <= 48:
                    age_segments['age_24_48h'] += 1
                elif ticket.age_hours <= 72:
                    age_segments['age_48_72h'] += 1
                else:
                    age_segments['age_72h'] += 1
        
        return age_segments
    
    def calculate_daily_age_distribution(self):
        """Calculate age distribution for open tickets and daily statistics"""
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            # Get yesterday's closing balance (today's opening balance)
            yesterday_stat = DailyStatistics.query.filter_by(statistic_date=yesterday).first()
            
            if yesterday_stat:
                # For subsequent records: use previous day's closing balance
                opening_balance = yesterday_stat.closing_balance
            else:
                # For the first record: calculate from current otrs_ticket table
                # Use closed_date IS NULL for consistency with closing balance
                opening_balance = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).count()
            
            # Get today's new tickets (created today)
            new_tickets = OtrsTicket.query.filter(
                db.func.date(OtrsTicket.created_date) == today
            ).count()
            
            # Get today's resolved tickets (closed today)
            resolved_tickets = OtrsTicket.query.filter(
                db.func.date(OtrsTicket.closed_date) == today
            ).count()
            
            # Get current open tickets for closing balance
            open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).all()
            closing_balance = len(open_tickets)
            
            # Calculate age distribution for open tickets
            age_lt_24h = 0
            age_24_48h = 0
            age_48_72h = 0
            age_72_96h = 0
            age_gt_96h = 0
            
            for ticket in open_tickets:
                if ticket.age_hours is not None:
                    if ticket.age_hours < 24:
                        age_lt_24h += 1
                    elif ticket.age_hours < 48:
                        age_24_48h += 1
                    elif ticket.age_hours < 72:
                        age_48_72h += 1
                    elif ticket.age_hours < 96:
                        age_72_96h += 1
                    else:
                        age_gt_96h += 1
            
            # Create or update daily statistics
            daily_stat = DailyStatistics.query.filter_by(statistic_date=today).first()
            if not daily_stat:
                daily_stat = DailyStatistics(statistic_date=today)
                db.session.add(daily_stat)
            
            # Update all statistics
            daily_stat.opening_balance = opening_balance
            daily_stat.new_tickets = new_tickets
            daily_stat.resolved_tickets = resolved_tickets
            daily_stat.closing_balance = closing_balance
            daily_stat.age_lt_24h = age_lt_24h
            daily_stat.age_24_48h = age_24_48h
            daily_stat.age_48_72h = age_48_72h
            daily_stat.age_72_96h = age_72_96h
            daily_stat.age_gt_96h = age_gt_96h
            daily_stat.updated_at = datetime.utcnow()
            
            # Log the execution with local time
            from datetime import timezone
            local_tz = timezone(timedelta(hours=8))  # Asia/Shanghai UTC+8
            local_time = datetime.now(local_tz).replace(tzinfo=None)  # Remove timezone info for storage
            
            existing_log = StatisticsLog.query.filter(
                StatisticsLog.statistic_date == today,
                StatisticsLog.status == 'success'
            ).order_by(StatisticsLog.execution_time.desc()).first()

            if existing_log:
                existing_log.execution_time = local_time
                existing_log.opening_balance = opening_balance
                existing_log.new_tickets = new_tickets
                existing_log.resolved_tickets = resolved_tickets
                existing_log.closing_balance = closing_balance
                existing_log.age_lt_24h = age_lt_24h
                existing_log.age_24_48h = age_24_48h
                existing_log.age_48_72h = age_48_72h
                existing_log.age_72_96h = age_72_96h
                existing_log.age_gt_96h = age_gt_96h
                existing_log.error_message = None
                existing_log.status = 'success'
                existing_log.created_at = datetime.utcnow()
            else:
                log_entry = StatisticsLog(
                    execution_time=local_time,
                    statistic_date=today,
                    opening_balance=opening_balance,
                    new_tickets=new_tickets,
                    resolved_tickets=resolved_tickets,
                    closing_balance=closing_balance,
                    age_lt_24h=age_lt_24h,
                    age_24_48h=age_24_48h,
                    age_48_72h=age_48_72h,
                    age_72_96h=age_72_96h,
                    age_gt_96h=age_gt_96h,
                    status='success'
                )
                db.session.add(log_entry)
            
            db.session.commit()
            print(f"✓ Daily statistics calculated for {today}: "
                  f"Opening: {opening_balance}, New: {new_tickets}, "
                  f"Resolved: {resolved_tickets}, Closing: {closing_balance}, "
                  f"Age <24h: {age_lt_24h}, 24-48h: {age_24_48h}, "
                  f"48-72h: {age_48_72h}, 72-96h: {age_72_96h}, >96h: {age_gt_96h}")
            
            return True, "Daily statistics calculated successfully"
            
        except Exception as e:
            error_msg = f"Error calculating daily statistics: {str(e)}"
            print(f"✗ {error_msg}")
            
            # Log error
            try:
                log_entry = StatisticsLog(
                    statistic_date=date.today(),
                    status='error',
                    error_message=str(e)
                )
                db.session.add(log_entry)
                db.session.commit()
            except:
                pass
            
            db.session.rollback()
            return False, error_msg
    
    def get_responsible_statistics(self, selected_responsibles, period='total'):
        """Get statistics for selected responsible persons with period filtering"""
        if not selected_responsibles:
            return {}
        
        # Get date filters based on period
        date_filters = self._get_period_filters(period)
        
        stats = {}
        
        # Build base query with period filtering
        base_query = OtrsTicket.query.filter(
            OtrsTicket.responsible.in_(selected_responsibles),
            OtrsTicket.closed_date.isnot(None)
        )
        if date_filters:
            base_query = base_query.filter(*date_filters)

        # Total tickets by responsible (within period)
        total_by_responsible = db.session.query(
            OtrsTicket.responsible,
            db.func.count(OtrsTicket.id).label('count')
        ).filter(
            OtrsTicket.responsible.in_(selected_responsibles),
            OtrsTicket.closed_date.isnot(None)
        )

        if date_filters:
            total_by_responsible = total_by_responsible.filter(*date_filters)
        
        total_by_responsible = total_by_responsible.group_by(OtrsTicket.responsible).all()
        stats['total_by_responsible'] = {record.responsible: record.count for record in total_by_responsible}
        
        # Open tickets by responsible (always current open tickets, regardless of period)
        open_by_responsible = db.session.query(
            OtrsTicket.responsible,
            db.func.count(OtrsTicket.id).label('count')
        ).filter(
            OtrsTicket.responsible.in_(selected_responsibles),
            OtrsTicket.closed_date.is_(None)
        ).group_by(OtrsTicket.responsible).all()
        
        stats['open_by_responsible'] = {record.responsible: record.count for record in open_by_responsible}
        
        # Age distribution for open tickets by responsible (always current)
        age_distribution = {}
        for responsible in selected_responsibles:
            open_tickets = OtrsTicket.query.filter(
                OtrsTicket.responsible == responsible,
                OtrsTicket.closed_date.is_(None)
            ).all()
            
            age_24h = 0
            age_24_48h = 0
            age_48_72h = 0
            age_72h = 0
            
            for ticket in open_tickets:
                if ticket.age_hours is not None:
                    if ticket.age_hours <= 24:
                        age_24h += 1
                    elif ticket.age_hours <= 48:
                        age_24_48h += 1
                    elif ticket.age_hours <= 72:
                        age_48_72h += 1
                    else:
                        age_72h += 1
            
            age_distribution[responsible] = {
                'age_24h': age_24h,
                'age_24_48h': age_24_48h,
                'age_48_72h': age_48_72h,
                'age_72h': age_72h
            }
        
        stats['age_distribution'] = age_distribution
        
        # Add period-specific statistics for summary table
        if period != 'total':
            stats['period_stats'] = self._get_period_specific_stats(selected_responsibles, period)
        
        return stats
    
    def _get_period_filters(self, period):
        """Get date filters based on period selection"""
        # For period statistics, we don't filter by date - we want all data
        # The filtering will be done in the period-specific grouping
        return None
    
    def _get_period_specific_stats(self, selected_responsibles, period):
        """Get period-specific statistics breakdown - shows all data grouped by period"""
        from datetime import datetime, timedelta
        
        stats = {}
        
        if period == 'day':
            # Group all data by day
            daily_data = db.session.query(
                db.func.date(OtrsTicket.closed_date).label('date'),
                OtrsTicket.responsible,
                db.func.count(OtrsTicket.id).label('count')
            ).filter(
                OtrsTicket.responsible.in_(selected_responsibles),
                OtrsTicket.closed_date.isnot(None)
            ).group_by(
                db.func.date(OtrsTicket.closed_date),
                OtrsTicket.responsible
            ).order_by(db.func.date(OtrsTicket.closed_date).desc()).all()
            
            # Organize data by date
            for record in daily_data:
                date_str = str(record.date)
                if date_str not in stats:
                    stats[date_str] = {}
                stats[date_str][record.responsible] = record.count
                
        elif period == 'week':
            # Group all data by week
            # Use PostgreSQL/MySQL compatible week calculation
            weekly_data = db.session.query(
                db.func.strftime('%Y-%W', OtrsTicket.closed_date).label('week'),
                OtrsTicket.responsible,
                db.func.count(OtrsTicket.id).label('count')
            ).filter(
                OtrsTicket.responsible.in_(selected_responsibles),
                OtrsTicket.closed_date.isnot(None)
            ).group_by(
                db.func.strftime('%Y-%W', OtrsTicket.closed_date),
                OtrsTicket.responsible
            ).order_by(db.func.strftime('%Y-%W', OtrsTicket.closed_date).desc()).all()
            
            # Organize data by week
            for record in weekly_data:
                week_str = f"第{record.week}周"
                if week_str not in stats:
                    stats[week_str] = {}
                stats[week_str][record.responsible] = record.count
                
        elif period == 'month':
            # Group all data by month
            monthly_data = db.session.query(
                db.func.strftime('%Y-%m', OtrsTicket.closed_date).label('month'),
                OtrsTicket.responsible,
                db.func.count(OtrsTicket.id).label('count')
            ).filter(
                OtrsTicket.responsible.in_(selected_responsibles),
                OtrsTicket.closed_date.isnot(None)
            ).group_by(
                db.func.strftime('%Y-%m', OtrsTicket.closed_date),
                OtrsTicket.responsible
            ).order_by(db.func.strftime('%Y-%m', OtrsTicket.closed_date).desc()).all()
            
            # Organize data by month
            for record in monthly_data:
                month_str = record.month
                if month_str not in stats:
                    stats[month_str] = {}
                stats[month_str][record.responsible] = record.count
        
        return stats
    
    def get_database_overview(self):
        """Get comprehensive database overview"""
        try:
            # Get total records count
            total_records = OtrsTicket.query.count()
            
            if total_records == 0:
                return {
                    'success': True,
                    'total_records': 0,
                    'data_sources_count': 0,
                    'last_updated': None,
                    'stats': {},
                    'empty_firstresponse_details': []
                }
            
            # Get data sources count
            data_sources_count = OtrsTicket.query.with_entities(OtrsTicket.data_source).distinct().count()
            
            # Get last updated timestamp
            last_updated_ticket = OtrsTicket.query.order_by(OtrsTicket.import_time.desc()).first()
            last_updated = last_updated_ticket.import_time.isoformat() if last_updated_ticket and last_updated_ticket.import_time else None
            
            # Get statistics using direct database queries
            stats = self.analyze_tickets_from_database()
            
            # Get empty first response details
            empty_firstresponse_tickets = OtrsTicket.query.filter(
                (OtrsTicket.first_response.is_(None) | 
                 (OtrsTicket.first_response == '') |
                 (OtrsTicket.first_response == 'nan') |
                 (OtrsTicket.first_response == 'NaN')),
                ~OtrsTicket.state.in_(['Closed', 'Resolved'])
            ).all()
            
            empty_firstresponse_details = []
            for ticket in empty_firstresponse_tickets:
                detail = {
                    'ticket_number': ticket.ticket_number or 'N/A',
                    'age': ticket.age or 'N/A',
                    'created': str(ticket.created_date) if ticket.created_date else 'N/A',
                    'priority': ticket.priority or 'N/A',
                    'state': ticket.state or 'N/A'
                }
                empty_firstresponse_details.append(detail)
            
            return {
                'success': True,
                'total_records': total_records,
                'data_sources_count': data_sources_count,
                'last_updated': last_updated,
                'stats': stats,
                'empty_firstresponse_details': empty_firstresponse_details
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting database statistics: {str(e)}'
            }
    
    def get_daily_statistics_data(self):
        """Get daily statistics data"""
        try:
            # Get all daily statistics
            daily_stats = DailyStatistics.query.order_by(DailyStatistics.statistic_date.desc()).all()
            
            # Get statistics logs - limit to 10 most recent for display
            stats_logs = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).limit(10).all()
            
            # Get current configuration
            from models.statistics import StatisticsConfig
            config = StatisticsConfig.query.first()
            
            data = {
                'daily_stats': [stat.to_dict() for stat in daily_stats],
                'stats_logs': [log.to_dict() for log in stats_logs],
                'config': config.to_dict() if config else {'schedule_time': '23:59', 'enabled': True}
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            return {
                'success': False, 
                'error': f'Error getting daily statistics: {str(e)}'
            }
    
    def log_statistic_query(self, query_type, upload_id=None, age_segment=None, record_count=0):
        """Log a statistical query operation"""
        try:
            # Get current statistics for context
            total_records = OtrsTicket.query.count()
            current_open_count = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).count()
            empty_firstresponse_count = OtrsTicket.query.filter(
                (OtrsTicket.first_response.is_(None) | 
                 (OtrsTicket.first_response == '') |
                 (OtrsTicket.first_response == 'nan') |
                 (OtrsTicket.first_response == 'NaN')),
                ~OtrsTicket.state.in_(['Closed', 'Resolved'])
            ).count()
            
            # Create statistic record
            statistic_record = Statistic(
                query_type=query_type,
                total_records=total_records,
                current_open_count=current_open_count,
                empty_firstresponse_count=empty_firstresponse_count,
                age_segment=age_segment,
                record_count=record_count,
                upload_id=upload_id
            )
            
            db.session.add(statistic_record)
            db.session.commit()
            
            return statistic_record
            
        except Exception as e:
            print(f"✗ Error logging statistic query: {str(e)}")
            db.session.rollback()
            return None
