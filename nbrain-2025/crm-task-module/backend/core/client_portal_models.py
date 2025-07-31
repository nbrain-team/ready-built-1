"""
Client Portal Database Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, Text, Float, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base

class ClientStatus(enum.Enum):
    PROSPECT = "prospect"
    ACTIVE = "active"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class TaskStatus(enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVE)
    
    # Contact Information
    primary_contact_name = Column(String)
    primary_contact_email = Column(String)
    primary_contact_phone = Column(String)
    company_website = Column(String)
    domain = Column(String)  # Primary domain for sync
    sync_email_addresses = Column(JSON, default=list)  # List of email addresses to sync
    
    # Business Information
    industry = Column(String)
    company_size = Column(String)
    project_value = Column(Float)
    monthly_recurring_revenue = Column(Float)
    
    # Project Information
    start_date = Column(DateTime)
    estimated_end_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # CRM Integration
    crm_opportunity_id = Column(String, ForeignKey('crm_opportunities.id'))
    imported_from_crm = Column(Boolean, default=False)
    crm_import_date = Column(DateTime)
    
    # Metrics
    health_score = Column(Integer, default=100)  # 0-100
    last_communication = Column(DateTime)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # Relationships
    tasks = relationship("ClientTask", back_populates="client", cascade="all, delete-orphan")
    communications = relationship("ClientCommunication", back_populates="client")  # Remove cascade to prevent accidental deletion
    documents = relationship("ClientDocument", back_populates="client", cascade="all, delete-orphan")
    team_members = relationship("ClientTeamMember", back_populates="client", cascade="all, delete-orphan")
    activities = relationship("ClientActivity", back_populates="client", cascade="all, delete-orphan")

class ClientTask(Base):
    __tablename__ = "client_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Assignment
    assigned_to = Column(String, ForeignKey('users.id'))
    assigned_by = Column(String, ForeignKey('users.id'))
    
    # Dates
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Task Details
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)  # {frequency: 'daily/weekly/monthly', interval: 1}
    
    # Dependencies
    depends_on_task_id = Column(String, ForeignKey('client_tasks.id'))
    
    # Metadata
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    
    # Relationships
    client = relationship("Client", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")

class ClientCommunication(Base):
    __tablename__ = "client_communications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    type = Column(String)  # email, internal_chat, meeting_note, phone_call
    
    # Communication Details
    subject = Column(String)
    content = Column(Text)
    summary = Column(Text)  # AI-generated summary
    
    # Participants
    from_user = Column(String)
    to_users = Column(JSON, default=list)
    cc_users = Column(JSON, default=list)
    
    # Email Specific
    email_thread_id = Column(String)
    email_message_id = Column(String)
    is_important = Column(Boolean, default=False)
    
    # Sync Metadata
    synced_by = Column(String)  # Email address of the user whose account this was synced from
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_by = Column(JSON, default=dict)  # {user_id: timestamp}
    
    # Relationships
    client = relationship("Client", back_populates="communications")
    reactions = relationship("CommunicationReaction", back_populates="communication", cascade="all, delete-orphan")

class ClientDocument(Base):
    __tablename__ = "client_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # contract, proposal, report, other
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    google_drive_id = Column(String, unique=True)  # Google Drive file ID
    google_drive_link = Column(String)  # Link to view in Google Drive
    vectorized = Column(Boolean, default=False)  # Whether document has been vectorized
    vectorized_at = Column(DateTime)  # When it was vectorized
    version = Column(Integer, default=1)
    uploaded_by = Column(String, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)
    
    # Relationships
    client = relationship("Client", back_populates="documents")

class ClientTeamMember(Base):
    __tablename__ = "client_team_members"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    role = Column(String)  # account_manager, project_lead, developer, designer, etc.
    
    # Permissions
    can_view_financials = Column(Boolean, default=False)
    can_edit_tasks = Column(Boolean, default=True)
    can_upload_documents = Column(Boolean, default=True)
    
    # Metadata
    added_date = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(String, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    client = relationship("Client", back_populates="team_members")

class ClientActivity(Base):
    __tablename__ = "client_activities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'))
    
    # Activity Details
    activity_type = Column(String)  # task_created, document_uploaded, status_changed, etc.
    description = Column(Text)
    meta_data = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="activities")

class TaskComment(Base):
    __tablename__ = "task_comments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('client_tasks.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_edited = Column(Boolean, default=False)
    
    # Relationships
    task = relationship("ClientTask", back_populates="comments")

class CommunicationReaction(Base):
    __tablename__ = "communication_reactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    communication_id = Column(String, ForeignKey('client_communications.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    emoji = Column(String, nullable=False)  # 👍, ❤️, 🎉, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    communication = relationship("ClientCommunication", back_populates="reactions") 

class ClientAIAnalysis(Base):
    __tablename__ = "client_ai_analysis"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    analysis_type = Column(String, nullable=False)  # 'weekly_summary', 'commitments', 'sentiment', 'suggested_tasks'
    
    # Analysis Results
    result_data = Column(JSON, nullable=False)  # Store the AI analysis results
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime)  # Optional expiration for time-sensitive data
    
    # Relationships
    client = relationship("Client", backref="ai_analyses") 

class ClientChatHistory(Base):
    __tablename__ = "client_chat_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey('clients.id'), nullable=False)
    
    # Chat content
    message = Column(Text, nullable=False)  # The AI response
    query = Column(Text)  # The user's original query
    sources = Column(JSON, default=list)  # Sources/citations if any
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    client = relationship("Client", backref="chat_history") 