"""
Super Agent API Endpoints
"""

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from .database import get_db, User
from .auth import get_current_active_user
from .super_agent_handler import super_agent_handler

import logging
logger = logging.getLogger(__name__)

# Request/Response models
class SuperAgentRequest(BaseModel):
    message: str
    workflow_id: Optional[str] = None
    context: Dict[str, Any] = {}
    client_id: Optional[str] = None

class SuperAgentResponse(BaseModel):
    response: str
    workflow_detected: Optional[Dict[str, Any]] = None
    context_update: Optional[Dict[str, Any]] = None
    workflow_complete: Optional[bool] = False
    action: Optional[Dict[str, Any]] = None
    generated_content: Optional[str] = None
    next_step: Optional[str] = None

def setup_super_agent_endpoints(app):
    """Add Super Agent endpoints to the FastAPI app"""
    
    @app.post("/super-agent/chat", response_model=SuperAgentResponse)
    async def chat_with_super_agent(
        request: SuperAgentRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Chat with the Super Agent"""
        try:
            # Add client_id to context if provided
            if request.client_id:
                request.context['client_id'] = request.client_id
            
            # Process the message
            result = super_agent_handler.process_message(
                message=request.message,
                workflow_id=request.workflow_id,
                context=request.context,
                user=current_user,
                db=db
            )
            
            return SuperAgentResponse(**result)
            
        except Exception as e:
            logger.error(f"Error in Super Agent chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/super-agent/workflows")
    async def get_available_workflows(
        current_user: User = Depends(get_current_active_user)
    ):
        """Get list of available workflows"""
        workflows = [
            {
                'id': 'social_media',
                'name': 'Create and Post to Social Media',
                'description': 'Create and publish content to Facebook, LinkedIn, or Twitter',
                'icon': 'ChatBubbleIcon'
            },
            {
                'id': 'google_docs_content',
                'name': 'Create Content & Save to Google Docs',
                'description': 'Create any type of content and save it as a Google Doc in client documents',
                'icon': 'FileTextIcon'
            },
            {
                'id': 'document_generation',
                'name': 'Generate Documents',
                'description': 'Create proposals, reports, emails, and other documents',
                'icon': 'FileTextIcon'
            },
            {
                'id': 'task_management',
                'name': 'Manage Tasks',
                'description': 'Create and update tasks for clients',
                'icon': 'CheckCircledIcon'
            },
            {
                'id': 'communication',
                'name': 'Send Communications',
                'description': 'Send emails and schedule meetings',
                'icon': 'EnvelopeClosedIcon'
            }
        ]
        
        return workflows 