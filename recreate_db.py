#!/usr/bin/env python3
"""
Script to recreate database with new Responsible field
"""

from app import app, db

with app.app_context():
    db.create_all()
    print("Database tables created successfully with Responsible field!")
