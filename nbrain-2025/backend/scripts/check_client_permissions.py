#!/usr/bin/env python3
"""
Check and fix client portal permissions for danny@nbrain.ai
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.database import DATABASE_URL, User
from core.client_portal_models import Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_permissions():
    """Check and fix client portal permissions"""
    try:
        engine = create_engine(DATABASE_URL)
        db = Session(engine)
        
        # Find danny@nbrain.ai
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        
        if not user:
            logger.error("User danny@nbrain.ai not found!")
            return
        
        logger.info(f"Found user: {user.email}")
        logger.info(f"Role: {user.role}")
        logger.info(f"Current permissions: {user.permissions}")
        
        # Ensure user has clients permission
        if not user.permissions:
            user.permissions = {}
        
        if not user.permissions.get('clients', False):
            logger.info("Adding 'clients' permission...")
            user.permissions['clients'] = True
            db.commit()
            logger.info("Permission added successfully!")
        else:
            logger.info("User already has 'clients' permission")
        
        # Check if there are any clients in the database
        client_count = db.query(Client).count()
        logger.info(f"\nTotal clients in database: {client_count}")
        
        if client_count > 0:
            clients = db.query(Client).all()
            logger.info("\nExisting clients:")
            for client in clients:
                logger.info(f"- {client.name} (ID: {client.id}, Status: {client.status.value})")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    check_and_fix_permissions() 