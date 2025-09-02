"""
Business logic services for OTRS Web Application
"""

from .ticket_service import TicketService
from .analysis_service import AnalysisService
from .export_service import ExportService
from .scheduler_service import SchedulerService

# Export all services for easy import
__all__ = [
    'TicketService',
    'AnalysisService', 
    'ExportService',
    'SchedulerService',
    'ticket_service',
    'analysis_service',
    'export_service',
    'scheduler_service'
]

# Global service instances (singleton pattern)
ticket_service = TicketService()
analysis_service = AnalysisService()
export_service = ExportService()
scheduler_service = SchedulerService()

def init_services(app):
    """Initialize all services with Flask app"""
    # Initialize scheduler with app context
    scheduler_service.initialize_scheduler(app)
    print("✓ All services initialized")
