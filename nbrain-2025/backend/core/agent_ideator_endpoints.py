"""
Agent Ideator API Endpoints
Extracted and refactored for standalone use
"""

from fastapi import HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import logging

# You'll need to import these from your main application
# from .database import get_db, User, AgentIdea
# from .auth import get_current_active_user
# from .ideator_handler import process_ideation_message, process_edit_message

logger = logging.getLogger(__name__)

# Pydantic models
class AgentIdeaCreate(BaseModel):
    title: str
    summary: str
    steps: List[str]
    agent_stack: dict
    client_requirements: List[str]
    conversation_history: Optional[List[dict]] = None
    agent_type: Optional[str] = None
    implementation_estimate: Optional[dict] = None
    security_considerations: Optional[dict] = None
    future_enhancements: Optional[List[dict]] = None

class AgentIdeaUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    steps: Optional[List[str]] = None
    agent_stack: Optional[dict] = None
    client_requirements: Optional[List[str]] = None
    status: Optional[str] = None
    implementation_estimate: Optional[dict] = None

class AgentIdeaResponse(BaseModel):
    id: str
    title: str
    summary: str
    steps: List[str]
    agent_stack: dict
    client_requirements: List[str]
    status: str
    agent_type: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    implementation_estimate: Optional[dict]
    security_considerations: Optional[dict]
    future_enhancements: Optional[List[dict]]

class IdeationMessage(BaseModel):
    message: str
    conversation_history: List[dict] = []

class EditMessage(BaseModel):
    message: str
    current_spec: dict
    conversation_history: List[dict] = []

class MoveToProductionRequest(BaseModel):
    spec_id: Optional[str]
    spec_details: dict


