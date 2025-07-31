"""
Client AI API Endpoints
"""

from fastapi import HTTPException, Depends, Response
from sqlalchemy.orm import Session
from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from .database import get_db, User
from .auth import get_current_active_user
from .client_ai_handler import client_ai_handler
from .client_portal_models import ClientAIAnalysis
import json
import logging

logger = logging.getLogger(__name__)

# Request/Response models
class ClientSearchRequest(BaseModel):
    query: str

class ClientAIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    generated_at: Optional[datetime] = None
    generated_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

def setup_client_ai_endpoints(app):
    """Add Client AI endpoints to the FastAPI app"""
    
    def get_or_generate_analysis(
        client_id: str, 
        analysis_type: str, 
        db: Session, 
        current_user: User,
        force_regenerate: bool = False
    ):
        """Get existing analysis or return None if not found"""
        try:
            if not force_regenerate:
                # Check for existing analysis
                existing = db.query(ClientAIAnalysis).filter(
                    ClientAIAnalysis.client_id == client_id,
                    ClientAIAnalysis.analysis_type == analysis_type
                ).order_by(ClientAIAnalysis.created_at.desc()).first()
                
                if existing:
                    logger.info(f"Found existing {analysis_type} analysis for client {client_id}")
                    return ClientAIResponse(
                        success=True,
                        data=existing.result_data,
                        generated_at=existing.created_at,
                        generated_by=existing.created_by
                    )
            
            return None
        except Exception as e:
            logger.error(f"Error getting analysis: {e}")
            raise
    
    def save_analysis(
        client_id: str,
        analysis_type: str,
        result_data: dict,
        db: Session,
        current_user: User
    ):
        """Save AI analysis results to database"""
        # Delete old analysis of same type
        db.query(ClientAIAnalysis).filter(
            ClientAIAnalysis.client_id == client_id,
            ClientAIAnalysis.analysis_type == analysis_type
        ).delete()
        
        # Save new analysis
        analysis = ClientAIAnalysis(
            client_id=client_id,
            analysis_type=analysis_type,
            result_data=result_data,
            created_by=current_user.id
        )
        db.add(analysis)
        db.commit()
    
    @app.post("/clients/{client_id}/ai/search")
    async def search_client_data(
        client_id: str,
        request: ClientSearchRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Natural language search across client data - always live"""
        try:
            # Search is always live, no caching
            results = client_ai_handler.search_client_data(client_id, request.query, db)
            return ClientAIResponse(success=True, data=results)
        except Exception as e:
            return ClientAIResponse(success=False, data=None, message=str(e))
    
    @app.get("/clients/{client_id}/ai/commitments")
    async def get_client_commitments(
        client_id: str,
        force_regenerate: bool = False,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get commitments - returns cached or prompts for generation"""
        try:
            # Check for existing analysis
            existing = get_or_generate_analysis(client_id, 'commitments', db, current_user, force_regenerate)
            if existing:
                return existing
            
            # No existing analysis found
            return ClientAIResponse(
                success=True,
                data=None,
                message="No analysis found. Click 'Generate' to create one."
            )
        except Exception as e:
            logger.error(f"Error in get_client_commitments: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/clients/{client_id}/ai/commitments/generate")
    async def generate_client_commitments(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Generate new commitments analysis"""
        try:
            commitments = client_ai_handler.extract_commitments(client_id, db)
            # Wrap the commitments list in a dict for consistency
            save_analysis(client_id, 'commitments', {"commitments": commitments}, db, current_user)
            return ClientAIResponse(
                success=True, 
                data=commitments,
                generated_at=datetime.utcnow(),
                generated_by=current_user.id
            )
        except Exception as e:
            return ClientAIResponse(success=False, data=None, message=str(e))
    
    @app.get("/clients/{client_id}/ai/weekly-summary")
    async def get_weekly_summary(
        client_id: str,
        force_regenerate: bool = False,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get weekly summary - returns cached or prompts for generation"""
        try:
            existing = get_or_generate_analysis(client_id, 'weekly_summary', db, current_user, force_regenerate)
            if existing:
                return existing
            
            return ClientAIResponse(
                success=True,
                data=None,
                message="No summary found. Click 'Generate' to create one."
            )
        except Exception as e:
            logger.error(f"Error in get_weekly_summary: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/clients/{client_id}/ai/weekly-summary/generate")
    async def generate_weekly_summary(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Generate new weekly summary"""
        try:
            summary = client_ai_handler.generate_weekly_summary(client_id, db)
            save_analysis(client_id, 'weekly_summary', summary, db, current_user)
            return ClientAIResponse(
                success=True,
                data=summary,
                generated_at=datetime.utcnow(),
                generated_by=current_user.id
            )
        except Exception as e:
            return ClientAIResponse(success=False, data=None, message=str(e))
    
    @app.get("/clients/{client_id}/ai/sentiment")
    async def analyze_client_sentiment(
        client_id: str,
        force_regenerate: bool = False,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get sentiment analysis - returns cached or prompts for generation"""
        try:
            existing = get_or_generate_analysis(client_id, 'sentiment', db, current_user, force_regenerate)
            if existing:
                return existing
            
            return ClientAIResponse(
                success=True,
                data=None,
                message="No analysis found. Click 'Generate' to create one."
            )
        except Exception as e:
            logger.error(f"Error in analyze_client_sentiment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/clients/{client_id}/ai/sentiment/generate")
    async def generate_sentiment_analysis(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Generate new sentiment analysis"""
        try:
            sentiment = client_ai_handler.analyze_sentiment(client_id, db)
            save_analysis(client_id, 'sentiment', sentiment, db, current_user)
            return ClientAIResponse(
                success=True,
                data=sentiment,
                generated_at=datetime.utcnow(),
                generated_by=current_user.id
            )
        except Exception as e:
            return ClientAIResponse(success=False, data=None, message=str(e))
    
    @app.get("/clients/{client_id}/ai/suggested-tasks")
    async def get_suggested_tasks(
        client_id: str,
        force_regenerate: bool = False,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get suggested tasks - returns cached or prompts for generation"""
        try:
            existing = get_or_generate_analysis(client_id, 'suggested_tasks', db, current_user, force_regenerate)
            if existing:
                return existing
            
            return ClientAIResponse(
                success=True,
                data=None,
                message="No suggestions found. Click 'Generate' to create some."
            )
        except Exception as e:
            logger.error(f"Error in get_suggested_tasks: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/clients/{client_id}/ai/suggested-tasks/generate")
    async def generate_suggested_tasks(
        client_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Generate new task suggestions"""
        try:
            tasks = client_ai_handler.suggest_tasks_from_communications(client_id, db)
            # Wrap the tasks list in a dict for consistency
            save_analysis(client_id, 'suggested_tasks', {"tasks": tasks}, db, current_user)
            return ClientAIResponse(
                success=True,
                data=tasks,
                generated_at=datetime.utcnow(),
                generated_by=current_user.id
            )
        except Exception as e:
            return ClientAIResponse(success=False, data=None, message=str(e))
    
    @app.post("/clients/{client_id}/ai/create-task")
    async def create_task_from_ai(
        client_id: str,
        task_data: dict,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a task from AI suggestion"""
        try:
            # Import here to avoid circular imports
            from .client_portal_models import ClientTask, TaskStatus, TaskPriority
            
            task = ClientTask(
                client_id=client_id,
                title=task_data.get('title'),
                description=task_data.get('description'),
                priority=TaskPriority(task_data.get('priority', 'medium')),
                due_date=task_data.get('due_date'),
                assigned_by=current_user.id,
                status=TaskStatus.TODO
            )
            db.add(task)
            db.commit()
            
            return ClientAIResponse(success=True, data={"task_id": task.id})
        except Exception as e:
            return ClientAIResponse(success=False, message=str(e)) 