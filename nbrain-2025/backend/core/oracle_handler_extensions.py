"""
Extensions for Oracle Handler
"""

import json
import uuid
from datetime import datetime
import logging
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

def store_email_for_display(oracle_handler, email_data: Dict, user_id: str, thread_id: str, db: Session):
    """Store email in oracle_emails table for display"""
    try:
        # Always start with a clean transaction state
        try:
            db.rollback()
        except:
            pass
            
        # Parse email addresses
        from_email = email_data.get('from', '')
        to_emails = [email_data.get('to', '')] if email_data.get('to') else []
        
        # Parse date
        from email.utils import parsedate_to_datetime
        try:
            email_date = parsedate_to_datetime(email_data.get('date', ''))
        except:
            email_date = datetime.utcnow()
        
        # Check if user sent this email
        is_sent = user_id in from_email if hasattr(oracle_handler, 'user_email') else False
        is_received = not is_sent
        
        # Create the email record using raw SQL to avoid model issues
        email_id = str(uuid.uuid4())
        
        # Use INSERT ... ON CONFLICT DO NOTHING to avoid constraint errors
        insert_query = text("""
            INSERT INTO oracle_emails (
                id, user_id, message_id, thread_id, subject, 
                from_email, to_emails, content, date, 
                is_sent, is_received, created_at
            ) VALUES (
                :id, :user_id, :message_id, :thread_id, :subject,
                :from_email, :to_emails, :content, :date,
                :is_sent, :is_received, :created_at
            )
            ON CONFLICT DO NOTHING
        """)
        
        db.execute(insert_query, {
            'id': email_id,
            'user_id': user_id,
            'message_id': email_data.get('id', thread_id),
            'thread_id': thread_id,
            'subject': email_data.get('subject', 'No Subject'),
            'from_email': from_email,
            'to_emails': json.dumps(to_emails),
            'content': email_data.get('body', ''),
            'date': email_date,
            'is_sent': is_sent,
            'is_received': is_received,
            'created_at': datetime.utcnow()
        })
        
        db.commit()
        
    except Exception as e:
        # Silently fail - don't break the sync process
        logger.debug(f"Could not store email for display: {e}")
        try:
            db.rollback()
        except:
            pass

# Monkey patch the method onto OracleHandler
def patch_oracle_handler():
    from .oracle_handler import OracleHandler
    OracleHandler._store_email_for_display = store_email_for_display 