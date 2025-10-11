"""
Service module initialization for OTRS Web Application
"""

from flask import Flask

# Import services
from .ticket_service import TicketService
from .analysis_service import AnalysisService
from .export_service import ExportService
from .scheduler_service import SchedulerService
from .update_service import UpdateService
from .system_config_service import SystemConfigService

# Service instances
ticket_service = TicketService()
analysis_service = AnalysisService()
export_service = ExportService()
scheduler_service = SchedulerService()
update_service = UpdateService()
system_config_service = SystemConfigService()

def init_services(app: Flask):
    """Initialize all services with Flask app"""
    ticket_service.initialize(app)
    analysis_service.initialize(app)
    export_service.initialize(app)
    scheduler_service.initialize(app)
    update_service.initialize(app)
    system_config_service.init_app(app)
    
    # Initialize default configurations
    system_config_service.initialize_default_configs()

__all__ = [
    'ticket_service',
    'analysis_service', 
    'export_service',
    'scheduler_service',
    'update_service',
    'system_config_service',
    'init_services'
]
