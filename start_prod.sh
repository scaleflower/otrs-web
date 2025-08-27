#!/bin/bash
# Production startup script for OTRS Ticket Analysis Web Application

echo "Starting OTRS Ticket Analysis Web Application in production mode..."

# Check if requirements are installed
if [ ! -f "requirements_prod.txt" ]; then
    echo "Error: requirements_prod.txt not found!"
    exit 1
fi

# Install production dependencies if not already installed
echo "Checking dependencies..."
pip install -r requirements_prod.txt

# Set production environment variables
export FLASK_ENV=production
export PYTHONPATH=.

# Start Gunicorn production server
echo "Starting Gunicorn production server..."
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app

echo "Production server started on http://0.0.0.0:5000"
