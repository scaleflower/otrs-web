"""
Ticket-related database models
"""

from datetime import datetime
from . import db

class OtrsTicket(db.Model):
    """OTRS ticket model"""
    __tablename__ = 'otrs_ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_date = db.Column(db.DateTime, index=True)
    closed_date = db.Column(db.DateTime, index=True)
    state = db.Column(db.String(100), index=True)
    priority = db.Column(db.String(50), index=True)
    first_response = db.Column(db.String(255))
    age = db.Column(db.String(50))
    age_hours = db.Column(db.Float, index=True)
    
    # Other common fields from Excel
    queue = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    customer_id = db.Column(db.String(255))
    customer_realname = db.Column(db.String(255))
    title = db.Column(db.Text)
    service = db.Column(db.String(255))
    type = db.Column(db.String(100))
    category = db.Column(db.String(255))
    sub_category = db.Column(db.String(255))
    responsible = db.Column(db.String(255), index=True)  # Responsible person field
    
    # Metadata
    import_time = db.Column(db.DateTime, default=datetime.now, index=True)
    data_source = db.Column(db.String(255), index=True)  # Original filename
    raw_data = db.Column(db.Text)  # Store complete raw JSON data
    
    def __repr__(self):
        return f'<OtrsTicket {self.ticket_number}>'
    
    def to_dict(self):
        """Convert ticket to dictionary"""
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'closed_date': self.closed_date.isoformat() if self.closed_date else None,
            'state': self.state,
            'priority': self.priority,
            'first_response': self.first_response,
            'age': self.age,
            'age_hours': self.age_hours,
            'queue': self.queue,
            'owner': self.owner,
            'customer_id': self.customer_id,
            'customer_realname': self.customer_realname,
            'title': self.title,
            'service': self.service,
            'type': self.type,
            'category': self.category,
            'sub_category': self.sub_category,
            'responsible': self.responsible,
            'import_time': self.import_time.isoformat() if self.import_time else None,
            'data_source': self.data_source
        }
    
    @property
    def is_open(self):
        """Check if ticket is open"""
        return self.closed_date is None
    
    @property
    def is_empty_first_response(self):
        """Check if first response is empty"""
        return (not self.first_response or 
                self.first_response == '' or 
                self.first_response.lower() in ['nan', 'none', 'null'])


class UploadDetail(db.Model):
    """Upload record table"""
    __tablename__ = 'upload_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, index=True)
    upload_time = db.Column(db.DateTime, default=datetime.now, index=True)
    record_count = db.Column(db.Integer, nullable=False)  # 当前数据库总记录数
    new_records_count = db.Column(db.Integer, default=0)  # 本次新增记录数
    import_mode = db.Column(db.String(50))  # Import mode: clear_existing or incremental
    stored_filename = db.Column(db.String(255))  # Physically stored filename for downloads
    
    # Relationships
    statistics = db.relationship('Statistic', backref='upload', lazy=True)
    
    def __repr__(self):
        return f'<UploadDetail {self.filename}>'
    
    def to_dict(self):
        """Convert upload detail to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'record_count': self.record_count,
            'new_records_count': self.new_records_count,
            'import_mode': self.import_mode,
            'stored_filename': self.stored_filename
        }
