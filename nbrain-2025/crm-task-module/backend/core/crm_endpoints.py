from fastapi import HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
from datetime import datetime
from pydantic import BaseModel

from .database import get_db, CRMOpportunity, CRMDocument, CRMOpportunityAgent, User
from .auth import get_current_active_user

# Re-define the models here to avoid circular imports
class CRMOpportunityCreate(BaseModel):
    status: str
    client_opportunity: str
    lead_start_date: Optional[str] = None
    lead_source: Optional[str] = None
    referral_source: Optional[str] = None
    product: Optional[str] = None
    deal_status: Optional[str] = None
    intro_call_date: Optional[str] = None
    todo_next_steps: Optional[str] = None
    discovery_call: Optional[str] = None
    presentation_date: Optional[str] = None
    proposal_sent: Optional[str] = None
    estimated_pipeline_value: Optional[str] = None
    deal_closed: Optional[str] = None
    kickoff_scheduled: Optional[str] = None
    actual_contract_value: Optional[str] = None
    monthly_fees: Optional[str] = None
    commission: Optional[str] = None
    invoice_setup: Optional[str] = None
    payment_1: Optional[str] = None
    payment_2: Optional[str] = None
    payment_3: Optional[str] = None
    payment_4: Optional[str] = None
    payment_5: Optional[str] = None
    payment_6: Optional[str] = None
    payment_7: Optional[str] = None
    notes_next_steps: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linkedin_profile: Optional[str] = None
    website_url: Optional[str] = None
    lead_status: Optional[str] = None
    job_title: Optional[str] = None
    company_address: Optional[str] = None
    opportunity_type: Optional[str] = None
    owner: Optional[str] = None
    sales_pipeline: Optional[str] = None
    stage: Optional[str] = None
    est_close_date: Optional[str] = None
    close_date: Optional[str] = None
    engagement_type: Optional[str] = None
    win_likelihood: Optional[str] = None
    forecast_category: Optional[str] = None

class CRMOpportunityUpdate(BaseModel):
    status: Optional[str] = None
    client_opportunity: Optional[str] = None
    lead_start_date: Optional[str] = None
    lead_source: Optional[str] = None
    referral_source: Optional[str] = None
    product: Optional[str] = None
    deal_status: Optional[str] = None
    intro_call_date: Optional[str] = None
    todo_next_steps: Optional[str] = None
    discovery_call: Optional[str] = None
    presentation_date: Optional[str] = None
    proposal_sent: Optional[str] = None
    estimated_pipeline_value: Optional[str] = None
    deal_closed: Optional[str] = None
    kickoff_scheduled: Optional[str] = None
    actual_contract_value: Optional[str] = None
    monthly_fees: Optional[str] = None
    commission: Optional[str] = None
    invoice_setup: Optional[str] = None
    payment_1: Optional[str] = None
    payment_2: Optional[str] = None
    payment_3: Optional[str] = None
    payment_4: Optional[str] = None
    payment_5: Optional[str] = None
    payment_6: Optional[str] = None
    payment_7: Optional[str] = None
    notes_next_steps: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linkedin_profile: Optional[str] = None
    website_url: Optional[str] = None
    lead_status: Optional[str] = None
    job_title: Optional[str] = None
    company_address: Optional[str] = None
    opportunity_type: Optional[str] = None
    owner: Optional[str] = None
    sales_pipeline: Optional[str] = None
    stage: Optional[str] = None
    est_close_date: Optional[str] = None
    close_date: Optional[str] = None
    engagement_type: Optional[str] = None
    win_likelihood: Optional[str] = None
    forecast_category: Optional[str] = None

class CRMOpportunityResponse(BaseModel):
    id: str
    status: str
    client_opportunity: str
    lead_start_date: Optional[str]
    lead_source: Optional[str]
    referral_source: Optional[str]
    product: Optional[str]
    deal_status: Optional[str]
    intro_call_date: Optional[str]
    todo_next_steps: Optional[str]
    discovery_call: Optional[str]
    presentation_date: Optional[str]
    proposal_sent: Optional[str]
    estimated_pipeline_value: Optional[str]
    deal_closed: Optional[str]
    kickoff_scheduled: Optional[str]
    actual_contract_value: Optional[str]
    monthly_fees: Optional[str]
    commission: Optional[str]
    invoice_setup: Optional[str]
    payment_1: Optional[str]
    payment_2: Optional[str] = None
    payment_3: Optional[str] = None
    payment_4: Optional[str] = None
    payment_5: Optional[str] = None
    payment_6: Optional[str] = None
    payment_7: Optional[str] = None
    notes_next_steps: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    linkedin_profile: Optional[str]
    website_url: Optional[str]
    lead_status: Optional[str]
    job_title: Optional[str]
    company_address: Optional[str]
    opportunity_type: Optional[str]
    owner: Optional[str]
    sales_pipeline: Optional[str]
    stage: Optional[str]
    est_close_date: Optional[str]
    close_date: Optional[str]
    engagement_type: Optional[str]
    win_likelihood: Optional[str]
    forecast_category: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    documents: List[dict] = []
    agent_links: List[dict] = []

