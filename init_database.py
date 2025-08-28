import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a minimal Flask app for database initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///otrs_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the database models
class UploadSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default='CURRENT_TIMESTAMP')
    total_records = db.Column(db.Integer, nullable=False)
    
    # 关系
    tickets = db.relationship('Ticket', backref='session', lazy=True)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), db.ForeignKey('upload_session.session_id'), nullable=False)
    ticket_number = db.Column(db.String(100))
    created_date = db.Column(db.DateTime)
    closed_date = db.Column(db.DateTime)
    state = db.Column(db.String(100))
    priority = db.Column(db.String(50))
    first_response = db.Column(db.String(255))
    age = db.Column(db.String(50))
    age_hours = db.Column(db.Float)
    
    # 原始数据存储（用于灵活查询）
    raw_data = db.Column(db.Text)

# Create database tables within application context
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
    print(f"Database file: otrs_data.db")
    print(f"Database size: {os.path.getsize('otrs_data.db')} bytes")
