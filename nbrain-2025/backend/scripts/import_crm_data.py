#!/usr/bin/env python3
"""
Import CRM data from CSV file into the database.
"""

import os
import sys
import csv
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path to import from core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import CRMOpportunity, User

load_dotenv()

def import_crm_data(csv_file_path, user_email):
    """Import CRM data from CSV file."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    # Create engine and session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find user
        user = session.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"User with email {user_email} not found")
            sys.exit(1)
        
        # Read CSV file
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            opportunities_created = 0
            
            for row in reader:
                # Map CSV columns to database fields
                opportunity = CRMOpportunity(
                    id=str(uuid.uuid4()),
                    status=row.get('Status', ''),
                    client_opportunity=row.get('Client Opportunity', ''),
                    lead_start_date=row.get('Lead Start Date', None) or None,
                    lead_source=row.get('Lead Source', None) or None,
                    referral_source=row.get('Referral Source', None) or None,
                    product=row.get('Product', None) or None,
                    deal_status=row.get('Status', None) or None,  # Second Status column
                    intro_call_date=row.get('Intro Call Date', None) or None,
                    todo_next_steps=row.get('To-Do / Next Steps', None) or None,
                    discovery_call=row.get('Discovery Call', None) or None,
                    presentation_date=row.get('Presentation Date', None) or None,
                    proposal_sent=row.get('Proposal sent to client?', None) or None,
                    estimated_pipeline_value=row.get('Estimated Pipeline Value', None) or None,
                    deal_closed=row.get('Deal closed (Yes or No)', None) or None,
                    kickoff_scheduled=row.get('Kickoff call scheduled (y/n)', None) or None,
                    actual_contract_value=row.get('Actual Contract Value', None) or None,
                    monthly_fees=row.get('Monthly Fees', None) or None,
                    commission=row.get('Commission $$', None) or None,
                    invoice_setup=row.get('Invoice         Set Up', None) or None,
                    payment_1=row.get('Payment 1', None) or None,
                    payment_2=row.get('Payment 2', None) or None,
                    payment_3=row.get('Payment 3', None) or None,
                    payment_4=row.get('Payment 4', None) or None,
                    payment_5=row.get('Payment 5', None) or None,
                    payment_6=row.get('Payment 6', None) or None,
                    payment_7=row.get('Payment 7', None) or None,
                    notes_next_steps=row.get('Notes on next steps.', None) or None,
                    user_id=user.id
                )
                
                session.add(opportunity)
                opportunities_created += 1
                print(f"Added: {row.get('Client Opportunity', 'Unknown')}")
            
            session.commit()
            print(f"\nSuccessfully imported {opportunities_created} opportunities!")
            
    except Exception as e:
        print(f"Error importing data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python import_crm_data.py <csv_file_path> <user_email>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    user_email = sys.argv[2]
    
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        sys.exit(1)
    
    import_crm_data(csv_file_path, user_email) 