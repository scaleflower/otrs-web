"""
Service module initialization for OTRS Web Application
"""

from flask import Flask

# Import services
from .ticket_service import TicketService
from .analysis_service import AnalysisService
from .export_service import ExportService
from .scheduler_service import SchedulerService
from .system_config_service import SystemConfigService
from .version_service import VersionService
from .upgrade_service import UpgradeService

# Service instances
ticket_service = TicketService()
analysis_service = AnalysisService()
export_service = ExportService()
scheduler_service = SchedulerService()
system_config_service = SystemConfigService()
version_service = VersionService()
upgrade_service = UpgradeService()

def init_services(app: Flask):
    """Initialize all services with Flask app"""
    ticket_service.initialize(app)
    analysis_service.initialize(app)
    export_service.initialize(app)
    scheduler_service.initialize(app)
    system_config_service.init_app(app)
    version_service.init_app(app)
    upgrade_service.init_app(app)

    # Initialize default configurations
    system_config_service.initialize_default_configs()

__all__ = [
    'ticket_service',
    'analysis_service',
    'export_service',
    'scheduler_service',
    'system_config_service',
    'version_service',
    'upgrade_service',
    'init_services'
]
