#!/usr/bin/env python3
"""
Test script to check client data in the database
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set up environment
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.database import DATABASE_URL, User, CRMOpportunity
from core.client_portal_models import Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_client_data():
    """Check client data in the database"""
    try:
        engine = create_engine(DATABASE_URL)
        db = Session(engine)
        
        # Check CRM opportunities
        crm_count = db.query(CRMOpportunity).count()
        logger.info(f"Total CRM opportunities: {crm_count}")
        
        # Check for closed deals
        closed_deals = db.query(CRMOpportunity).filter(
            CRMOpportunity.deal_status == "Closed"
        ).all()
        logger.info(f"Closed deals: {len(closed_deals)}")
        
        if closed_deals:
            logger.info("\nClosed CRM deals:")
            for deal in closed_deals:
                logger.info(f"- {deal.client_opportunity} (ID: {deal.id})")
        
        # Check clients
        client_count = db.query(Client).count()
        logger.info(f"\nTotal clients in portal: {client_count}")
        
        if client_count > 0:
            clients = db.query(Client).all()
            logger.info("\nExisting clients:")
            for client in clients:
                logger.info(f"- {client.name} (ID: {client.id}, Status: {client.status.value})")
                if client.crm_opportunity_id:
                    logger.info(f"  Linked to CRM opportunity: {client.crm_opportunity_id}")
        
        # Check danny@nbrain.ai permissions
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        if user:
            logger.info(f"\nUser danny@nbrain.ai:")
            logger.info(f"- Role: {user.role}")
            logger.info(f"- Has 'clients' permission: {user.permissions.get('clients', False)}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    test_client_data() 