def setup_agent_ideator_endpoints(app, get_db, get_current_active_user, AgentIdea, process_ideation_message, process_edit_message):
    """
    Setup agent ideator endpoints on the FastAPI app
    
    Args:
        app: FastAPI application instance
        get_db: Database session dependency
        get_current_active_user: Auth dependency
        AgentIdea: SQLAlchemy model for agent ideas
        process_ideation_message: Handler function for ideation
        process_edit_message: Handler function for editing
    """
    
    @app.post("/agent-ideas", response_model=AgentIdeaResponse)
    async def create_agent_idea(
        idea: AgentIdeaCreate,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_active_user)
    ):
        """Create a new agent idea from the ideation process."""
        db_idea = AgentIdea(
            id=str(uuid.uuid4()),
            title=idea.title,
            summary=idea.summary,
            steps=idea.steps,
            agent_stack=idea.agent_stack,
            client_requirements=idea.client_requirements,
            conversation_history=idea.conversation_history,
            agent_type=idea.agent_type,
            implementation_estimate=idea.implementation_estimate,
            security_considerations=idea.security_considerations,
            future_enhancements=idea.future_enhancements,
            user_id=current_user.id
        )
        db.add(db_idea)
        db.commit()
        db.refresh(db_idea)
        return db_idea

    @app.get("/agent-ideas", response_model=List[AgentIdeaResponse])
    async def get_agent_ideas(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_active_user)
    ):
        """Get all agent ideas (shared across all users)."""
        return db.query(AgentIdea).order_by(AgentIdea.created_at.desc()).all()

    @app.get("/agent-ideas/{idea_id}", response_model=AgentIdeaResponse)
    async def get_agent_idea(
        idea_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_active_user)
    ):
        """Get a specific agent idea (accessible by any user)."""
        idea = db.query(AgentIdea).filter(
            AgentIdea.id == idea_id
        ).first()
        if not idea:
            raise HTTPException(status_code=404, detail="Agent idea not found")
        return idea

    @app.put("/agent-ideas/{idea_id}", response_model=AgentIdeaResponse)
    async def update_agent_idea(
        idea_id: str,
        update: AgentIdeaUpdate,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_active_user)
    ):
        """Update an existing agent idea (any user can update)."""
        idea = db.query(AgentIdea).filter(
            AgentIdea.id == idea_id
        ).first()
        if not idea:
            raise HTTPException(status_code=404, detail="Agent idea not found")
        
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(idea, field, value)
        
        idea.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(idea)
        return idea

    @app.put("/agent-ideas/{idea_id}/full-update", response_model=AgentIdeaResponse)
    async def full_update_agent_idea(
        idea_id: str,
        spec_data: dict,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_active_user)
    ):
        """Full update of an agent idea with all fields."""
        idea = db.query(AgentIdea).filter(
            AgentIdea.id == idea_id
        ).first()
        if not idea:
            raise HTTPException(status_code=404, detail="Agent idea not found")
        
        # Update all fields from spec_data
        for field, value in spec_data.items():
            if hasattr(idea, field) and field not in ['id', 'created_at', 'user_id']:
                setattr(idea, field, value)
        
        idea.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(idea)
        return idea

    @app.delete("/agent-ideas/{idea_id}")
    async def delete_agent_idea(
        idea_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_active_user)
    ):
        """Delete an agent idea (any user can delete)."""
        idea = db.query(AgentIdea).filter(
            AgentIdea.id == idea_id
        ).first()
        if not idea:
            raise HTTPException(status_code=404, detail="Agent idea not found")
        
        db.delete(idea)
        db.commit()
        return {"message": "Agent idea deleted successfully"}

    @app.post("/agent-ideator/chat")
    async def agent_ideator_chat(
        message: IdeationMessage,
        current_user = Depends(get_current_active_user)
    ):
        """Handle the conversational agent ideation process."""
        response = await process_ideation_message(
            message.message,
            message.conversation_history
        )
        
        # Check if it's a streaming response
        if response.get("stream"):
            async def stream_generator():
                try:
                    async for chunk in response["generator"]:
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    logger.error(f"Error during ideation stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            # Non-streaming response
            return response

    @app.post("/agent-ideator/edit")
    async def agent_ideator_edit(
        message: EditMessage,
        current_user = Depends(get_current_active_user)
    ):
        """Handle the conversational agent editing process."""
        response = await process_edit_message(
            message.message,
            message.current_spec,
            message.conversation_history
        )
        
        # Check if it's a streaming response
        if response.get("stream"):
            async def stream_generator():
                try:
                    async for chunk in response["generator"]:
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    logger.error(f"Error during edit stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            # Non-streaming response
            return response

    @app.post("/agent-ideas/move-to-production")
    async def move_agent_to_production(
        request: MoveToProductionRequest,
        current_user = Depends(get_current_active_user)
    ):
        """Send agent specification to production team (via email for now)."""
        try:
            # Format the specification details
            spec = request.spec_details
            email_content = f"""
New Agent Production Request from {current_user.email}

Agent Title: {spec.get('title', 'N/A')}
Type: {spec.get('agent_type', 'N/A')}

Summary:
{spec.get('summary', 'N/A')}

Implementation Steps:
{chr(10).join(f"- {step}" for step in spec.get('steps', []))}

Technical Stack:
{json.dumps(spec.get('agent_stack', {}), indent=2)}

Client Requirements:
{chr(10).join(f"- {req}" for req in spec.get('client_requirements', []))}

Cost Estimate:
Traditional Approach: {spec.get('implementation_estimate', {}).get('traditional_approach', {}).get('total_cost', 'N/A')}
AI-Powered Approach: {spec.get('implementation_estimate', {}).get('ai_powered_approach', {}).get('total_cost', 'N/A')}

Specification ID: {spec.get('id', 'N/A')}
User Email: {current_user.email}
"""
            
            # For now, just log it - in production, you'd send an actual email
            logger.info(f"Production request from {current_user.email}:")
            logger.info(email_content)
            
            # In a real implementation, you would send an email here
            # Example email sending code (requires SMTP configuration):
            """
            msg = MIMEMultipart()
            msg['From'] = 'system@nbrain.ai'
            msg['To'] = 'danny@nbrain.ai'
            msg['Subject'] = f'New Agent Production Request: {spec.get("title", "Untitled")}'
            msg.attach(MIMEText(email_content, 'plain'))
            
            # Send email via SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('your-email@gmail.com', 'your-password')
                server.send_message(msg)
            """
            
            return {"message": "Agent specification sent to production team successfully"}
        except Exception as e:
            logger.error(f"Error sending to production: {e}")
            raise HTTPException(status_code=500, detail="Failed to send specification to production team") 