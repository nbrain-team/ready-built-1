"""
Oracle API Endpoints
"""

from fastapi import HTTPException, Depends, BackgroundTasks, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from .database import get_db, User
from .auth import get_current_active_user
from .oracle_handler import (
    get_oracle_handler, 
    OracleDataSource, 
    OracleActionItem, 
    OracleInsight
)
# ClientTask import removed - not needed after disabling task conversion endpoints

# Create router
router = APIRouter(prefix="/api/oracle", tags=["oracle"])

# Pydantic models
class OracleSearchRequest(BaseModel):
    query: str
    sources: List[str] = []

class OracleConnectResponse(BaseModel):
    authUrl: str

class OracleActionItemUpdate(BaseModel):
    status: str

class DataSourceResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    lastSync: Optional[str] = None
    count: Optional[int] = None
    errorMessage: Optional[str] = None

class ActionItemResponse(BaseModel):
    id: str
    title: str
    source: str
    sourceType: str
    dueDate: Optional[str] = None
    priority: str
    status: str
    createdAt: str
    metaData: Optional[Dict[str, Any]] = None

class InsightResponse(BaseModel):
    id: str
    content: str
    source: str
    timestamp: str
    category: str

@router.get("/sources", response_model=List[DataSourceResponse])
async def get_data_sources(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all data sources for the current user"""
    sources = db.query(OracleDataSource).filter(
        OracleDataSource.user_id == current_user.id
    ).all()
    
    # Map to response format
    response = []
    source_map = {
        'email': 'Gmail',
        'calendar': 'Google Calendar',
        'drive': 'Google Drive',
        'voice': 'Voice Notes',
        'meeting': 'Meeting Transcripts'
    }
    
    # Add connected sources from database
    for source in sources:
        response.append(DataSourceResponse(
            id=source.id,
            name=source_map.get(source.source_type, source.source_type),
            type=source.source_type,
            status=source.status,
            lastSync=source.last_sync.isoformat() if source.last_sync else None,
            count=source.item_count,
            errorMessage=source.error_message if hasattr(source, 'error_message') else None
        ))
    
    # Add disconnected sources (only for Google OAuth sources, not voice/meeting)
    connected_types = {s.source_type for s in sources}
    google_oauth_types = ['email', 'calendar', 'drive']  # Only these can be connected via OAuth
    
    for source_type in google_oauth_types:
        if source_type not in connected_types:
            response.append(DataSourceResponse(
                id=f"disconnected-{source_type}",  # Use a proper ID format
                name=source_map[source_type],
                type=source_type,
                status='disconnected',
                lastSync=None,
                count=None
            ))
    
    return response

@router.post("/connect/{source_type}", response_model=OracleConnectResponse)
async def connect_data_source(
    source_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get OAuth URL for connecting a data source"""
    if source_type not in ['email', 'calendar', 'drive']:
        raise HTTPException(status_code=400, detail="Invalid source type")
    
    auth_url = get_oracle_handler().get_auth_url(source_type, current_user.id)
    return OracleConnectResponse(authUrl=auth_url)

@router.post("/sync/{source_type}")
async def sync_data_source(
    source_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync data from a connected source"""
    # Update status to syncing
    data_source = db.query(OracleDataSource).filter(
        OracleDataSource.user_id == current_user.id,
        OracleDataSource.source_type == source_type
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    data_source.status = 'syncing'
    db.commit()
    
    # Add background task for syncing
    if source_type == 'email':
        background_tasks.add_task(
            sync_emails_background,
            current_user.id,
            source_type
        )
    
    return {"message": f"Syncing {source_type} in background"}

@router.get("/action-items", response_model=List[ActionItemResponse])
async def get_action_items(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all action items for the current user"""
    try:
        # Ensure clean transaction state
        db.rollback()
        
        items = db.query(OracleActionItem).filter(
            OracleActionItem.user_id == current_user.id,
            OracleActionItem.is_deleted == False  # Filter out deleted items
        ).order_by(OracleActionItem.created_at.desc()).all()
        
        return [
            ActionItemResponse(
                id=item.id,
                title=item.title,
                source=item.source,
                sourceType=item.source_type,
                dueDate=item.due_date.isoformat() if item.due_date else None,
                priority=item.priority,
                status=item.status,
                createdAt=item.created_at.isoformat(),
                metaData=item.meta_data
            )
            for item in items
        ]
    except Exception as e:
        logger.error(f"Error fetching action items: {e}")
        db.rollback()  # Ensure we rollback on error
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/action-items/{item_id}")
async def delete_action_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an action item (soft delete for training purposes)"""
    item = db.query(OracleActionItem).filter(
        OracleActionItem.id == item_id,
        OracleActionItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    # Soft delete - mark as deleted but keep in database
    item.is_deleted = True
    item.deleted_at = datetime.utcnow()
    item.status = 'deleted'
    
    db.commit()
    
    # Log deletion for training purposes
    logger.info(f"Action item deleted for training: {item.title} - {item.meta_data}")
    
    return {"message": "Action item deleted"}

@router.post("/action-items/{item_id}/convert-to-task")
async def convert_action_item_to_task(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Convert an action item to a task"""
    
    # TODO: This endpoint needs to be fixed - ClientTask doesn't have user_id field
    # For now, just return an error
    raise HTTPException(
        status_code=501, 
        detail="Task conversion is temporarily disabled. Action items can be managed directly."
    )
    
    # Original code commented out:
    # item = db.query(OracleActionItem).filter(
    #     OracleActionItem.id == item_id,
    #     OracleActionItem.user_id == current_user.id
    # ).first()
    # 
    # if not item:
    #     raise HTTPException(status_code=404, detail="Action item not found")
    # 
    # if item.task_created:
    #     raise HTTPException(status_code=400, detail="Task already created for this action item")
    # 
    # # Create a new task
    # new_task = ClientTask(
    #     user_id=current_user.id,
    #     title=item.title,
    #     description=item.meta_data.get('description', '') or item.meta_data.get('context', ''),
    #     priority=item.priority,
    #     due_date=item.due_date,
    #     status='pending',
    #     source='oracle_action_item',
    #     category='general'
    # )
    # 
    # db.add(new_task)
    # db.flush()  # Get the task ID
    # 
    # # Update action item
    # item.task_created = True
    # item.task_id = new_task.id
    # item.status = 'converted'
    # 
    # db.commit()
    # 
    # return {
    #     "message": "Task created successfully",
    #     "task_id": new_task.id,
    #     "task_title": new_task.title
    # }

@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_oracle_tasks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all tasks created from Oracle action items"""
    
    # TODO: This endpoint needs to be fixed - ClientTask doesn't have user_id field
    # For now, just return empty list
    return []
    
    # Original code commented out:
    # tasks = db.query(ClientTask).filter(
    #     ClientTask.user_id == current_user.id,
    #     ClientTask.source == 'oracle_action_item'
    # ).order_by(ClientTask.created_at.desc()).all()
    # 
    # return [
    #     {
    #         "id": task.id,
    #         "title": task.title,
    #         "description": task.description,
    #         "priority": task.priority,
    #         "status": task.status,
    #         "dueDate": task.due_date.isoformat() if task.due_date else None,
    #         "category": task.category,
    #         "createdAt": task.created_at.isoformat()
    #     }
    #     for task in tasks
    # ]

@router.put("/action-items/{item_id}")
async def update_action_item(
    item_id: str,
    update: OracleActionItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an action item's status"""
    item = db.query(OracleActionItem).filter(
        OracleActionItem.id == item_id,
        OracleActionItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    item.status = update.status
    if update.status == 'completed':
        from datetime import datetime
        item.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Action item updated"}

@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent insights for the current user"""
    # Generate new insights
    get_oracle_handler().generate_insights(current_user.id, db)
    
    # Fetch all insights
    insights = db.query(OracleInsight).filter(
        OracleInsight.user_id == current_user.id
    ).order_by(OracleInsight.created_at.desc()).limit(20).all()
    
    return [
        InsightResponse(
            id=insight.id,
            content=insight.content,
            source=insight.source,
            timestamp=insight.created_at.isoformat(),
            category=insight.category
        )
        for insight in insights
    ]

@router.post("/search")
async def search_oracle(
    request: OracleSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search across all connected data sources"""
    results = get_oracle_handler().search_oracle(
        request.query,
        current_user.id,
        request.sources,
        db
    )
    
    return {"results": results}

# This endpoint needs special handling for OAuth callback
# It will be registered separately in setup_oracle_endpoints
async def oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Google"""
    try:
        result = get_oracle_handler().handle_oauth_callback(code, state, db)
        # Return the status in the expected format
        return {
            "status": "success",
            "message": "Successfully connected",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/debug/oauth-config")
async def debug_oauth_config():
    """Debug endpoint to check OAuth configuration"""
    import os
    return {
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "not set"),
        "client_id_set": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "client_secret_set": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "expected_callback": "https://command.nbrain.ai/oracle/auth/callback",
        "note": "Make sure GOOGLE_REDIRECT_URI in Render matches exactly what's in Google Cloud Console"
    }

@router.delete("/disconnect/{source_type}")
async def disconnect_data_source(
    source_type: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect a data source"""
    data_source = db.query(OracleDataSource).filter(
        OracleDataSource.user_id == current_user.id,
        OracleDataSource.source_type == source_type
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Clear credentials and mark as disconnected
    data_source.credentials = None
    data_source.status = 'disconnected'
    data_source.last_sync = None
    db.commit()
    
    return {"message": f"Successfully disconnected {source_type}"}

@router.get("/emails", response_model=List[Dict[str, Any]])
async def get_oracle_emails(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get emails stored in Oracle"""
    # For now, we'll fetch from oracle_emails table if it exists
    # Otherwise, fetch from Gmail directly
    try:
        query = text("""
            SELECT id, message_id, thread_id, subject, from_email, 
                   to_emails, content, date, is_sent, is_received, created_at
            FROM oracle_emails 
            WHERE user_id = :user_id
            ORDER BY date DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"user_id": current_user.id, "limit": limit})
        emails = []
        for row in result:
            emails.append({
                "id": row.id,
                "message_id": row.message_id,
                "thread_id": row.thread_id,
                "subject": row.subject,
                "from": row.from_email,
                "to": json.loads(row.to_emails) if row.to_emails else [],
                "content": row.content,
                "date": row.date.isoformat() if row.date else None,
                "is_sent": row.is_sent,
                "is_received": row.is_received,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        return emails
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        if "oracle_emails" in str(e):
            raise HTTPException(status_code=503, detail="Email table not initialized. Please connect and sync email first.")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/emails/{thread_id}/full")
async def get_full_email(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get full email content by thread ID"""
    # Get the email from oracle_emails table
    result = db.execute(
        text("""
            SELECT id, message_id, thread_id, subject, from_email, to_emails, 
                   content, date, is_sent, is_received
            FROM oracle_emails 
            WHERE user_id = :user_id AND thread_id = :thread_id
            ORDER BY date DESC
            LIMIT 1
        """),
        {
            "user_id": current_user.id,
            "thread_id": thread_id
        }
    )
    
    email = result.fetchone()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {
        "id": email.id,
        "subject": email.subject,
        "from": email.from_email,
        "to": json.loads(email.to_emails) if email.to_emails else [],
        "date": email.date.isoformat() if email.date else None,
        "content": email.content,  # Full content
        "thread_id": email.thread_id,
        "is_sent": email.is_sent,
        "is_received": email.is_received
    }

@router.post("/generate-action-items")
async def generate_action_items_with_ai(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate action items from recent emails using AI"""
    try:
        # For now, just sync emails which will extract action items
        # The oracle_handler.sync_emails already extracts action items from emails
        logger.info(f"Syncing emails to generate action items for user {current_user.id}")
        
        # Check if email is connected
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == current_user.id,
            OracleDataSource.source_type == 'email'
        ).first()
        
        if not data_source or data_source.status != 'connected':
            return {"message": "Please connect your email first", "action_items": []}
        
        # Sync emails (this will extract action items)
        try:
            action_items_count = get_oracle_handler().sync_emails(current_user.id, db)
            return {
                "message": f"Generated {action_items_count} action items from recent emails",
                "action_items_count": action_items_count
            }
        except Exception as sync_error:
            logger.error(f"Error syncing emails: {sync_error}")
            return {"message": "Error generating action items. Please try syncing emails first.", "action_items": []}
            
    except Exception as e:
        logger.error(f"Error in generate action items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-insights-ai")
async def generate_insights_with_ai(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate insights from emails using AI"""
    try:
        # Get emails from the last 2 weeks
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        # Fetch recent emails
        query = text("""
            SELECT subject, content, from_email, date, is_sent
            FROM oracle_emails 
            WHERE user_id = :user_id AND date >= :two_weeks_ago
            ORDER BY date DESC
            LIMIT 100
        """)
        
        result = db.execute(query, {
            "user_id": current_user.id, 
            "two_weeks_ago": two_weeks_ago
        })
        
        emails = []
        sent_count = 0
        received_count = 0
        
        for row in result:
            emails.append({
                "subject": row.subject,
                "content": row.content[:200] if row.content else '',  # Truncate for analysis
                "from": row.from_email,
                "date": row.date,
                "is_sent": row.is_sent
            })
            if row.is_sent:
                sent_count += 1
            else:
                received_count += 1
        
        if not emails:
            return {"message": "No recent emails found", "insights": []}
        
        # Generate basic insights without AI
        insights = []
        
        # Email volume insight
        insight1 = OracleInsight(
            user_id=current_user.id,
            content=f"You've exchanged {len(emails)} emails in the last 2 weeks ({sent_count} sent, {received_count} received)",
            source="Email Analysis",
            category="email_trend"
        )
        db.add(insight1)
        insights.append(insight1)
        
        # Most active day insight
        from collections import Counter
        day_counts = Counter()
        for email in emails:
            if email['date']:
                day_counts[email['date'].strftime('%A')] += 1
        
        if day_counts:
            most_active_day = day_counts.most_common(1)[0]
            insight2 = OracleInsight(
                user_id=current_user.id,
                content=f"Your most active email day is {most_active_day[0]} with {most_active_day[1]} emails",
                source="Email Analysis",
                category="email_pattern"
            )
            db.add(insight2)
            insights.append(insight2)
        
        # Response rate insight
        if sent_count > 0:
            response_rate = (received_count / sent_count) * 100
            insight3 = OracleInsight(
                user_id=current_user.id,
                content=f"Your email response rate is approximately {response_rate:.0f}%",
                source="Email Analysis",
                category="email_pattern"
            )
            db.add(insight3)
            insights.append(insight3)
        
        db.commit()
        
        return {
            "message": f"Generated {len(insights)} insights",
            "insights": [
                {
                    "content": i.content,
                    "category": i.category,
                    "source": i.source
                }
                for i in insights
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/action-items/deleted")
async def get_deleted_action_items(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get deleted action items for training purposes (admin only)"""
    # You might want to add admin check here
    items = db.query(OracleActionItem).filter(
        OracleActionItem.user_id == current_user.id,
        OracleActionItem.is_deleted == True
    ).order_by(OracleActionItem.deleted_at.desc()).all()
    
    return [
        {
            "id": item.id,
            "title": item.title,
            "source": item.source,
            "meta_data": item.meta_data,
            "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None,
            "reason": "User indicated this was not a valid action item"
        }
        for item in items
    ]

def setup_oracle_endpoints(app):
    """Add Oracle endpoints to the FastAPI app"""
    # Include the router
    app.include_router(router)
    
    # Register the OAuth callback separately without the prefix
    # This is needed because Google OAuth expects the exact callback URL
    @app.get("/oracle/auth/callback")
    async def oauth_callback_handler(
        code: str,
        state: str,
        db: Session = Depends(get_db)
    ):
        return await oauth_callback(code, state, db)

# Background task functions
def sync_emails_background(user_id: str, source_type: str):
    """Background task to sync emails"""
    from .database import SessionLocal
    
    db = SessionLocal()
    try:
        # Sync emails
        action_items_found = get_oracle_handler().sync_emails(user_id, db)
        
        # Update source status
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == user_id,
            OracleDataSource.source_type == source_type
        ).first()
        
        if data_source:
            data_source.status = 'connected'
            data_source.error_message = None  # Clear any previous errors
            db.commit()
            
    except ValueError as e:
        # Handle authentication errors specifically
        logger.error(f"Authentication error syncing emails: {e}")
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == user_id,
            OracleDataSource.source_type == source_type
        ).first()
        
        if data_source:
            if "authentication expired" in str(e).lower():
                data_source.status = 'disconnected'
                data_source.error_message = str(e)
            else:
                data_source.status = 'connected'
                data_source.error_message = f"Sync failed: {str(e)}"
            db.commit()
            
    except Exception as e:
        logger.error(f"Error syncing emails: {e}")
        # Update status to error
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == user_id,
            OracleDataSource.source_type == source_type
        ).first()
        
        if data_source:
            data_source.status = 'connected'  # Still connected, just sync failed
            data_source.error_message = f"Sync error: {str(e)}"
            db.commit()
    finally:
        db.close()

# Export the router and oauth_callback function
__all__ = ['router', 'oauth_callback'] 