from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import os

db = SQLAlchemy()

class State(db.Model):
    __tablename__ = 'states'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # State code like 'YB' for Yobe
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'local_governments': [lg.to_dict() for lg in self.local_governments]
        }

class LocalGovernment(db.Model):
    __tablename__ = 'local_governments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'state_id': self.state_id,
            'state_name': self.state.name if self.state else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_master_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_master(self):
        """Check if user is the master admin based on .env credentials"""
        master_username = os.environ.get('MASTER_USERNAME')
        return self.email == master_username and self.is_admin

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_master_admin': self.is_master_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    property_type = db.Column(db.String(10), nullable=False)  # 'sale' or 'rent'
    location = db.Column(db.String(200), nullable=True)  # Optional legacy field
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=True)
    local_government_id = db.Column(db.Integer, db.ForeignKey('local_governments.id'), nullable=True)
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    area_sqft = db.Column(db.Float, default=0)
    status = db.Column(db.String(10), default='active')  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_location_display(self):
        """Get formatted location string"""
        if self.local_government and self.state:
            return f"{self.local_government.name}, {self.state.name}"
        elif self.state:
            return self.state.name
        else:
            return self.location or "Location not specified"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'property_type': self.property_type,
            'location': self.location,
            'state_id': self.state_id,
            'local_government_id': self.local_government_id,
            'state_name': self.state.name if self.state else None,
            'local_government_name': self.local_government.name if self.local_government else None,
            'location_display': self.get_location_display(),
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'area_sqft': self.area_sqft,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'images': [img.to_dict() for img in self.images]
        }

class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    upload_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'image_filename': self.image_filename,
            'is_primary': self.is_primary,
            'upload_order': self.upload_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ContactInquiry(db.Model):
    __tablename__ = 'contact_inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    subscribe_newsletter = db.Column(db.Boolean, default=False)  # Newsletter subscription field
    status = db.Column(db.String(20), default='new')  # 'new', 'read', 'responded'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'property_id': self.property_id,
            'message': self.message,
            'subscribe_newsletter': self.subscribe_newsletter,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'property_title': self.property.title if self.property else None
        }

class UserApplication(db.Model):
    __tablename__ = 'user_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'property_id': self.property_id,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_email': self.user.email if self.user else None,
            'property_title': self.property.title if self.property else None
        }

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_email': self.admin.email if self.admin else None,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CustomerEmail(db.Model):
    __tablename__ = 'customer_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # For unsubscribe functionality
    source = db.Column(db.String(50), default='inquiry_form')  # Track where subscription came from
    
    # Newsletter subscription preferences (default to True for all)
    weekly_subscription = db.Column(db.Boolean, default=True)
    monthly_subscription = db.Column(db.Boolean, default=True)
    quarterly_subscription = db.Column(db.Boolean, default=True)
    yearly_subscription = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None,
            'is_active': self.is_active,
            'source': self.source,
            'weekly_subscription': self.weekly_subscription,
            'monthly_subscription': self.monthly_subscription,
            'quarterly_subscription': self.quarterly_subscription,
            'yearly_subscription': self.yearly_subscription
        }

# Define relationships after all models are defined
State.local_governments = db.relationship('LocalGovernment', backref='state', lazy=True, cascade='all, delete-orphan')
State.properties = db.relationship('Property', backref='state', lazy=True)
LocalGovernment.properties = db.relationship('Property', backref='local_government', lazy=True)
Property.images = db.relationship('PropertyImage', backref='property', lazy=True, cascade='all, delete-orphan')
Property.inquiries = db.relationship('ContactInquiry', backref='property', lazy=True)
Property.applications = db.relationship('UserApplication', backref='property', lazy=True)
User.applications = db.relationship('UserApplication', backref='user', lazy=True)
User.admin_logs = db.relationship('AdminLog', backref='admin', lazy=True)

