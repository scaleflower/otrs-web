"""
Scheduler service for handling scheduled tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from models import StatisticsConfig
from .analysis_service import AnalysisService
from .backup_service import BackupService

class SchedulerService:
    """Service for scheduler operations"""
    
    def __init__(self, analysis_service=None, update_service=None):
        self.scheduler = None
        self.analysis_service = analysis_service or AnalysisService()
        self.update_service = update_service
        self.backup_service = None
        self.app = None
    
    def initialize_scheduler(self, app):
        """Initialize and start the scheduler"""
        if self.scheduler is None:
            self.app = app  # Store Flask app reference
            self.scheduler = BackgroundScheduler()
            
            # Initialize backup service
            self.backup_service = BackupService(app)
            
            # Schedule age distribution calculation
            self._schedule_age_distribution()
            
            # Schedule daily database backup
            self._schedule_daily_backup()

            # Schedule GitHub update checks
            self._schedule_update_checks()
            
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

    def _schedule_update_checks(self):
        """Schedule periodic update checks with APScheduler"""
        if not self.update_service or not self.app:
            return

        if not self.app.config.get('APP_UPDATE_ENABLED', True):
            return

        interval = int(self.app.config.get('APP_UPDATE_POLL_INTERVAL', 3600))
        interval = max(interval, 300)

        try:
            try:
                self.scheduler.remove_job('update_check_job')
            except Exception:
                pass

            self.scheduler.add_job(
                func=self._run_update_check_job,
                trigger='interval',
                seconds=interval,
                id='update_check_job',
                name='Poll GitHub for application updates',
                replace_existing=True
            )
            print(f"✓ Update check job scheduled every {interval} seconds")
        except Exception as e:
            print(f"✗ Error scheduling update checks: {str(e)}")

    def _run_update_check_job(self):
        """Execute update check inside application context"""
        if not self.update_service or not self.app:
            return

        try:
            with self.app.app_context():
                self.update_service.check_for_updates()
        except Exception as e:
            print(f"✗ Error during update check: {str(e)}")
    
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
    
    def _schedule_daily_backup(self):
        """Schedule daily database backup"""
        try:
            # Check if auto backup is enabled
            auto_backup = self.app.config.get('AUTO_BACKUP', True) if self.app else True
            
            if not auto_backup:
                print("✓ Auto backup is disabled")
                return
            
            # Get backup time from configuration
            backup_time = self.app.config.get('BACKUP_TIME', '02:00') if self.app else '02:00'
            
            # Parse backup time
            hour, minute = map(int, backup_time.split(':'))
            
            # Remove existing backup job if any
            try:
                self.scheduler.remove_job('daily_backup_job')
            except:
                pass
            
            # Schedule backup at configured time
            self.scheduler.add_job(
                func=self._daily_backup_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_backup_job',
                name=f'Daily database backup at {backup_time}',
                replace_existing=True
            )
            print(f"✓ Daily backup job scheduled for {backup_time}")
            
        except Exception as e:
            print(f"✗ Error scheduling daily backup: {str(e)}")
    
    def _daily_backup_job(self):
        """Job function for daily database backup"""
        try:
            print(f"🔄 Starting scheduled daily backup at {datetime.now()}")
            
            # Run within Flask app context
            if self.app and self.backup_service:
                with self.app.app_context():
                    # Create backup
                    success, message, backup_path = self.backup_service.create_backup(
                        compress=True, 
                        include_timestamp=True
                    )
                    
                    if success:
                        print(f"✓ Daily backup completed: {message}")
                        
                        # Clean up old backups
                        cleanup_success, cleanup_message, deleted_count = self.backup_service.cleanup_old_backups()
                        if cleanup_success and deleted_count > 0:
                            print(f"✓ Cleanup completed: {cleanup_message}")
                        
                    else:
                        print(f"✗ Daily backup failed: {message}")
            else:
                print("✗ No Flask app context or backup service available for scheduled backup")
                
        except Exception as e:
            print(f"✗ Error in scheduled daily backup: {str(e)}")
    
    def trigger_manual_backup(self):
        """Manually trigger database backup"""
        try:
            print("🔧 Manual database backup triggered")
            if self.backup_service:
                success, message, backup_path = self.backup_service.create_backup(compress=True, include_timestamp=True)
                # Return only success and message for consistency with other trigger methods
                return success, message
            else:
                return False, "Backup service not initialized"
        except Exception as e:
            error_msg = f"Error in manual backup: {str(e)}"
            print(f"✗ {error_msg}")
            return False, error_msg
    
    def get_backup_status(self):
        """Get backup service status and statistics"""
        try:
            if not self.backup_service:
                return {
                    'service_available': False,
                    'error': 'Backup service not initialized'
                }
            
            # Get backup statistics
            stats = self.backup_service.get_backup_stats()
            
            # Get backup list
            backups = self.backup_service.list_backups()
            
            # Check if auto backup is enabled
            auto_backup = self.app.config.get('AUTO_BACKUP', True) if self.app else True
            
            return {
                'service_available': True,
                'auto_backup_enabled': auto_backup,
                'statistics': stats,
                'recent_backups': backups[:5],  # Last 5 backups
                'total_backups': len(backups)
            }
            
        except Exception as e:
            return {
                'service_available': False,
                'error': str(e)
            }
    
    def cleanup_old_backups(self, retention_days=None):
        """Manually trigger backup cleanup"""
        try:
            if not self.backup_service:
                return False, "Backup service not initialized"
            
            return self.backup_service.cleanup_old_backups(retention_days)
            
        except Exception as e:
            error_msg = f"Error cleaning up backups: {str(e)}"
            print(f"✗ {error_msg}")
            return False, error_msg
    
    def verify_backup(self, backup_filename):
        """Verify a backup file"""
        try:
            if not self.backup_service:
                return False, "Backup service not initialized"
            
            return self.backup_service.verify_backup(backup_filename)
            
        except Exception as e:
            error_msg = f"Error verifying backup: {str(e)}"
            print(f"✗ {error_msg}")
            return False, error_msg
