#!/usr/bin/env python3
"""
Create Google Drive folders for all existing clients
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from core.database import SessionLocal
from core.client_portal_models import Client, ClientActivity
from core.google_drive_handler import google_drive_handler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_folders_for_existing_clients():
    """Create Google Drive folders for all existing clients"""
    db = SessionLocal()
    
    try:
        # Get all clients
        clients = db.query(Client).all()
        logger.info(f"Found {len(clients)} clients")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for client in clients:
            logger.info(f"Processing client: {client.name}")
            
            try:
                folder_id = google_drive_handler.create_client_folder(client.name)
                
                if folder_id:
                    # Check if this is a new folder creation (not already existing)
                    existing_activity = db.query(ClientActivity).filter(
                        ClientActivity.client_id == client.id,
                        ClientActivity.activity_type == "drive_folder_created"
                    ).first()
                    
                    if not existing_activity:
                        # Create activity record
                        activity = ClientActivity(
                            client_id=client.id,
                            activity_type="drive_folder_created",
                            description=f"Google Drive folder created for client (bulk creation)",
                            meta_data={"folder_id": folder_id}
                        )
                        db.add(activity)
                        db.commit()
                        logger.info(f"✓ Created folder for {client.name}")
                        success_count += 1
                    else:
                        logger.info(f"- Folder already exists for {client.name}")
                        skip_count += 1
                else:
                    logger.warning(f"! Could not create folder for {client.name}")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"✗ Error creating folder for {client.name}: {e}")
                error_count += 1
        
        logger.info(f"\nSummary:")
        logger.info(f"  Created: {success_count}")
        logger.info(f"  Already existed: {skip_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Total: {len(clients)}")
        
    except Exception as e:
        logger.error(f"Error in bulk folder creation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_folders_for_existing_clients() 