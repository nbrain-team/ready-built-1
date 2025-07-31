"""
Read.ai Webhook Endpoints
Handles incoming webhooks from Read.ai
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import json
import secrets
import os

from .database import get_db, User
from .auth import get_current_active_user
from .readai_handler import readai_handler
from .readai_models import ReadAIIntegration, ReadAIMeeting

logger = logging.getLogger(__name__)

def setup_readai_endpoints(app):
    """Add Read.ai endpoints to the FastAPI app"""
    
    @app.post("/webhooks/readai")
    async def receive_readai_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        x_readai_signature: Optional[str] = Header(None),
        db: Session = Depends(get_db)
    ):
        """
        Receive webhook from Read.ai
        This is the callback URL you'll provide to Read.ai
        """
        try:
            # Get request body
            body = await request.body()
            webhook_data = await request.json()
            
            logger.info(f"Received Read.ai webhook: {webhook_data.get('event_type', 'unknown')}")
            
            # Get user_id from webhook data or headers
            # Read.ai should include some identifier to map to your users
            user_identifier = webhook_data.get('user_email') or webhook_data.get('user_id')
            
            if not user_identifier:
                logger.warning("No user identifier in webhook")
                return JSONResponse({"status": "no_user_identifier"}, status_code=200)
            
            # Find user by email or external ID
            user = None
            if '@' in str(user_identifier):
                user = db.query(User).filter(User.email == user_identifier).first()
            
            if not user:
                logger.warning(f"User not found for identifier: {user_identifier}")
                return JSONResponse({"status": "user_not_found"}, status_code=200)
            
            # Get integration for verification
            integration = db.query(ReadAIIntegration).filter(
                ReadAIIntegration.user_id == user.id
            ).first()
            
            # Verify webhook signature if secret is configured
            if integration and integration.webhook_secret and x_readai_signature:
                if not readai_handler.verify_webhook_signature(
                    body, x_readai_signature, integration.webhook_secret
                ):
                    logger.warning("Invalid webhook signature")
                    raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Process webhook in background
            background_tasks.add_task(
                readai_handler.process_webhook,
                webhook_data,
                user.id,
                db
            )
            
            return JSONResponse({"status": "accepted"}, status_code=200)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook body")
            return JSONResponse({"status": "invalid_json"}, status_code=400)
        except Exception as e:
            logger.error(f"Error processing Read.ai webhook: {e}", exc_info=True)
            return JSONResponse({"status": "error"}, status_code=500)
    
    @app.get("/readai/integration-status")
    async def get_readai_integration_status(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get Read.ai integration status for current user"""
        integration = db.query(ReadAIIntegration).filter(
            ReadAIIntegration.user_id == current_user.id
        ).first()
        
        if not integration:
            return {
                "integrated": False,
                "webhook_url": f"{os.getenv('APP_BASE_URL', 'https://your-app.onrender.com')}/webhooks/readai"
            }
        
        return {
            "integrated": True,
            "status": integration.integration_status,
            "last_webhook": integration.last_webhook_at.isoformat() if integration.last_webhook_at else None,
            "webhook_url": f"{os.getenv('APP_BASE_URL', 'https://your-app.onrender.com')}/webhooks/readai",
            "webhook_secret": integration.webhook_secret[:8] + "..." if integration.webhook_secret else None
        }
    
    @app.post("/readai/generate-webhook-secret")
    async def generate_webhook_secret(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Generate a new webhook secret for Read.ai integration"""
        # Get or create integration
        integration = db.query(ReadAIIntegration).filter(
            ReadAIIntegration.user_id == current_user.id
        ).first()
        
        if not integration:
            integration = ReadAIIntegration(
                user_id=current_user.id,
                integration_status='active'
            )
            db.add(integration)
        
        # Generate new secret
        new_secret = secrets.token_urlsafe(32)
        integration.webhook_secret = new_secret
        
        db.commit()
        
        return {
            "webhook_secret": new_secret,
            "webhook_url": f"{os.getenv('APP_BASE_URL', 'https://your-app.onrender.com')}/webhooks/readai",
            "instructions": "Add this webhook URL and secret to your Read.ai integration settings"
        }
    
    @app.get("/readai/meetings")
    async def get_readai_meetings(
        limit: int = 20,
        client_id: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get Read.ai meetings for current user"""
        query = db.query(ReadAIMeeting).join(ReadAIIntegration).filter(
            ReadAIIntegration.user_id == current_user.id
        )
        
        if client_id:
            query = query.filter(ReadAIMeeting.client_id == client_id)
        
        meetings = query.order_by(ReadAIMeeting.start_time.desc()).limit(limit).all()
        
        return [{
            "id": meeting.id,
            "title": meeting.meeting_title,
            "platform": meeting.meeting_platform,
            "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
            "duration_minutes": meeting.duration_minutes,
            "participants": meeting.participants,
            "summary": meeting.summary,
            "action_items": meeting.action_items,
            "client_id": meeting.client_id,
            "synced_to_oracle": meeting.synced_to_oracle
        } for meeting in meetings]
    
    @app.get("/readai/meetings/{meeting_id}")
    async def get_readai_meeting_detail(
        meeting_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get detailed Read.ai meeting information"""
        meeting = db.query(ReadAIMeeting).join(ReadAIIntegration).filter(
            ReadAIMeeting.id == meeting_id,
            ReadAIIntegration.user_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return {
            "id": meeting.id,
            "readai_meeting_id": meeting.readai_meeting_id,
            "title": meeting.meeting_title,
            "url": meeting.meeting_url,
            "platform": meeting.meeting_platform,
            "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
            "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
            "duration_minutes": meeting.duration_minutes,
            "participants": meeting.participants,
            "host_email": meeting.host_email,
            "transcript": meeting.transcript,
            "summary": meeting.summary,
            "key_points": meeting.key_points,
            "action_items": meeting.action_items,
            "sentiment_score": meeting.sentiment_score,
            "engagement_score": meeting.engagement_score,
            "client_id": meeting.client_id,
            "synced_to_oracle": meeting.synced_to_oracle,
            "oracle_action_items_created": meeting.oracle_action_items_created
        }
    
    @app.post("/readai/search")
    async def search_readai_meetings(
        request: Dict[str, Any],
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Search through Read.ai meeting transcripts"""
        query = request.get("query", "")
        client_id = request.get("client_id")
        
        results = readai_handler.search_meetings(
            query=query,
            user_id=current_user.id,
            client_id=client_id,
            db=db
        )
        
        return {"results": results}
    
    @app.delete("/readai/integration")
    async def disconnect_readai_integration(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Disconnect Read.ai integration"""
        integration = db.query(ReadAIIntegration).filter(
            ReadAIIntegration.user_id == current_user.id
        ).first()
        
        if integration:
            integration.integration_status = 'disconnected'
            integration.webhook_secret = None
            db.commit()
            
        return {"status": "disconnected"} 