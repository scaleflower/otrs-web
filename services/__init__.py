"""
Business logic services for OTRS Web Application
"""

import os

from .ticket_service import TicketService
from .analysis_service import AnalysisService
from .export_service import ExportService
from .scheduler_service import SchedulerService
from .update_service import UpdateService

# Export all services for easy import
__all__ = [
    'TicketService',
    'AnalysisService', 
    'ExportService',
    'SchedulerService',
    'UpdateService',
    'ticket_service',
    'analysis_service',
    'export_service',
    'scheduler_service',
    'update_service'
]

# Global service instances (singleton pattern)
ticket_service = TicketService()
analysis_service = AnalysisService()
export_service = ExportService()
update_service = UpdateService()
scheduler_service = SchedulerService(
    analysis_service=analysis_service,
    update_service=update_service
)

def init_services(app):
    """Initialize all services with Flask app"""
    update_service.initialize(app)

    should_start_scheduler = True
    if app.config.get('DEBUG'):
        # When Flask debug reloader is active, ensure scheduler only starts in the main process
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            should_start_scheduler = False

    if should_start_scheduler:
        # Initialize scheduler with app context
        scheduler_service.initialize_scheduler(app)
    else:
        print("✓ Scheduler initialization skipped for reloader process")

    print("✓ All services initialized")
