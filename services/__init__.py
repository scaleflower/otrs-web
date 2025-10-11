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
    'ticket_service',
    'analysis_service', 
    'export_service',
    'scheduler_service',
    'update_service',
    'system_config_service',
    'init_services'
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
system_config_service = SystemConfigService()

def init_services(app: Flask):
    """Initialize all services with Flask app"""
    ticket_service.initialize(app)
    analysis_service.initialize(app)
    export_service.initialize(app)
    update_service.initialize(app)
    system_config_service.init_app(app)
    
    # Initialize default configurations
    system_config_service.initialize_default_configs()

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
