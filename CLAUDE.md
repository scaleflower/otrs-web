# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OTRS Web Application - A Flask-based web application for analyzing and visualizing OTRS ticket data. The system supports multiple databases (SQLite for development, PostgreSQL for production) and comprehensive statistical analysis of ticket data.

## Common Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python3 app.py

# Run with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:15001 --access-logfile - --error-logfile - app:app
```

### Docker

```bash
# Build and run with PostgreSQL (recommended for production)
docker-compose up -d

# Build and run with SQLite
docker-compose -f docker-compose.sqlite.yml up -d

# View logs
docker-compose logs -f otrs-web

# Rebuild after code changes
docker-compose up -d --build
```

### Database Management

```bash
# Initialize PostgreSQL database (if needed)
python init_postgres_db.py

# The application automatically creates tables on first run
# Database schema migrations are handled automatically via models/__init__.py
```

## Architecture

### Core Design Pattern

The application follows a modular architecture with clear separation of concerns:

**app.py** → Main Flask application, registers blueprints and initializes services
**blueprints/** → Route handlers organized by feature (upload, statistics, export, backup, admin, init, daily_stats)
**services/** → Business logic layer (ticket, analysis, export, scheduler, backup, system_config)
**models/** → SQLAlchemy ORM models (ticket, statistics, user, system_config)
**utils/** → Helper functions (auth, validators, formatters, decorators)
**config/** → Environment-based configuration (base, development, production)

### Service Layer Architecture

All business logic is encapsulated in services (services/__init__.py):

- **TicketService**: Handles Excel file uploads, parsing, and ticket data storage
- **AnalysisService**: Performs statistical analysis on ticket data (age segments, responsible persons, daily stats)
- **ExportService**: Generates Excel and text exports of analysis results
- **SchedulerService**: Manages APScheduler for automated daily statistics and backups
- **BackupService**: Database backup/restore operations with compression
- **SystemConfigService**: Manages system-wide configuration settings

Services are initialized in app.py via `init_services(app)` and should be imported from the services module, not instantiated directly.

### Database Models

**OtrsTicket**: Core ticket data (ticket_number, priority, state, age, created_date, closed_date, responsible)
**UploadDetail**: Upload session tracking (filename, stored_filename, record_count, new_records_count, upload_time)
**DailyStatistics**: Aggregated daily statistics for performance
**StatisticsConfig**: Scheduler configuration (schedule_time, enabled)
**StatisticsLog**: Query execution logging
**ResponsibleConfig**: User-specific responsible person selections
**SystemConfig**: Key-value system configuration storage

### Blueprint Organization

Each blueprint handles a specific feature domain:

- **upload_bp**: File upload and processing
- **statistics_bp**: Statistical queries and analysis
- **export_bp**: Data export functionality
- **daily_stats_bp**: Daily statistics management (password-protected)
- **backup_bp**: Database backup/restore operations
- **admin_bp**: Administrative functions
- **init_bp**: First-time setup wizard

### Configuration System

Configuration uses environment-based classes (config/__init__.py):

- **BaseConfig**: Default settings, database URIs, upload limits, scheduler settings
- **DevelopmentConfig**: Debug enabled, verbose logging
- **ProductionConfig**: Optimized for deployment

Environment is selected via `FLASK_ENV` environment variable (development/production).

### Database Flexibility

The application supports both SQLite and PostgreSQL:

- **SQLite**: Default for development, stores data in `db/otrs_data.db`
- **PostgreSQL**: Recommended for production, configured via environment variables

Database connection is determined by `SQLALCHEMY_DATABASE_URI` in config, which checks:
1. `DATABASE_URL` environment variable (Heroku-style)
2. `SQLALCHEMY_DATABASE_URI` environment variable
3. Falls back to SQLite in `db/otrs_data.db`

### Scheduler System

APScheduler manages automated tasks (services/scheduler_service.py):

- **Daily Statistics**: Calculates and stores aggregated ticket statistics
- **Database Backups**: Automated backups with configurable retention (default: 30 days)
- **Schedule Time**: Configurable via web UI, default 23:59 Asia/Shanghai

Scheduler persists across restarts and handles concurrent execution prevention.

### File Upload Processing

Excel files are processed through a pipeline (services/ticket_service.py):

1. Secure filename generation with timestamp prefix
2. Pandas-based Excel parsing (supports .xlsx, .xls)
3. Data validation and normalization
4. Duplicate detection via ticket_number + data_source
5. Age calculation from created_date to current time
6. Batch insertion with SQLAlchemy bulk operations
7. UploadDetail record creation for tracking

### Important Implementation Notes

- **Circular Import Prevention**: Services are imported after app initialization in app.py
- **Database Initialization**: models/__init__.py handles table creation and schema migrations automatically
- **Missing Tables**: Application checks for missing tables and creates them without dropping existing data
- **File Storage**: Uploaded files stored with format `YYYYMMDD_HHMMSS_originalname.xlsx`
- **Data Source Tracking**: Each ticket records its originating file for traceability
- **Age Calculation**: Tickets track age_hours for segment analysis (0-24h, 24-48h, 48-72h, >72h)

## Environment Variables

Key environment variables (see config/base.py for full list):

```bash
# Application
FLASK_ENV=development|production
PORT=15001
SECRET_KEY=your-secret-key-here

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database
# OR use individual variables:
DATABASE_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=otrs_db
DB_USER=otrs_user
DB_PASSWORD=otrs_password

