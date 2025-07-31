"""
RAG (Retrieval-Augmented Generation) Database Models
Adapted from Generic RAG Platform for nBrain integration
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class DataSource(Base):
    """Data source configuration for RAG system"""
    __tablename__ = 'rag_data_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    config = Column(JSON)  # Stores metrics, dimensions, and other config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entries = relationship("DataEntry", back_populates="source", cascade="all, delete-orphan")

class DataEntry(Base):
    """Stores actual data entries for RAG queries"""
    __tablename__ = 'rag_data_entries'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('rag_data_sources.id'), nullable=False)
    entity_id = Column(String(200), nullable=False)  # Unique identifier within source
    timestamp = Column(DateTime)
    data = Column(JSON)  # Flexible storage for metrics and dimensions
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source = relationship("DataSource", back_populates="entries")
    
    # Indexes for performance
    __table_args__ = (
        {'extend_existing': True}
    )

class RAGChatHistory(Base):
    """Chat history specific to RAG interactions"""
    __tablename__ = 'rag_chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text)
    context_data = Column(JSON)  # Stores context used for the query
    data_sources_used = Column(JSON)  # Which data sources were queried
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="rag_chats")

class RAGConfiguration(Base):
    """Stores RAG-specific configuration per user or globally"""
    __tablename__ = 'rag_configurations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Null for global config
    config_type = Column(String(50), nullable=False)  # 'prompts', 'ui', 'data_schema', etc.
    config_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="rag_configs") 