from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class State(db.Model):
    __tablename__ = 'states'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # State code like 'YB' for Yobe
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    local_governments = db.relationship('LocalGovernment', backref='state', lazy=True, cascade='all, delete-orphan')
    properties = db.relationship('Property', backref='state', lazy=True)
    
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
    
    # Relationships
    properties = db.relationship('Property', backref='local_government', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'state_id': self.state_id,
            'state_name': self.state.name if self.state else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

