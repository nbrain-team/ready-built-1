#!/usr/bin/env python3
"""
Quick CRM import script for running in production.
Copy and paste this into Render's Python shell.
"""

import os
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, CRMOpportunity, User

# Sample data from your CSV
crm_data = [
    {
        "status": "Active",
        "client_opportunity": "WD40",
        "lead_start_date": "10/29/24",
        "lead_source": "Network",
        "referral_source": "Alex Repola",
        "product": "Agency",
        "deal_status": "Warm Lead",
        "todo_next_steps": "Follow Up"
    },
    {
        "status": "Active",
        "client_opportunity": "Inveterate",
        "lead_start_date": "10/29/24",
        "lead_source": "Network",
        "referral_source": "Cary Johnson",
        "product": "Agency",
        "deal_status": "Warm Lead",
        "todo_next_steps": "Outreach"
    },
    {
        "status": "Active",
        "client_opportunity": "Ignite Visibility",
        "lead_start_date": "10/29/24",
        "lead_source": "Network",
        "referral_source": "Danny DeMichele",
        "product": "Franchise",
        "deal_status": "Warm Lead",
        "todo_next_steps": "Outreach"
    },
    {
        "status": "Active",
        "client_opportunity": "Threshold Brands",
        "lead_start_date": "10/30/24",
        "lead_source": "Network",
        "referral_source": "Cary Johnson",
        "product": "Franchise",
        "deal_status": "Proposal",
        "intro_call_date": "01/29/25",
        "todo_next_steps": "Check-In Call",
        "discovery_call": "Yes",
        "presentation_date": "11/01/24",
        "estimated_pipeline_value": "$30,000.00"
    },
    {
        "status": "Active",
        "client_opportunity": "American Dream TV",
        "lead_start_date": "03/25/25",
        "lead_source": "Network",
        "referral_source": "Dan Caufield",
        "product": "Custom",
        "deal_status": "Discovery",
        "todo_next_steps": "CLOSED",
        "discovery_call": "Yes",
        "presentation_date": "04/03/25",
        "estimated_pipeline_value": "$75,000.00",
        "deal_closed": "Yes",
        "kickoff_scheduled": "Yes",
        "actual_contract_value": "$75,000.00",
        "monthly_fees": "$25,000.00",
        "commission": "$5,000.00",
        "payment_1": "Received"
    }
]

def quick_import():
    """Quick import of CRM data."""
    db = SessionLocal()
    
    try:
        # Find the user
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        if not user:
            print("User danny@nbrain.ai not found!")
            return
        
        # Import opportunities
        for data in crm_data:
            opp = CRMOpportunity(
                id=str(uuid.uuid4()),
                user_id=user.id,
                **data
            )
            db.add(opp)
            print(f"Added: {data['client_opportunity']}")
        
        db.commit()
        print(f"\nSuccessfully imported {len(crm_data)} opportunities!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    quick_import() 