"""
Agent Ideator Database Models
Extracted for standalone use
"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class AgentIdea(Base):
    __tablename__ = 'agent_ideas'
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)  # List of step descriptions
    agent_stack = Column(JSON, nullable=False)  # Technical stack details
    client_requirements = Column(JSON, nullable=False)  # List of requirements
    conversation_history = Column(JSON, nullable=True)  # Store the ideation conversation
    status = Column(String, default="draft")  # draft, completed, in_development
    agent_type = Column(String, nullable=True)  # customer_service, data_analysis, etc.
    implementation_estimate = Column(JSON, nullable=True)  # Cost and time estimates
    security_considerations = Column(JSON, nullable=True)  # Security details
    future_enhancements = Column(JSON, nullable=True)  # List of future enhancement ideas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign key to users table
    user_id = Column(String, ForeignKey('users.id'))
    
    # If you need the relationship, uncomment and adjust based on your User model
    # user = relationship("User", back_populates="agent_ideas") 