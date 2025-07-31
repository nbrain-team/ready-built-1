"""
Add oracle_emails table for storing email content
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean, ForeignKey, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("Error: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class OracleEmail(Base):
    __tablename__ = "oracle_emails"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'))
    message_id = Column(String, unique=True)
    thread_id = Column(String)
    subject = Column(String)
    from_email = Column(String)
    to_emails = Column(JSON, default=list)
    cc_emails = Column(JSON, default=list)
    content = Column(Text)
    date = Column(DateTime)
    is_sent = Column(Boolean, default=False)
    is_received = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def main():
    print("Creating oracle_emails table...")
    
    # Create the table
    Base.metadata.create_all(engine)
    
    print("oracle_emails table created successfully!")

if __name__ == "__main__":
    main() 