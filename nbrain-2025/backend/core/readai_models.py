"""
Read.ai Integration Models
For storing webhook data and meeting transcripts
"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, func, Text, Boolean, Float, Integer
from sqlalchemy.orm import relationship
from .database import Base
import uuid

class ReadAIIntegration(Base):
    __tablename__ = "readai_integrations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Integration Settings
    webhook_secret = Column(String, nullable=True)  # For webhook verification
    integration_status = Column(String, default='active')  # active, paused, disconnected
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_webhook_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="readai_integrations")
    meetings = relationship("ReadAIMeeting", back_populates="integration", cascade="all, delete-orphan")


class ReadAIMeeting(Base):
    __tablename__ = "readai_meetings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id = Column(String, ForeignKey('readai_integrations.id'), nullable=False)
    
    # Read.ai Meeting Data
    readai_meeting_id = Column(String, unique=True, nullable=False)  # ID from Read.ai
    meeting_title = Column(String, nullable=False)
    meeting_url = Column(String, nullable=True)
    meeting_platform = Column(String, nullable=True)  # Zoom, Teams, Meet, etc.
    
    # Participants
    participants = Column(JSON, nullable=True)  # List of participant info
    host_email = Column(String, nullable=True)
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Float, nullable=True)
    
    # Transcript and Summary
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # List of key discussion points
    action_items = Column(JSON, nullable=True)  # List of action items
    
    # Analysis
    sentiment_score = Column(Float, nullable=True)  # Overall meeting sentiment
    engagement_score = Column(Float, nullable=True)  # Participant engagement
    
    # Client Association
    client_id = Column(String, ForeignKey('clients.id'), nullable=True)
    client = relationship("Client", backref="readai_meetings")
    
    # Oracle Integration
    synced_to_oracle = Column(Boolean, default=False)
    oracle_action_items_created = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    webhook_received_at = Column(DateTime(timezone=True), nullable=True)
    
    # Raw webhook data for debugging
    raw_webhook_data = Column(JSON, nullable=True)
    
    # Relationships
    integration = relationship("ReadAIIntegration", back_populates="meetings") 