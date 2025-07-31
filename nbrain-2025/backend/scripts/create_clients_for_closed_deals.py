import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import get_db, CRMOpportunity, Client, ClientTask, ClientActivity
from datetime import datetime
import json

def create_clients_for_closed_deals():
    # Get database session
    db = next(get_db())
    
    try:
        # First, get all closed deals
        closed_deals = db.query(CRMOpportunity).filter(
            CRMOpportunity.deal_status == 'Closed'
        ).all()
        
        print(f"\nFound {len(closed_deals)} closed deals in CRM")
        
        if not closed_deals:
            print("No closed deals found.")
            return
        
        # Check which ones already have client portal records
        existing_crm_ids = {client.crm_opportunity_id for client in 
                           db.query(Client).filter(Client.crm_opportunity_id.isnot(None)).all()}
        
        clients_created = 0
        
        for deal in closed_deals:
            if deal.id in existing_crm_ids:
                print(f"\n✓ Client portal already exists for: {deal.client_opportunity}")
                continue
            
            print(f"\nCreating client portal for: {deal.client_opportunity}")
            print(f"   Contact: {deal.contact_name} ({deal.contact_email})")
            if deal.actual_contract_value:
                print(f"   Deal Value: ${float(deal.actual_contract_value):,.2f}")
            
            # Create the client record
            client = Client(
                name=deal.client_opportunity,
                contact_name=deal.contact_name or "Unknown",
                contact_email=deal.contact_email or "no-email@example.com",
                status='active',
                health_score=85,  # Default health score
                onboarding_date=deal.deal_closed or datetime.now().strftime('%Y-%m-%d'),
                contract_value=float(deal.actual_contract_value) if deal.actual_contract_value else 0.0,
                notes=f"Converted from CRM deal. Original notes: {deal.notes_next_steps or 'None'}",
                crm_opportunity_id=deal.id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(client)
            db.flush()  # Get the client ID
            
            # Create default kickoff tasks
            kickoff_tasks = [
                ("Schedule kickoff meeting", "Schedule initial kickoff meeting with client", "high", 1),
                ("Gather requirements", "Collect detailed requirements and project scope", "high", 2),
                ("Setup communication channels", "Setup Slack/Teams and invite client team", "medium", 3),
                ("Create project timeline", "Develop and share project timeline with milestones", "medium", 4),
                ("Initial documentation", "Create initial project documentation and share access", "low", 5)
            ]
            
            for title, description, priority, order in kickoff_tasks:
                task = ClientTask(
                    client_id=client.id,
                    title=title,
                    description=description,
                    status='todo',
                    priority=priority,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    task_order=order
                )
                db.add(task)
            
            # Create initial activity log
            activity = ClientActivity(
                client_id=client.id,
                activity_type='client_created',
                description='Client portal created from closed CRM deal',
                user_id=1,  # System user
                created_at=datetime.now()
            )
            db.add(activity)
            
            clients_created += 1
            print(f"   ✓ Client portal created with ID: {client.id}")
            print(f"   ✓ Created 5 kickoff tasks")
        
        db.commit()
        print(f"\nSummary: Created {clients_created} new client portal records")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating client portal records for closed CRM deals...")
    create_clients_for_closed_deals() 