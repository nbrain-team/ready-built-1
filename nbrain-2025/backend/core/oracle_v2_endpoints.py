"""
Oracle V2 API Endpoints - Complete feature set
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from .database import User, get_db
from .auth import get_current_active_user
from .oracle_v2 import oracle_v2

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/oracle", tags=["oracle"])

# Request/Response models
class ConnectResponse(BaseModel):
    authUrl: str

class ActionItemResponse(BaseModel):
    id: str
    title: str
    source: str
    sourceType: str
    priority: str
    status: str
    createdAt: str
    dueDate: Optional[str] = None
    category: str
    context: str
    metaData: Dict[str, Any]

class StatusUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    source_filter: Optional[str] = None

class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = ""
    start: str  # ISO datetime
    end: str    # ISO datetime
    timezone: str = "UTC"
    location: Optional[str] = None
    attendees: List[str] = []

@router.get("/sources")
async def get_sources(current_user: User = Depends(get_current_active_user)):
    """Get data source status"""
    # Check if user has connected accounts
    has_credentials = oracle_v2.storage.get_user_credentials(current_user.id) is not None
    
    return [
        {
            "id": "email",
            "name": "Gmail",
            "type": "email",
            "status": "connected" if has_credentials else "disconnected",
            "lastSync": None,
            "features": ["action_extraction", "search", "ai_analysis"]
        },
        {
            "id": "calendar",
            "name": "Google Calendar",
            "type": "calendar",
            "status": "connected" if has_credentials else "disconnected",
            "lastSync": None,
            "features": ["event_sync", "meeting_prep", "scheduling"]
        }
    ]

@router.post("/connect/email", response_model=ConnectResponse)
async def connect_email(current_user: User = Depends(get_current_active_user)):
    """Get OAuth URL for email connection"""
    try:
        auth_url = oracle_v2.get_auth_url(current_user.id)
        return ConnectResponse(authUrl=auth_url)
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/email")
async def sync_email(current_user: User = Depends(get_current_active_user)):
    """Sync emails from Gmail with nBrain Priority label"""
    try:
        # Call the async method with await
        result = await oracle_v2.sync_recent_emails(current_user.id)
        
        # Check the result status
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Sync failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/email-no-label")
async def sync_email_no_label(current_user: User = Depends(get_current_active_user)):
    """Sync emails with nBrain label (both read and unread)"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta
        import uuid
        
        credentials = oracle_v2.storage.get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Email not connected")
        
        creds = Credentials(**credentials)
        service = build('gmail', 'v1', credentials=creds)
        
        # Get emails from last 7 days with label - try multiple formats
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")
        queries = [
            f'after:{seven_days_ago} label:"nBrain Priority"',
            f'after:{seven_days_ago} in:"nBrain Priority"'
        ]
        
        messages = []
        successful_query = None
        
        for query in queries:
            logger.info(f"Trying query: {query}")
            try:
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=50
                ).execute()
                
                messages = results.get('messages', [])
                if len(messages) > 0:
                    successful_query = query
                    logger.info(f"Found {len(messages)} emails with query: {query}")
                    break
            except Exception as e:
                logger.warning(f"Query failed: {query} - {e}")
                continue
        
        if len(messages) == 0:
            # Fallback to recent emails without label
            logger.info("No labeled emails found, getting recent emails")
            query = f'after:{seven_days_ago}'
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=20
            ).execute()
            messages = results.get('messages', [])
            successful_query = "recent emails (no label)"
        
        synced_count = 0
        
        for message in messages[:20]:  # Process up to 20 emails
            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Parse and store email
                email_data = oracle_v2._parse_email(msg)
                oracle_v2._store_email_for_display(current_user.id, email_data)
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error processing message {message['id']}: {e}")
                continue
        
        return {
            "message": f"Synced {synced_count} emails",
            "emails_found": len(messages),
            "emails_processed": synced_count,
            "query_used": successful_query,
            "note": "Emails are now stored and will persist across logins"
        }
        
    except Exception as e:
        logger.error(f"Error syncing emails without label: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/calendar")
