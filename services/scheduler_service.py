"""
Scheduler service for handling scheduled tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from models import StatisticsConfig
from .analysis_service import AnalysisService

class SchedulerService:
    """Service for scheduler operations"""
    
    def __init__(self):
        self.scheduler = None
        self.analysis_service = AnalysisService()
        self.app = None
    
    def initialize_scheduler(self, app):
        """Initialize and start the scheduler"""
        if self.scheduler is None:
            self.app = app  # Store Flask app reference
            self.scheduler = BackgroundScheduler()
            
            # Schedule age distribution calculation
            self._schedule_age_distribution()
            
            # Start scheduler
            self.scheduler.start()
            print("✓ Scheduler initialized and started")
            
            # Register shutdown handler
            import atexit
            atexit.register(lambda: self.shutdown())
        
        return self.scheduler
    
    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            print("✓ Scheduler shutdown completed")
    
    def _schedule_age_distribution(self):
        """Schedule age distribution calculation based on configured time"""
        schedule_time = self._get_schedule_time()
        
        try:
            hour, minute = map(int, schedule_time.split(':'))
            
            # Remove existing job if any
            try:
                self.scheduler.remove_job('age_distribution_job')
            except:
                pass
            
            # Add new job with configured time
            self.scheduler.add_job(
                func=self._calculate_age_distribution_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='age_distribution_job',
                name='Calculate age distribution at configured time',
                replace_existing=True
            )
            print(f"✓ Age distribution job scheduled for {schedule_time}")
            
        except Exception as e:
            print(f"✗ Error scheduling age distribution: {str(e)}")
    
    def _calculate_age_distribution_job(self):
        """Job function for calculating age distribution"""
        try:
            print(f"🕐 Starting scheduled age distribution calculation at {datetime.now()}")
            
            # Run within Flask app context
            if self.app:
                with self.app.app_context():
                    success, message = self.analysis_service.calculate_daily_age_distribution()
                    
                    if success:
                        print(f"✓ Scheduled calculation completed: {message}")
                    else:
                        print(f"✗ Scheduled calculation failed: {message}")
            else:
                print("✗ No Flask app context available for scheduled job")
                
        except Exception as e:
            print(f"✗ Error in scheduled age distribution calculation: {str(e)}")
    
    def _get_schedule_time(self):
        """Get schedule time from database configuration"""
        try:
            if self.app:
                with self.app.app_context():
                    config = StatisticsConfig.query.first()
                    if config and config.enabled:
                        return config.schedule_time
                    return '23:59'  # Default time
            else:
                return '23:59'  # Fallback default
        except Exception as e:
            print(f"Error getting schedule time: {str(e)}")
            return '23:59'  # Fallback default
    
    def update_schedule(self, schedule_time, enabled=True):
        """Update the schedule configuration"""
        try:
            # Validate time format
            hour, minute = map(int, schedule_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time format")
            
            # Update database configuration
            from models import db
            
            if self.app:
                with self.app.app_context():
                    config = StatisticsConfig.query.first()
                    if not config:
                        config = StatisticsConfig()
                        db.session.add(config)
                    
                    config.schedule_time = schedule_time
                    config.enabled = enabled
                    config.updated_at = datetime.utcnow()
                    
                    db.session.commit()
            else:
                raise Exception("No Flask app context available")
            
            # Reschedule the job if scheduler is running
            if self.scheduler and self.scheduler.running and enabled:
                self._schedule_age_distribution()
            elif self.scheduler and self.scheduler.running and not enabled:
                # Remove job if disabled
                try:
                    self.scheduler.remove_job('age_distribution_job')
                    print("✓ Age distribution job disabled")
                except:
                    pass
            
            return True, "Schedule updated successfully"
            
        except Exception as e:
            return False, f"Error updating schedule: {str(e)}"
    
    def get_scheduler_status(self):
        """Get current scheduler status"""
        try:
            if not self.scheduler:
                return {
                    'running': False,
                    'jobs': [],
                    'error': 'Scheduler not initialized'
                }
            
            jobs_info = []
            if self.scheduler.running:
                for job in self.scheduler.get_jobs():
                    job_info = {
                        'id': job.id,
                        'name': job.name,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    }
                    jobs_info.append(job_info)
            
            return {
                'running': self.scheduler.running,
                'jobs': jobs_info,
                'job_count': len(jobs_info)
            }
            
        except Exception as e:
            return {
                'running': False,
                'jobs': [],
                'error': str(e)
            }
    
    def trigger_manual_calculation(self):
        """Manually trigger age distribution calculation"""
        try:
            print("🔧 Manual age distribution calculation triggered")
            return self.analysis_service.calculate_daily_age_distribution()
        except Exception as e:
            error_msg = f"Error in manual calculation: {str(e)}"
            print(f"✗ {error_msg}")
            return False, error_msg
    
    def reschedule_job(self):
        """Reschedule the age distribution job with current configuration"""
        try:
            if self.scheduler and self.scheduler.running:
                self._schedule_age_distribution()
                return True, "Job rescheduled successfully"
            else:
                return False, "Scheduler is not running"
        except Exception as e:
            return False, f"Error rescheduling job: {str(e)}"