# Backup
AUTO_BACKUP_ENABLED=true
BACKUP_TIME=02:00
BACKUP_RETENTION_DAYS=30
```

## Directory Structure

```
├── app.py                    # Main Flask application
├── blueprints/              # Route handlers by feature
│   ├── upload_bp.py         # File upload routes
│   ├── statistics_bp.py     # Statistics routes
│   ├── export_bp.py         # Export routes
│   ├── daily_stats_bp.py    # Daily statistics routes
│   ├── backup_bp.py         # Backup routes
│   ├── admin_bp.py          # Admin routes
│   └── init_bp.py           # Initialization wizard
├── services/                # Business logic layer
│   ├── ticket_service.py    # Ticket data operations
│   ├── analysis_service.py  # Statistical analysis
│   ├── export_service.py    # Data export logic
│   ├── scheduler_service.py # Scheduled tasks
│   ├── backup_service.py    # Backup operations
│   └── system_config_service.py
├── models/                  # Database models
│   ├── ticket.py            # OtrsTicket, UploadDetail
│   ├── statistics.py        # Statistics models
│   ├── user.py              # User-related models
│   └── system_config.py     # System configuration
├── utils/                   # Helper utilities
│   ├── auth.py              # Authentication
│   ├── validators.py        # Input validation
│   └── formatters.py        # Data formatting
├── config/                  # Configuration
│   ├── base.py              # Base configuration
│   ├── development.py       # Dev environment
│   └── production.py        # Prod environment
├── templates/               # Jinja2 templates
├── static/                  # CSS, JS, images
├── uploads/                 # Uploaded Excel files
├── db/                      # SQLite database (if used)
├── logs/                    # Application logs
└── database_backups/        # Database backup files
```

## Development Guidelines

### Adding New Features

1. **Create service** in `services/` for business logic
2. **Create blueprint** in `blueprints/` for routes
3. **Register blueprint** in `app.py`
4. **Add models** in `models/` if database changes needed
5. **Update `__init__.py`** files to export new components

### Database Changes

- Add new model classes in appropriate file under `models/`
- Export model in `models/__init__.py`
- Add table name to required_tables set in `models/__init__.py`
- Application will auto-create new tables on next restart
- For complex migrations, update `_ensure_upload_detail_schema()` pattern

### Scheduled Tasks

Add new scheduled tasks via SchedulerService:

```python
from services import scheduler_service

def my_scheduled_function():
    # Task logic here
    pass

# In service initialization
scheduler_service.scheduler.add_job(
    my_scheduled_function,
    'cron',
    hour=2,
    minute=0,
    id='my_task_id'
)
```

## Troubleshooting

### Database Connection Issues

- Check database credentials in `.env` or environment variables
- Verify PostgreSQL is running: `docker-compose ps`
- Check logs: `docker-compose logs postgres`

### Upload Failures

- Verify Excel file format (.xlsx or .xls)
- Check file size (max 16MB)
- Ensure required columns exist in Excel
- Check logs in `logs/` directory

### Port Conflicts

- Default port is 15001
- Change via `PORT` environment variable
- Update docker-compose.yml port mapping if needed
