from sqlalchemy import Column, String, Date, Text, DateTime, UUID, func
from sqlalchemy.orm import relationship

class CRMOpportunity(Base):
    __tablename__ = "crm_opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False)
    client_opportunity = Column(String, nullable=False)
    lead_start_date = Column(Date, nullable=True)
    lead_source = Column(String, nullable=True)
    referral_source = Column(String, nullable=True)
    product = Column(String, nullable=True)
    deal_status = Column(String, nullable=True)
    intro_call_date = Column(Date, nullable=True)
    todo_next_steps = Column(Text, nullable=True)
    discovery_call = Column(Date, nullable=True)
    presentation_date = Column(Date, nullable=True)
    proposal_sent = Column(Date, nullable=True)
    estimated_pipeline_value = Column(String, nullable=True)
    deal_closed = Column(Date, nullable=True)
    kickoff_scheduled = Column(Date, nullable=True)
    actual_contract_value = Column(String, nullable=True)
    monthly_fees = Column(String, nullable=True)
    commission = Column(String, nullable=True)
    invoice_setup = Column(Date, nullable=True)
    payment_1 = Column(String, nullable=True)
    payment_2 = Column(String, nullable=True)
    payment_3 = Column(String, nullable=True)
    payment_4 = Column(String, nullable=True)
    payment_5 = Column(String, nullable=True)
    payment_6 = Column(String, nullable=True)
    payment_7 = Column(String, nullable=True)
    notes_next_steps = Column(Text, nullable=True)
    
    # New contact fields
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    linkedin_profile = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    # Relationships
    documents = relationship("CRMDocument", back_populates="opportunity", cascade="all, delete-orphan")
    agent_links = relationship("CRMOpportunityAgent", back_populates="opportunity", cascade="all, delete-orphan") 