class CRMDocumentCreate(BaseModel):
    name: str
    type: str  # 'link' or 'file'
    url: Optional[str] = None

class CRMAgentLink(BaseModel):
    agent_idea_id: str
    notes: Optional[str] = None

def setup_crm_endpoints(app):
    """Add CRM endpoints to the FastAPI app."""
    
    @app.post("/crm/opportunities", response_model=CRMOpportunityResponse)
    async def create_opportunity(
        opportunity: CRMOpportunityCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Create a new CRM opportunity."""
        db_opportunity = CRMOpportunity(
            id=str(uuid.uuid4()),
            **opportunity.dict(),
            user_id=current_user.id
        )
        db.add(db_opportunity)
        db.commit()
        db.refresh(db_opportunity)
        
        # Format response with relationships
        response = CRMOpportunityResponse(
            **{k: v for k, v in db_opportunity.__dict__.items() if not k.startswith('_')},
            documents=[],
            agent_links=[]
        )
        return response

    @app.get("/crm/opportunities", response_model=List[CRMOpportunityResponse])
    async def get_opportunities(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Get all CRM opportunities (shared across all users)."""
        try:
            opportunities = db.query(CRMOpportunity).order_by(CRMOpportunity.created_at.desc()).all()
            
            result = []
            for opp in opportunities:
                try:
                    # Safely get relationships
                    documents = []
                    agent_links = []
                    
                    try:
                        documents = [{
                            "id": doc.id,
                            "name": doc.name,
                            "type": doc.type,
                            "url": doc.url,
                            "uploaded_at": doc.uploaded_at
                        } for doc in opp.documents]
                    except Exception as e:
                        print(f"Error loading documents for opportunity {opp.id}: {e}")
                    
                    try:
                        agent_links = [{
                            "id": link.id,
                            "agent_idea_id": link.agent_idea_id,
                            "agent_title": link.agent_idea.title if link.agent_idea else None,
                            "linked_at": link.linked_at,
                            "notes": link.notes
                        } for link in opp.agent_links]
                    except Exception as e:
                        print(f"Error loading agent links for opportunity {opp.id}: {e}")
                    
                    # Build response
                    opp_dict = {k: v for k, v in opp.__dict__.items() if not k.startswith('_')}
                    opp_dict['documents'] = documents
                    opp_dict['agent_links'] = agent_links
                    
                    result.append(CRMOpportunityResponse(**opp_dict))
                except Exception as e:
                    print(f"Error serializing opportunity {opp.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    
            return result
        except Exception as e:
            print(f"Error in get_opportunities: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/crm/opportunities/{opportunity_id}", response_model=CRMOpportunityResponse)
    async def get_opportunity(
        opportunity_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Get a specific CRM opportunity (accessible by any user)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return CRMOpportunityResponse(
            **{k: v for k, v in opportunity.__dict__.items() if not k.startswith('_')},
            documents=[{
                "id": doc.id,
                "name": doc.name,
                "type": doc.type,
                "url": doc.url,
                "uploaded_at": doc.uploaded_at
            } for doc in opportunity.documents],
            agent_links=[{
                "id": link.id,
                "agent_idea_id": link.agent_idea_id,
                "agent_title": link.agent_idea.title if link.agent_idea else None,
                "linked_at": link.linked_at,
                "notes": link.notes
            } for link in opportunity.agent_links]
        )

    @app.put("/crm/opportunities/{opportunity_id}", response_model=CRMOpportunityResponse)
    async def update_opportunity(
        opportunity_id: str,
        update: CRMOpportunityUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Update a CRM opportunity (any user can update)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Store old status to check if it changed
        old_deal_status = opportunity.deal_status
        
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(opportunity, field, value)
        
        opportunity.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(opportunity)
        
        # Check if deal_status changed to "Closed" and create client
        print(f"DEBUG: Checking deal_status change - old: '{old_deal_status}', new: '{opportunity.deal_status}'")
        if (old_deal_status or "").lower() != "closed" and (opportunity.deal_status or "").lower() == "closed":
            try:
                # Import here to avoid circular imports
                from .client_portal_handler import client_portal_handler
                
                # Create client from the closed opportunity
                client = client_portal_handler.create_client_from_crm(opportunity_id, db)
                
                # Log success
                print(f"Successfully created client '{client.name}' from closed opportunity '{opportunity.client_opportunity}'")
            except Exception as e:
                # Log error but don't fail the opportunity update
                print(f"Error creating client from opportunity: {e}")
                import traceback
                traceback.print_exc()
        
        return CRMOpportunityResponse(
            **{k: v for k, v in opportunity.__dict__.items() if not k.startswith('_')},
            documents=[{
                "id": doc.id,
                "name": doc.name,
                "type": doc.type,
                "url": doc.url,
                "uploaded_at": doc.uploaded_at
            } for doc in opportunity.documents],
            agent_links=[{
                "id": link.id,
                "agent_idea_id": link.agent_idea_id,
                "agent_title": link.agent_idea.title if link.agent_idea else None,
                "linked_at": link.linked_at,
                "notes": link.notes
            } for link in opportunity.agent_links]
        )

    @app.delete("/crm/opportunities/{opportunity_id}")
    async def delete_opportunity(
        opportunity_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Delete a CRM opportunity (any user can delete)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        db.delete(opportunity)
        db.commit()
        return {"message": "Opportunity deleted successfully"}

    @app.post("/crm/opportunities/{opportunity_id}/documents")
    async def add_document_link(
        opportunity_id: str,
        document: CRMDocumentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Add a document link to an opportunity (any user can add)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        db_document = CRMDocument(
            id=str(uuid.uuid4()),
            name=document.name,
            type=document.type,
            url=document.url,
            opportunity_id=opportunity_id
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return {
            "id": db_document.id,
            "name": db_document.name,
            "type": db_document.type,
            "url": db_document.url,
            "uploaded_at": db_document.uploaded_at
        }

    @app.post("/crm/opportunities/{opportunity_id}/upload")
    async def upload_document(
        opportunity_id: str,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Upload a document file to an opportunity (any user can upload)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Create upload directory if it doesn't exist
        upload_dir = f"uploads/crm/{opportunity_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = f"{upload_dir}/{file_id}{file_extension}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create database record
        db_document = CRMDocument(
            id=file_id,
            name=file.filename,
            type="file",
            file_path=file_path,
            mime_type=file.content_type,
            size=len(content),
            opportunity_id=opportunity_id
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return {
            "id": db_document.id,
            "name": db_document.name,
            "type": db_document.type,
            "mime_type": db_document.mime_type,
            "size": db_document.size,
            "uploaded_at": db_document.uploaded_at
        }

    @app.delete("/crm/opportunities/{opportunity_id}/documents/{document_id}")
    async def delete_document(
        opportunity_id: str,
        document_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Delete a document from an opportunity (any user can delete)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        document = db.query(CRMDocument).filter(
            CRMDocument.id == document_id,
            CRMDocument.opportunity_id == opportunity_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file if it exists
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.delete(document)
        db.commit()
        return {"message": "Document deleted successfully"}

    @app.post("/crm/opportunities/{opportunity_id}/agent-links")
    async def link_agent_idea(
        opportunity_id: str,
        link: CRMAgentLink,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Link an agent idea to an opportunity (any user can link)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Check if link already exists
        existing_link = db.query(CRMOpportunityAgent).filter(
            CRMOpportunityAgent.opportunity_id == opportunity_id,
            CRMOpportunityAgent.agent_idea_id == link.agent_idea_id
        ).first()
        
        if existing_link:
            raise HTTPException(status_code=400, detail="Agent already linked to this opportunity")
        
        db_link = CRMOpportunityAgent(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            agent_idea_id=link.agent_idea_id,
            notes=link.notes
        )
        db.add(db_link)
        db.commit()
        db.refresh(db_link)
        
        return {
            "id": db_link.id,
            "agent_idea_id": db_link.agent_idea_id,
            "linked_at": db_link.linked_at,
            "notes": db_link.notes
        }

    @app.delete("/crm/opportunities/{opportunity_id}/agent-links/{link_id}")
    async def unlink_agent_idea(
        opportunity_id: str,
        link_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Remove an agent idea link from an opportunity (any user can unlink)."""
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        link = db.query(CRMOpportunityAgent).filter(
            CRMOpportunityAgent.id == link_id,
            CRMOpportunityAgent.opportunity_id == opportunity_id
        ).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        db.delete(link)
        db.commit()
        return {"message": "Agent link removed successfully"}

    @app.get("/crm/opportunities/debug")
    async def debug_opportunities(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        """Debug endpoint to check raw CRM data"""
        try:
            # Get count
            count = db.query(CRMOpportunity).count()
            
            # Get first 5 records raw
            opportunities = db.query(CRMOpportunity).limit(5).all()
            
            # Check for any with null status
            null_status_count = db.query(CRMOpportunity).filter(
                CRMOpportunity.status == None
            ).count()
            
            return {
                "total_count": count,
                "null_status_count": null_status_count,
                "sample_records": [
                    {
                        "id": opp.id,
                        "status": opp.status,
                        "client_opportunity": opp.client_opportunity,
                        "created_at": str(opp.created_at) if opp.created_at else None,
                        "lead_status": opp.lead_status,
                        "stage": opp.stage
                    }
                    for opp in opportunities
                ],
                "table_exists": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "table_exists": False
            } 