async def sync_calendar(current_user: User = Depends(get_current_active_user)):
    """Sync calendar events and extract action items"""
    try:
        result = oracle_v2.sync_calendar(current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync calendar")

@router.post("/search")
async def search_content(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Search across emails and action items using vector search"""
    try:
        results = oracle_v2.search_content(
            current_user.id, 
            request.query,
            request.source_filter
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/action-items", response_model=List[ActionItemResponse])
async def get_action_items(
    status: Optional[str] = Query(None, description="Filter by status: pending, completed"),
    priority: Optional[str] = Query(None, description="Filter by priority: high, medium, low"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all action items with optional filters"""
    items = oracle_v2.get_action_items(current_user.id, status, priority)
    return [ActionItemResponse(**item.to_dict()) for item in items]

@router.put("/action-items/{item_id}")
async def update_action_item(
    item_id: str,
    update: StatusUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update action item status or priority"""
    success = oracle_v2.update_action_item(
        current_user.id, 
        item_id, 
        update.status,
        update.priority
    )
    if not success:
        raise HTTPException(status_code=404, detail="Action item not found")
    return {"message": "Updated successfully"}

@router.delete("/action-items/{item_id}")
async def delete_action_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete an action item"""
    success = oracle_v2.delete_action_item(current_user.id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Action item not found")
    return {"message": "Deleted successfully"}

@router.post("/action-items/{item_id}/mark-complete")
async def mark_action_item_complete(
    item_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Mark an action item as complete"""
    success = oracle_v2.update_action_item(current_user.id, item_id, status="completed")
    if not success:
        raise HTTPException(status_code=404, detail="Action item not found")
    return {"message": "Marked as complete"}

@router.post("/action-items/{item_id}/get-suggested-response")
async def get_suggested_response_for_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get AI-suggested response for an action item"""
    try:
        # Get the action item
        items = oracle_v2.get_action_items(current_user.id)
        item = next((i for i in items if i.id == item_id), None)
        
        if not item:
            raise HTTPException(status_code=404, detail="Action item not found")
        
        # Generate suggested response
        suggestion = oracle_v2.suggest_response(current_user.id, item_id)
        
        return {"suggested_response": suggestion}
    except Exception as e:
        logger.error(f"Error generating suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestion")

@router.post("/send-email-reply")
async def send_email_reply(
    request: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Send an email reply via Gmail"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import base64
        
        thread_id = request.get('thread_id')
        to_email = request.get('from_email')  # Reply to the sender
        reply_content = request.get('reply_content')
        
        if not all([thread_id, to_email, reply_content]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Get user credentials
        credentials = oracle_v2.storage.get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Gmail not connected")
        
        creds = Credentials(**credentials)
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user's email address
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        
        # Create reply message
        message = MIMEMultipart()
        message['to'] = to_email
        message['from'] = user_email
        message['subject'] = 'Re: ' + request.get('subject', 'Your message')
        
        # Add reply content
        message.attach(MIMEText(reply_content, 'plain'))
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send the reply
        reply = service.users().messages().send(
            userId='me',
            body={
                'raw': raw_message,
                'threadId': thread_id
            }
        ).execute()
        
        return {"message": "Reply sent successfully", "messageId": reply['id']}
        
    except Exception as e:
        logger.error(f"Error sending email reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/action-items/{item_id}/suggest-response")
async def suggest_response(
    item_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get AI-suggested response for an action item"""
    try:
        suggestion = oracle_v2.suggest_response(current_user.id, item_id)
        return {"suggestion": suggestion}
    except Exception as e:
        logger.error(f"Error generating suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestion")

@router.get("/insights")
async def get_insights(current_user: User = Depends(get_current_active_user)):
    """Get insights about workload and patterns"""
    try:
        insights = oracle_v2.get_insights(current_user.id)
        return insights
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.post("/calendar/create-event")
async def create_calendar_event(
    event_data: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a calendar event"""
    try:
        credentials = oracle_v2.storage.get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Calendar not connected")
        
        created_event = oracle_v2.calendar.create_event(
            current_user.id,
            credentials,
            event_data.dict()
        )
        
        return {
            "message": "Event created successfully",
            "event": {
                "id": created_event.get('id'),
                "htmlLink": created_event.get('htmlLink'),
                "summary": created_event.get('summary')
            }
        }
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")

@router.get("/calendar/busy-times")
async def get_busy_times(
    days_ahead: int = Query(7, description="Number of days to check"),
    current_user: User = Depends(get_current_active_user)
):
    """Get busy time slots from calendar"""
    try:
        credentials = oracle_v2.storage.get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Calendar not connected")
        
        busy_times = oracle_v2.calendar.get_busy_times(
            current_user.id,
            credentials,
            days_ahead
        )
        
        return {"busy_times": busy_times}
    except Exception as e:
        logger.error(f"Error getting busy times: {e}")
        raise HTTPException(status_code=500, detail="Failed to get busy times")

# Placeholder endpoints for frontend compatibility
@router.get("/tasks")
async def get_tasks(current_user: User = Depends(get_current_active_user)):
    """Get tasks (returns action items marked as tasks)"""
    items = oracle_v2.get_action_items(current_user.id)
    tasks = [item for item in items if item.category == 'task']
    return [item.to_dict() for item in tasks]

@router.get("/emails")
async def get_emails(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get emails from database grouped by thread"""
    try:
        from sqlalchemy import text
        import json
        
        # First try with is_deleted column
        try:
            query = text("""
                WITH ranked_emails AS (
                    SELECT 
                        id, message_id, thread_id, subject, from_email, 
                        to_emails, content, date, is_sent, is_received, created_at,
                        ROW_NUMBER() OVER (PARTITION BY thread_id ORDER BY date DESC) as rn,
                        COUNT(*) OVER (PARTITION BY thread_id) as thread_count
                    FROM oracle_emails 
                    WHERE user_id = :user_id 
                    AND (is_deleted IS FALSE OR is_deleted IS NULL)
                )
                SELECT 
                    id, message_id, thread_id, subject, from_email,
                    to_emails, content, date, is_sent, is_received, 
                    created_at, thread_count
                FROM ranked_emails
                WHERE rn = 1
                ORDER BY date DESC NULLS LAST
                LIMIT 100
            """)
            result = db.execute(query, {"user_id": current_user.id})
        except Exception as e:
            if "is_deleted" in str(e):
                # Rollback the failed transaction
                db.rollback()
                
                # Fallback query without is_deleted column
                logger.warning("is_deleted column not found, using fallback query")
                query = text("""
                    WITH ranked_emails AS (
                        SELECT 
                            id, message_id, thread_id, subject, from_email, 
                            to_emails, content, date, is_sent, is_received, created_at,
                            ROW_NUMBER() OVER (PARTITION BY thread_id ORDER BY date DESC) as rn,
                            COUNT(*) OVER (PARTITION BY thread_id) as thread_count
                        FROM oracle_emails 
                        WHERE user_id = :user_id
                    )
                    SELECT 
                        id, message_id, thread_id, subject, from_email,
                        to_emails, content, date, is_sent, is_received, 
                        created_at, thread_count
                    FROM ranked_emails
                    WHERE rn = 1
                    ORDER BY date DESC NULLS LAST
                    LIMIT 100
                """)
                result = db.execute(query, {"user_id": current_user.id})
            else:
                raise
        
        emails = []
        
        for row in result:
            email_data = {
                "id": row.thread_id,  # Use thread_id as the main ID for grouping
                "message_id": row.message_id,
                "thread_id": row.thread_id,
                "subject": row.subject,
                "from": row.from_email,
                "to": json.loads(row.to_emails) if row.to_emails else [],
                "date": row.date.isoformat() if row.date else None,
                "snippet": row.content[:200] + "..." if len(row.content) > 200 else row.content,
                "content": row.content,
                "thread_count": row.thread_count
            }
            
            # Add thread count to subject if multiple emails
            if row.thread_count > 1:
                email_data["subject"] = f"{row.subject} ({row.thread_count})"
            
            emails.append(email_data)
        
        logger.info(f"Returning {len(emails)} email threads for user {current_user.id}")
        return emails
        
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        if "oracle_emails" in str(e):
            # Table doesn't exist
            return []
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/emails/{thread_id}")
async def delete_email_thread(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Soft delete an email thread"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # Soft delete all emails in the thread
        query = text("""
            UPDATE oracle_emails 
            SET is_deleted = TRUE, deleted_at = :deleted_at
            WHERE user_id = :user_id AND thread_id = :thread_id
        """)
        
        result = db.execute(query, {
            "user_id": current_user.id,
            "thread_id": thread_id,
            "deleted_at": datetime.utcnow()
        })
        
        db.commit()
        
        if result.rowcount > 0:
            logger.info(f"Soft deleted {result.rowcount} emails in thread {thread_id}")
            return {"message": f"Deleted thread {thread_id}", "emails_deleted": result.rowcount}
        else:
            raise HTTPException(status_code=404, detail="Thread not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email thread: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails/{thread_id}/full")
async def get_full_email(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get full email content by thread ID"""
    try:
        from sqlalchemy import text
        import json
        
        # For now, just get the email by thread_id from the database
        query = text("""
            SELECT id, message_id, thread_id, subject, from_email, 
                   to_emails, content, date
            FROM oracle_emails 
            WHERE user_id = :user_id AND (thread_id = :thread_id OR message_id = :thread_id)
            LIMIT 1
        """)
        
        result = db.execute(query, {"user_id": current_user.id, "thread_id": thread_id})
        row = result.first()
        
        if row:
            return {
                "id": row.message_id,
                "thread_id": row.thread_id,
                "subject": row.subject,
                "from": row.from_email,
                "to": json.loads(row.to_emails) if row.to_emails else [],
                "date": row.date.isoformat() if row.date else None,
                "content": row.content,
                "snippet": row.content[:200] + "..." if len(row.content) > 200 else row.content
            }
        else:
            raise HTTPException(status_code=404, detail="Email not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggested-tasks")
async def get_suggested_tasks(current_user: User = Depends(get_current_active_user)):
    """Get suggested tasks (high priority pending items)"""
    items = oracle_v2.get_action_items(current_user.id, "pending", "high")
    return [{"id": item.id, "title": item.title, "source": item.source} for item in items[:5]]

@router.get("/sentiment")
async def get_sentiment(current_user: User = Depends(get_current_active_user)):
    """Get workload sentiment based on action items"""
    insights = oracle_v2.get_insights(current_user.id)
    
    # Calculate sentiment based on workload
    pending = insights['summary']['pending']
    overdue_count = len(insights['overdue'])
    
    if overdue_count > 5 or pending > 20:
        sentiment = "stressed"
        score = 0.3
    elif overdue_count > 2 or pending > 10:
        sentiment = "busy"
        score = 0.6
    else:
        sentiment = "balanced"
        score = 0.8
    
    return {
        "overall": sentiment,
        "score": score,
        "trends": [],
        "insights": insights['recommendations']
    }

@router.post("/generate-action-items")
async def generate_action_items(current_user: User = Depends(get_current_active_user)):
    """Generate action items from existing emails in database"""
    db = None
    try:
        from sqlalchemy import text
        
        # Get emails from database
        db = next(get_db())
        
        # Fetch existing emails from database
        try:
            # Try with is_deleted column first
            result = db.execute(
                text("""
                    SELECT id, subject, content, from_email, date
                    FROM oracle_emails
                    WHERE user_id = :user_id
                    AND is_deleted = false
                    ORDER BY date DESC
                    LIMIT 50
                """),
                {"user_id": current_user.id}
            )
            emails = result.fetchall()
        except Exception as e:
            # Rollback the failed transaction
            db.rollback()
            
            # Fallback without is_deleted column
            logger.warning("is_deleted column not found, using fallback query")
            result = db.execute(
                text("""
                    SELECT id, subject, content, from_email, date
                    FROM oracle_emails
                    WHERE user_id = :user_id
                    ORDER BY date DESC
                    LIMIT 50
                """),
                {"user_id": current_user.id}
            )
            emails = result.fetchall()
        
        if not emails:
            return {
                "message": "No emails found. Please sync your emails first.",
                "action_items_count": 0,
                "items": []
            }
        
        # Extract action items from existing emails
        new_items = []
        for email in emails:
            try:
                # Use AI to extract action items
                items = await oracle_v2.ai.extract_action_items_from_email(
                    email.subject or "",
                    email.content or "",
                    email.from_email or ""
                )
                
                # Store action items
                for item in items:
                    stored_item = oracle_v2.storage.store_action_item(current_user.id, item)
                    if stored_item:
                        new_items.append(stored_item)
                        
            except Exception as e:
                logger.error(f"Error extracting from email {email.id}: {e}")
                continue
        
        return {
            "message": f"Generated {len(new_items)} new action items from existing emails",
            "action_items_count": len(new_items),
            "items": [item if isinstance(item, dict) else item.to_dict() for item in new_items[:10]]
        }
        
    except Exception as e:
        logger.error(f"Error generating action items: {e}")
        if db:
            db.rollback()
        return {
            "message": "Error generating action items. Please try again.",
            "action_items_count": 0,
            "items": []
        }
    finally:
        if db:
            db.close()

@router.post("/generate-sentiment")
async def generate_sentiment_analysis(current_user: User = Depends(get_current_active_user)):
    """Trigger sentiment analysis generation"""
    # For now, just return success
    return {"message": "Sentiment analysis updated"}

@router.post("/generate-suggested-tasks") 
async def generate_suggested_tasks_endpoint(current_user: User = Depends(get_current_active_user)):
    """Trigger suggested tasks generation"""
    # For now, just return success
    return {"message": "Suggested tasks updated"}

@router.get("/debug/gmail-labels")
async def get_gmail_labels(current_user: User = Depends(get_current_active_user)):
    """Debug endpoint to list all Gmail labels"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        credentials = oracle_v2.storage.get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Gmail not connected")
        
        creds = Credentials(**credentials)
        service = build('gmail', 'v1', credentials=creds)
        
        # Get all labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        # Format label information
        label_info = []
        for label in labels:
            label_info.append({
                "id": label['id'],
                "name": label['name'],
                "type": label.get('type', 'user')
            })
        
        # Sort by name
        label_info.sort(key=lambda x: x['name'])
        
        return {
            "total_labels": len(labels),
            "labels": label_info,
            "looking_for": ["nBrain+Priority", "nBrain Priority"],
            "found_plus": any(label['name'] == 'nBrain+Priority' for label in label_info),
            "found_space": any(label['name'] == 'nBrain Priority' for label in label_info),
            "found_any": any(label['name'] in ['nBrain+Priority', 'nBrain Priority'] for label in label_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting Gmail labels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug/sync-with-label")
async def debug_sync_with_label(
    label_name: str = Query(..., description="Label name to sync"),
    current_user: User = Depends(get_current_active_user)
):
    """Debug endpoint to manually sync emails with a specific label"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta
        
        credentials = oracle_v2.storage.get_user_credentials(current_user.id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Email not connected")
        
        creds = Credentials(**credentials)
        service = build('gmail', 'v1', credentials=creds)
        
        # Try the exact label provided
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")
        query = f'after:{seven_days_ago} label:{label_name}'
        
        logger.info(f"Debug sync with query: {query}")
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        
        # Process and store emails
        synced_count = 0
        email_subjects = []
        
        for message in messages[:10]:
            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Parse email
                email_data = oracle_v2._parse_email(msg)
                email_subjects.append(email_data.get('subject', 'No Subject'))
                
                # Store in database
                oracle_v2._store_email_for_display(current_user.id, email_data)
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
        
        return {
            "query_used": query,
            "total_found": len(messages),
            "emails_synced": synced_count,
            "sample_subjects": email_subjects[:5],
            "message": f"Found {len(messages)} emails with label '{label_name}'"
        }
        
    except Exception as e:
        logger.error(f"Debug sync error: {e}")
        return {
            "error": str(e),
            "query_attempted": f'after:{seven_days_ago} label:{label_name}',
            "suggestion": "Try different label formats or check if label exists in Gmail"
        }

# OAuth callback handler
async def oauth_callback(code: str, state: str):
    """Handle OAuth callback and sync emails"""
    try:
        result = oracle_v2.handle_oauth_callback(code, state)
        user_id = result.get('user_id')
        
        # Trigger email sync after successful connection
        if user_id:
            try:
                logger.info(f"Triggering email sync for user {user_id} after OAuth connection")
                # Use await for the async method
                sync_result = await oracle_v2.sync_recent_emails(user_id)
                logger.info(f"Successfully synced {sync_result.get('emails_synced', 0)} emails after OAuth")
            except Exception as sync_error:
                logger.error(f"Error syncing emails after OAuth: {sync_error}")
                # Don't fail the OAuth callback, just log the error
        
        return {
            "status": "success",
            "message": "Email and Calendar connected successfully. Emails are being synced.",
            "result": result
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) 