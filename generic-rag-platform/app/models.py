from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import JSON

class User(db.Model, UserMixin):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    chats = db.relationship('ChatHistory', backref='author', lazy=True)
    data_sources = db.relationship('DataSource', backref='owner', lazy=True)
    documents = db.relationship('Document', backref='owner', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class ChatHistory(db.Model):
    """Store chat conversations."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(36), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    context_data = db.Column(JSON, nullable=True)  # Store any context like selected data source, date range, etc.
    
    def __repr__(self):
        return f"ChatHistory(user={self.user_id}, session={self.session_id}, time={self.timestamp})"

class DataSource(db.Model):
    """Generic data source configuration."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Optional user ownership
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_type = db.Column(db.String(50), nullable=False)  # 'csv', 'api', 'database', etc.
    config = db.Column(JSON, nullable=False)  # Store metrics, dimensions, and other config
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entries = db.relationship('DataEntry', backref='source', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"DataSource('{self.name}', type='{self.source_type}')"

class DataEntry(db.Model):
    """Generic data entry - can store any type of data."""
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False, index=True)
    entity_id = db.Column(db.String(200), nullable=False, index=True)  # Generic identifier
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    data = db.Column(JSON, nullable=False)  # Flexible JSON storage for any data structure
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_source_entity_time', 'source_id', 'entity_id', 'timestamp'),
        db.Index('idx_source_time', 'source_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"DataEntry(source={self.source_id}, entity={self.entity_id}, time={self.timestamp})"

class Document(db.Model):
    """Store uploaded documents for RAG."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'context', 'reference', 'data', etc.
    content_type = db.Column(db.String(100), nullable=True)  # MIME type
    storage_path = db.Column(db.String(500), nullable=True)  # Local or S3 path
    vector_store_id = db.Column(db.String(255), nullable=True)  # For vector database integration
    metadata = db.Column(JSON, nullable=True)  # Additional metadata
    status = db.Column(db.String(20), nullable=False, default='processing')  # processing, ready, failed
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"Document('{self.filename}', status='{self.status}')"

class SystemConfig(db.Model):
    """Store system-wide configuration."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(JSON, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"SystemConfig('{self.key}')" 