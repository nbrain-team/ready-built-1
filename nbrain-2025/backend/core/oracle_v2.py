"""
Oracle V2 - Enhanced personal assistant module with all features
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re

# Import enhanced modules
from .oracle_v2_storage import oracle_storage
from .oracle_v2_ai import oracle_ai
from .oracle_v2_search import oracle_search
from .oracle_v2_calendar import oracle_calendar

logger = logging.getLogger(__name__)

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/oracle/auth/callback")

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.readonly'
]

@dataclass
class ActionItem:
    """Enhanced action item data class"""
    id: str
    title: str
    source: str
    source_type: str = "email"
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime = None
    due_date: Optional[str] = None
    category: str = "other"
    context: str = ""
    metadata: dict = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "sourceType": self.source_type,
            "priority": self.priority,
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
            "dueDate": self.due_date,
            "category": self.category,
            "context": self.context,
            "metaData": self.metadata
        }

class OracleV2:
    """Enhanced Oracle handler with all features"""
    
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        }
        # Use enhanced storage
        self.storage = oracle_storage
        self.ai = oracle_ai
        self.search = oracle_search
        self.calendar = oracle_calendar
    
    def get_auth_url(self, user_id: str) -> str:
        """Generate OAuth URL for email connection"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Include user_id in state
        state = base64.urlsafe_b64encode(
            json.dumps({"user_id": user_id}).encode()
        ).decode()
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        
        return auth_url
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and store credentials"""
        # Decode state
        state_data = json.loads(base64.urlsafe_b64decode(state))
        user_id = state_data['user_id']
        
        # Exchange code for credentials
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)
        
        # Store credentials using enhanced storage
        credentials = {
            'token': flow.credentials.token,
            'refresh_token': flow.credentials.refresh_token,
            'token_uri': flow.credentials.token_uri,
            'client_id': flow.credentials.client_id,
            'client_secret': flow.credentials.client_secret,
            'scopes': flow.credentials.scopes
        }
        
        self.storage.set_user_credentials(user_id, credentials)
        
        return {"status": "success", "user_id": user_id}
    
    async def sync_recent_emails(self, user_id: str) -> Dict[str, Any]:
        """Sync recent emails for a user"""
        logger.info(f"Starting email sync for user {user_id}")
        
        # Get stored credentials
        creds_dict = self.storage.get_user_credentials(user_id)
        if not creds_dict:
            logger.warning(f"No credentials found for user {user_id}")
            return {"status": "error", "message": "No credentials found"}
        
        logger.info(f"Found credentials for user {user_id}")
        
        try:
            # Build Gmail service
            creds = Credentials(**creds_dict)
            service = build('gmail', 'v1', credentials=creds)
            
            # Get emails from the last 7 days with nBrain Priority label
            date_7_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y/%m/%d')
            
            # Use the correct query format with quotes and space
            queries_to_try = [
                f'after:{date_7_days_ago} label:"nBrain Priority"',  # Primary - with quotes and space
                f'after:{date_7_days_ago} label:Label_2688496639481219320',  # Backup - direct label ID
            ]
            
            emails_found = False
            messages = []
            
            for query in queries_to_try:
                logger.info(f"Searching emails with query: {query}")
                try:
                    result = service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=50
                    ).execute()
                    
                    messages = result.get('messages', [])
                    if messages:
                        logger.info(f"Found {len(messages)} emails with query: {query}")
                        emails_found = True
                        break
                    else:
                        logger.info(f"No emails found with query: {query}")
                except Exception as e:
                    logger.warning(f"Query failed: {query}, error: {e}")
                    continue
            
            if not emails_found:
                logger.warning("No emails found with nBrain Priority label. Make sure to label your emails in Gmail.")
                return {
                    "status": "success",
                    "emails_synced": 0,
                    "message": "No emails found with 'nBrain Priority' label. Please label your important emails in Gmail."
                }
            
            total_processed = 0
            for msg_ref in messages:
                try:
                    # Get full message
                    msg = service.users().messages().get(
                        userId='me',
                        id=msg_ref['id']
                    ).execute()
                    
                    # Parse and store email
                    email_data = self._parse_email(msg)
                    if email_data:
                        # Store for display
                        self._store_email_for_display(user_id, email_data)
                        
                        # Extract action items
                        action_items = await self.ai.extract_action_items_from_email(
                            email_data['subject'],
                            email_data['content'],
                            email_data['from_email']
                        )
                        
                        # Store action items
                        for item in action_items:
                            self.storage.store_action_item(user_id, item)
                        
                        total_processed += 1
                        
                except Exception as e:
                    logger.error(f"Error processing message {msg_ref['id']}: {e}")
                    continue
            
            return {
                "status": "success",
                "emails_synced": total_processed,
                "message": f"Successfully synced {total_processed} emails"
            }
            
        except Exception as e:
            logger.error(f"Error syncing emails: {e}")
            return {"status": "error", "message": str(e)}
    
    def sync_calendar(self, user_id: str) -> Dict[str, Any]:
        """Sync calendar events and extract action items"""
        credentials = self.storage.get_user_credentials(user_id)
        if not credentials:
            raise ValueError("User not connected")
        
        # Sync calendar events
        result = self.calendar.sync_calendar_events(user_id, credentials)
        
        # Convert calendar action items to ActionItem objects
        calendar_action_items = []
        for item_data in result.get('action_items', []):
            action_item = ActionItem(
                id=str(uuid.uuid4()),
                title=item_data['title'],
                source=item_data.get('source_calendar_id', 'calendar'),
                source_type='calendar',
                priority=item_data.get('priority', 'medium'),
                due_date=item_data.get('due_date'),
                category=item_data.get('category', 'meeting_prep'),
                context=item_data.get('context', ''),
                metadata={
                    'calendar_event_id': item_data.get('source_calendar_id'),
                    'attendees': item_data.get('attendees', [])
                }
            )
            calendar_action_items.append(action_item)
            
            # Index for search
            self.search.index_action_item(user_id, action_item.to_dict())
        
        # Merge with existing items
        existing_items_data = self.storage.get_action_items(user_id)
        existing_items = []
        
        for item_data in existing_items_data:
            existing_items.append(ActionItem(
                id=item_data['id'],
                title=item_data['title'],
                source=item_data['source'],
                source_type=item_data.get('sourceType', 'email'),
                priority=item_data.get('priority', 'medium'),
                status=item_data.get('status', 'pending'),
                created_at=datetime.fromisoformat(item_data.get('createdAt', datetime.utcnow().isoformat())),
                due_date=item_data.get('dueDate'),
                category=item_data.get('category', 'other'),
                context=item_data.get('context', ''),
                metadata=item_data.get('metaData', {})
            ))
        
        # Add calendar items
        for item in calendar_action_items:
            existing_items.append(item)
        
        # Save updated list
        self.storage.set_action_items(user_id, existing_items)
        
        return {
            'events_synced': len(result.get('events', [])),
            'action_items_created': len(calendar_action_items),
            'events': result.get('events', [])[:10]  # Return first 10 events
        }
    
    def search_content(self, user_id: str, query: str, 
                      source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search across emails and action items"""
        return self.search.search(user_id, query, source_filter)
    
    def get_action_items(self, user_id: str, 
                        status_filter: Optional[str] = None,
                        priority_filter: Optional[str] = None) -> List[ActionItem]:
        """Get action items with optional filters"""
        items_data = self.storage.get_action_items(user_id)
        items = []
        
        for item_data in items_data:
            # Skip items without required fields
            if 'title' not in item_data or 'source' not in item_data:
                continue
                
            # Generate ID if missing (for backwards compatibility)
            if 'id' not in item_data:
                item_data['id'] = str(uuid.uuid4())
                
            item = ActionItem(
                id=item_data['id'],
                title=item_data['title'],
                source=item_data['source'],
                source_type=item_data.get('sourceType', 'email'),
                priority=item_data.get('priority', 'medium'),
                status=item_data.get('status', 'pending'),
                created_at=datetime.fromisoformat(item_data.get('createdAt', datetime.utcnow().isoformat())),
                due_date=item_data.get('dueDate'),
                category=item_data.get('category', 'other'),
                context=item_data.get('context', ''),
                metadata=item_data.get('metaData', {})
            )
            
            # Apply filters
            if status_filter and item.status != status_filter:
                continue
            if priority_filter and item.priority != priority_filter:
                continue
                
            items.append(item)
        
        # Sort by priority and due date
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        items.sort(key=lambda x: (
            priority_order.get(x.priority, 3),
            x.due_date or '9999-12-31',
            x.created_at
        ))
        
        return items
    
    def update_action_item(self, user_id: str, item_id: str, 
                          status: Optional[str] = None,
                          priority: Optional[str] = None) -> bool:
        """Update action item with enhanced features"""
        items_data = self.storage.get_action_items(user_id)
        items = []
        updated = False
        
        for item_data in items_data:
            if item_data['id'] == item_id:
                if status:
                    item_data['status'] = status
                if priority:
                    item_data['priority'] = priority
                updated = True
                
                # Re-index for search
                self.search.index_action_item(user_id, item_data)
            
            items.append(item_data)
        
        if updated:
            self.storage.set_action_items(user_id, items)
        
        return updated
    
    def delete_action_item(self, user_id: str, item_id: str) -> bool:
        """Delete an action item"""
        items_data = self.storage.get_action_items(user_id)
        filtered_items = [item for item in items_data if item['id'] != item_id]
        
        if len(filtered_items) < len(items_data):
            self.storage.set_action_items(user_id, filtered_items)
            return True
        
        return False
    
    def suggest_response(self, user_id: str, item_id: str) -> str:
        """Get AI-suggested response for an action item"""
        items = self.get_action_items(user_id)
        
        for item in items:
            if item.id == item_id:
                # Get the original email if available
                email_data = {
                    'subject': item.metadata.get('subject', ''),
                    'from': item.source
                }
                
                return self.ai.suggest_response(email_data, item.to_dict())
        
        return "I'll take care of this and get back to you soon."
    
    def get_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights about user's workload and patterns"""
        items = self.get_action_items(user_id)
        
        # Calculate statistics
        total_items = len(items)
        pending_items = len([i for i in items if i.status == 'pending'])
        completed_items = len([i for i in items if i.status == 'completed'])
        high_priority = len([i for i in items if i.priority == 'high'])
        
        # Category breakdown
        categories = {}
        for item in items:
            cat = item.category
            categories[cat] = categories.get(cat, 0) + 1
        
        # Overdue items
        today = datetime.now().strftime('%Y-%m-%d')
        overdue = []
        upcoming = []
        
        for item in items:
            if item.due_date and item.status == 'pending':
                if item.due_date < today:
                    overdue.append({
                        'id': item.id,
                        'title': item.title,
                        'due_date': item.due_date,
                        'priority': item.priority
                    })
                elif item.due_date <= (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'):
                    upcoming.append({
                        'id': item.id,
                        'title': item.title,
                        'due_date': item.due_date,
                        'priority': item.priority
                    })
        
        return {
            'summary': {
                'total': total_items,
                'pending': pending_items,
                'completed': completed_items,
                'high_priority': high_priority,
                'completion_rate': round(completed_items / total_items * 100, 1) if total_items > 0 else 0
            },
            'categories': categories,
            'overdue': overdue[:5],  # Top 5 overdue
            'upcoming': upcoming[:5],  # Top 5 upcoming
            'recommendations': self._generate_recommendations(items, overdue, categories)
        }
    
    def _generate_recommendations(self, items: List[ActionItem], 
                                 overdue: List[Dict], 
                                 categories: Dict[str, int]) -> List[str]:
        """Generate smart recommendations"""
        recommendations = []
        
        if len(overdue) > 3:
            recommendations.append(f"You have {len(overdue)} overdue items. Consider prioritizing these today.")
        
        # Find most common category
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            if top_category[1] > 5:
                recommendations.append(f"You have many {top_category[0].replace('_', ' ')} tasks. Consider batching similar tasks.")
        
        # High priority items
        high_priority = [i for i in items if i.priority == 'high' and i.status == 'pending']
        if len(high_priority) > 5:
            recommendations.append(f"You have {len(high_priority)} high-priority items. Consider delegating or rescheduling lower priority tasks.")
        
        return recommendations
    
    def _parse_email(self, message: Dict) -> Dict[str, Any]:
        """Parse Gmail message into structured data"""
        headers = message['payload'].get('headers', [])
        
        email_data = {
            'id': message['id'],
            'thread_id': message.get('threadId', message['id']),  # Add thread_id
            'from': next((h['value'] for h in headers if h['name'] == 'From'), ''),
            'to': next((h['value'] for h in headers if h['name'] == 'To'), ''),
            'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), ''),
            'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
            'body': self._get_email_body(message['payload'])
        }
        
        return email_data
    
    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8', errors='ignore')
        
        return body[:3000]  # Limit body length

    def _store_email_for_display(self, user_id: str, email_data: Dict[str, Any]):
        """Store email in database for display"""
        from sqlalchemy import text
        import json
        from email.utils import parsedate_to_datetime
        
        # Lazy import to avoid circular dependency
        try:
            from .database import get_db
        except ImportError:
            logger.warning("Database not available for email storage")
            return
        
        # Get a database session
        try:
            db = next(get_db())
        except Exception as e:
            logger.warning(f"Could not get database session: {e}")
            return
        
        try:
            # Parse date
            try:
                email_date = parsedate_to_datetime(email_data.get('date', ''))
            except:
                email_date = datetime.utcnow()
            
            # Prepare email record
            email_id = str(uuid.uuid4())
            
            # Use INSERT ... ON CONFLICT DO UPDATE to handle duplicates
            insert_query = text("""
                INSERT INTO oracle_emails (
                    id, user_id, message_id, thread_id, subject, 
                    from_email, to_emails, content, date, 
                    is_sent, is_received, created_at
                ) VALUES (
                    :id, :user_id, :message_id, :thread_id, :subject,
                    :from_email, :to_emails, :content, :date,
                    :is_sent, :is_received, :created_at
                )
                ON CONFLICT (user_id, message_id) DO UPDATE SET
                    subject = EXCLUDED.subject,
                    content = EXCLUDED.content,
                    date = EXCLUDED.date
            """)
            
            db.execute(insert_query, {
                'id': email_id,
                'user_id': user_id,
                'message_id': email_data.get('id'),
                'thread_id': email_data.get('thread_id', email_data.get('id')),  # Use actual thread_id
                'subject': email_data.get('subject', 'No Subject'),
                'from_email': email_data.get('from', ''),
                'to_emails': json.dumps([email_data.get('to', '')]),
                'content': email_data.get('body', ''),  # Changed from 'content' to 'body'
                'date': email_date,
                'is_sent': False,  # Will be determined later
                'is_received': True,
                'created_at': datetime.utcnow()
            })
            
            db.commit()
            logger.info(f"Stored email {email_data.get('id')} for display")
            
        except Exception as e:
            logger.error(f"Error storing email for display: {e}")
            try:
                db.rollback()
            except:
                pass
        finally:
            db.close()

# Global instance
oracle_v2 = OracleV2() 