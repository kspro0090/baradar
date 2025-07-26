from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False)  # 'system_manager', 'approval_admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    created_services = db.relationship('Service', backref='creator', lazy='dynamic')
    handled_requests = db.relationship('ServiceRequest', backref='handler', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_system_manager(self):
        return self.role == 'system_manager'
    
    def is_approval_admin(self):
        return self.role == 'approval_admin'

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    google_doc_id = db.Column(db.String(255))  # Google Docs file ID
    # New fields for image-based forms
    form_type = db.Column(db.String(20), default='google_doc')  # 'google_doc' or 'image'
    image_path = db.Column(db.String(500))  # Path to uploaded image
    form_design_data = db.Column(db.Text)  # JSON data for form design (textboxes, fonts, positions)
    page_size = db.Column(db.String(10), default='A4')  # A4, A5, or 'original'
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Auto-approval settings
    auto_approve_enabled = db.Column(db.Boolean, default=False)
    auto_approve_sheet_id = db.Column(db.String(255), default="1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ")
    auto_approve_sheet_column = db.Column(db.String(10), default="A")
    auto_approve_field_name = db.Column(db.String(100))  # Which field to check (e.g., 'employee_name')
    
    # Relationships
    form_fields = db.relationship('FormField', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    requests = db.relationship('ServiceRequest', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_form_design_data(self):
        """Get form design data as dictionary"""
        if self.form_design_data:
            return json.loads(self.form_design_data)
        return {}
    
    def set_form_design_data(self, data):
        """Set form design data from dictionary"""
        self.form_design_data = json.dumps(data, ensure_ascii=False)
    
    def get_stats(self):
        total = self.requests.count()
        approved = self.requests.filter_by(status='approved').count()
        rejected = self.requests.filter_by(status='rejected').count()
        pending = self.requests.filter_by(status='pending').count()
        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending
        }

class FormField(db.Model):
    __tablename__ = 'form_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, number, email, date, textarea
    is_required = db.Column(db.Boolean, default=True)
    field_order = db.Column(db.Integer, default=0)
    placeholder = db.Column(db.String(200))
    options = db.Column(db.Text)  # JSON array for select/radio fields
    document_placeholder = db.Column(db.String(100))  # Placeholder in Word template
    
    def get_options(self):
        if self.options:
            return json.loads(self.options)
        return []

class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    tracking_code = db.Column(db.String(20), unique=True, nullable=False)
    form_data = db.Column(db.Text, nullable=False)  # JSON
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approval_note = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pdf_filename = db.Column(db.String(255))
    
    def get_form_data(self):
        return json.loads(self.form_data)
    
    def set_form_data(self, data):
        self.form_data = json.dumps(data, ensure_ascii=False)

