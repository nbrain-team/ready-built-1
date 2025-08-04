import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, func, Text, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment. Please set it.")

# Configure engine with FIXED connection pooling for concurrent requests
engine_config = {
    "pool_size": 10,  # Increased from 5 to handle concurrent requests
    "max_overflow": 20,  # Increased from 10 for better peak handling
    "pool_timeout": 30,  # Keep timeout at 30 seconds
    "pool_recycle": 300,  # Recycle connections after 5 minutes
    "pool_pre_ping": True,  # Verify connections before using them
    "echo_pool": False,  # Disable pool logging in production
    "poolclass": pool.QueuePool,  # Use QueuePool explicitly
}

# Add SSL configuration for PostgreSQL
if DATABASE_URL.startswith("postgresql://"):
    # Convert postgresql:// to postgresql+psycopg2:// for better compatibility
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    # Add SSL mode if not present
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

logger.info("Creating database engine with optimized connection pooling...")
engine = create_engine(DATABASE_URL, **engine_config)

# Use scoped_session for thread-safe session management
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(session_factory)

Base = declarative_base()

# --- Database Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # User profile fields
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    
    # Role and permissions
    role = Column(String, default="user")  # "user" or "admin"
    permissions = Column(JSON, default=lambda: {
        "chat": True, 
        "history": True, 
        "email-personalizer": True, 
        "agent-ideas": True, 
        "knowledge": True, 
        "crm": True, 
        "clients": True, 
        "oracle": True
    })  # Module access permissions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    conversations = relationship("ChatSession", back_populates="user")
    agent_ideas = relationship("AgentIdea", back_populates="user")
    crm_opportunities = relationship("CRMOpportunity", back_populates="user")


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    messages = Column(JSON, nullable=False)
    
    user_id = Column(String, ForeignKey('users.id'))
    user = relationship("User", back_populates="conversations")


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
    
    user_id = Column(String, ForeignKey('users.id'))
    user = relationship("User", back_populates="agent_ideas")
    
    # Add relationship to CRM opportunities
    crm_opportunities = relationship("CRMOpportunityAgent", back_populates="agent_idea")

# Import Client models first to ensure they're available for foreign keys
try:
    from .client_portal_models import Client
except ImportError:
    pass  # Models not yet created

# Import Read.ai models after initial setup to avoid circular imports
# These will be available after the models are created
try:
    from .readai_models import ReadAIIntegration, ReadAIMeeting
except ImportError:
    pass  # Models not yet created

# Import RAG models
from .rag_models import DataSource, DataEntry, RAGChatHistory, RAGConfiguration

# Import Salon models
from .salon_models import (
    SalonLocation, SalonStaff, StaffPerformance, 
    SalonClient, SalonAppointment, StaffPrediction, SalonAnalytics
)


class CRMOpportunity(Base):
    __tablename__ = 'crm_opportunities'
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False)  # Active, Closed, Dead
    client_opportunity = Column(String, nullable=False)
    lead_start_date = Column(String, nullable=True)
    lead_source = Column(String, nullable=True)
    referral_source = Column(String, nullable=True)
    product = Column(String, nullable=True)
    deal_status = Column(String, nullable=True)  # Warm Lead, Proposal, Discovery, etc.
    intro_call_date = Column(String, nullable=True)
    todo_next_steps = Column(Text, nullable=True)
    discovery_call = Column(String, nullable=True)
    presentation_date = Column(String, nullable=True)
    proposal_sent = Column(String, nullable=True)
    estimated_pipeline_value = Column(String, nullable=True)
    deal_closed = Column(String, nullable=True)
    kickoff_scheduled = Column(String, nullable=True)
    actual_contract_value = Column(String, nullable=True)
    monthly_fees = Column(String, nullable=True)
    commission = Column(String, nullable=True)
    invoice_setup = Column(String, nullable=True)
    payment_1 = Column(String, nullable=True)
    payment_2 = Column(String, nullable=True)
    payment_3 = Column(String, nullable=True)
    payment_4 = Column(String, nullable=True)
    payment_5 = Column(String, nullable=True)
    payment_6 = Column(String, nullable=True)
    payment_7 = Column(String, nullable=True)
    notes_next_steps = Column(Text, nullable=True)
    
    # Contact fields
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    linkedin_profile = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    
    # New fields
    lead_status = Column(String, nullable=True)  # New Lead, Working Lead, etc.
    job_title = Column(String, nullable=True)
    company_address = Column(Text, nullable=True)
    
    # Additional expanded view fields
    opportunity_type = Column(String, nullable=True)  # Qualified Lead, Current Client
    owner = Column(String, nullable=True)  # Salesperson
    sales_pipeline = Column(String, nullable=True)  # New Business, Renewals, Upsell
    stage = Column(String, nullable=True)  # Warm Lead, Cold Lead, Introduction, etc.
    est_close_date = Column(String, nullable=True)  # Estimated close date
    close_date = Column(String, nullable=True)  # Actual close date
    engagement_type = Column(String, nullable=True)  # MRR, One-time
    win_likelihood = Column(String, nullable=True)  # Percentage likelihood
    forecast_category = Column(String, nullable=True)  # Pipeline, Best Case, Committed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user_id = Column(String, ForeignKey('users.id'))
    user = relationship("User", back_populates="crm_opportunities")
    
    # Relationships
    documents = relationship("CRMDocument", back_populates="opportunity", cascade="all, delete-orphan")
    agent_links = relationship("CRMOpportunityAgent", back_populates="opportunity", cascade="all, delete-orphan")


class CRMDocument(Base):
    __tablename__ = 'crm_documents'
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # link, file
    url = Column(String, nullable=True)  # For links
    file_path = Column(String, nullable=True)  # For uploaded files
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    opportunity_id = Column(String, ForeignKey('crm_opportunities.id'))
    opportunity = relationship("CRMOpportunity", back_populates="documents")


class CRMOpportunityAgent(Base):
    __tablename__ = 'crm_opportunity_agents'
    
    id = Column(String, primary_key=True, index=True)
    opportunity_id = Column(String, ForeignKey('crm_opportunities.id'))
    agent_idea_id = Column(String, ForeignKey('agent_ideas.id'))
    linked_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    
    opportunity = relationship("CRMOpportunity", back_populates="agent_links")
    agent_idea = relationship("AgentIdea", back_populates="crm_opportunities")


def get_db():
    """Dependency to get a DB session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Use close() instead of remove() to avoid state conflicts

def create_tables():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(bind=engine) 