#!/usr/bin/env python3
"""
Create Client Portal tables if they don't exist
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect
from core.database import DATABASE_URL, Base
from core.client_portal_models import (
    Client, ClientTask, ClientCommunication, ClientDocument,
    ClientTeamMember, ClientActivity, TaskComment, CommunicationReaction
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_client_portal_tables():
    """Create all client portal tables if they don't exist"""
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Get list of existing tables
        existing_tables = inspector.get_table_names()
        
        # List of client portal tables
        client_portal_tables = [
            'clients',
            'client_tasks',
            'client_communications',
            'client_documents',
            'client_team_members',
            'client_activities',
            'task_comments',
            'communication_reactions'
        ]
        
        # Check which tables need to be created
        tables_to_create = [table for table in client_portal_tables if table not in existing_tables]
        
        if tables_to_create:
            logger.info(f"Creating client portal tables: {tables_to_create}")
            Base.metadata.create_all(bind=engine, tables=[
                Base.metadata.tables[table] for table in Base.metadata.tables 
                if table in tables_to_create
            ])
            logger.info("Client portal tables created successfully!")
        else:
            logger.info("All client portal tables already exist.")
        
        # Verify all tables were created
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        for table in client_portal_tables:
            if table in existing_tables:
                logger.info(f"✓ Table '{table}' exists")
            else:
                logger.error(f"✗ Table '{table}' was not created")
        
    except Exception as e:
        logger.error(f"Error creating client portal tables: {e}")
        raise

if __name__ == "__main__":
    create_client_portal_tables() 