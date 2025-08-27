@echo off
REM Production startup script for Windows
echo Starting OTRS Ticket Analysis Web Application in production mode...

REM Check if requirements are installed
if not exist "requirements_prod.txt" (
    echo Error: requirements_prod.txt not found!
    exit /b 1
)

REM Install production dependencies
echo Checking dependencies...
pip install -r requirements_prod.txt

REM Set production environment variables
set FLASK_ENV=production
set PYTHONPATH=.

REM Start Gunicorn production server
echo Starting Gunicorn production server...
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app

echo Production server started on http://0.0.0.0:5000
