"""
RAG (Retrieval-Augmented Generation) Database Models
Adapted from Generic RAG Platform for nBrain integration
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean, Float, Index
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
    """Individual data entries for RAG system"""
    __tablename__ = 'rag_data_entries'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('rag_data_sources.id'), nullable=False)
    entity_id = Column(String(200), nullable=False)
    timestamp = Column(DateTime)
    data = Column(JSON)  # Stores the actual data
    entry_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source = relationship("DataSource", back_populates="entries")
    
    # Indexes
    __table_args__ = (
        Index('idx_rag_data_entries_source_entity', 'source_id', 'entity_id'),
        Index('idx_rag_data_entries_timestamp', 'timestamp'),
    )

class RAGChatHistory(Base):
    """Chat history specific to RAG interactions"""
    __tablename__ = 'rag_chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)  # Changed from Integer to String
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
    user_id = Column(String, ForeignKey('users.id'), nullable=True)  # Changed from Integer to String
    config_type = Column(String(50), nullable=False)  # 'prompts', 'ui', 'data_schema', etc.
    config_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="rag_configs") 