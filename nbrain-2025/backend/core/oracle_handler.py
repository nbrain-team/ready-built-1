"""
Oracle Handler - Unified personal knowledge assistant
Handles email integration, action item extraction, and multi-source search
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, func, Text, Integer
from .database import Base, get_db

# Import the mixin
from .oracle_email_search import OracleEmailSearchMixin

logger = logging.getLogger(__name__)

# Google OAuth2 configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/oracle/auth/callback")

# For production, the redirect URI should come from environment variable
# This allows different URIs for development and production
logger.info(f"OAuth redirect URI configured as: {GOOGLE_REDIRECT_URI}")

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Database Models for Oracle
class OracleDataSource(Base):
    __tablename__ = "oracle_data_sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'))
    source_type = Column(String, nullable=False)  # email, calendar, drive, voice, meeting
    status = Column(String, default='disconnected')  # connected, disconnected, syncing
    credentials = Column(JSON, nullable=True)  # Encrypted OAuth credentials
    last_sync = Column(DateTime, nullable=True)
    item_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)  # Store error messages
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class OracleActionItem(Base):
    __tablename__ = "oracle_action_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'))
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=True)  # Email ID, calendar event ID, etc.
    due_date = Column(DateTime, nullable=True)
    priority = Column(String, default='medium')  # high, medium, low
    status = Column(String, default='pending')  # pending, completed, deleted
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    task_created = Column(Boolean, default=False)
    task_id = Column(String, nullable=True)

class OracleInsight(Base):
    __tablename__ = "oracle_insights"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    category = Column(String, nullable=False)  # meeting_summary, email_trend, productivity, etc.
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OracleHandler(OracleEmailSearchMixin):
    def __init__(self):
        # Check if credentials are configured
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.warning("Google OAuth credentials not configured. GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set.")
            self.oauth_configured = False
        else:
            self.oauth_configured = True
            logger.info(f"Google OAuth configured with redirect URI: {GOOGLE_REDIRECT_URI}")
            
        self.client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        }
    
    def get_auth_url(self, source_type: str, user_id: str) -> str:
        """Generate OAuth URL for connecting a data source"""
        if not self.oauth_configured:
            raise ValueError("Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
            
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Include state to track source type and user
        state = base64.urlsafe_b64encode(
            json.dumps({"source_type": source_type, "user_id": user_id}).encode()
        ).decode()
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent screen to ensure refresh_token
        )
        
        logger.info(f"Generated auth URL for {source_type}: {auth_url[:50]}...")
        return auth_url
    
    def handle_oauth_callback(self, code: str, state: str, db: Session) -> Dict[str, Any]:
        """Handle OAuth callback and store credentials"""
        # Decode state
        state_data = json.loads(base64.urlsafe_b64decode(state))
        source_type = state_data['source_type']
        user_id = state_data['user_id']
        
        # Exchange code for credentials
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Log credential details for debugging
        logger.info(f"OAuth callback for {source_type} - has refresh_token: {bool(credentials.refresh_token)}")
        
        # Store or update data source
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == user_id,
            OracleDataSource.source_type == source_type
        ).first()
        
        if not data_source:
            data_source = OracleDataSource(
                user_id=user_id,
                source_type=source_type
            )
            db.add(data_source)
        
        # Store credentials (in production, encrypt these)
        data_source.credentials = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Warn if refresh_token is missing
        if not credentials.refresh_token:
            logger.warning(f"No refresh_token received for {source_type}. User may need to revoke access and reconnect.")
        
        data_source.status = 'connected'
        
        db.commit()
        
        return {"status": "success", "source_type": source_type}
    
    def sync_emails(self, user_id: str, db: Session) -> int:
        """Sync emails from Gmail - bidirectional communication (sent and received)"""
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == user_id,
            OracleDataSource.source_type == 'email'
        ).first()
        
        if not data_source or not data_source.credentials:
            raise ValueError("Email not connected")
        
        # Build Gmail service with token refresh
        try:
            creds = Credentials(**data_source.credentials)
            
            # Check if token needs refresh
            if creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                logger.info("Token expired, refreshing...")
                creds.refresh(Request())
                
                # Update stored credentials with new token
                data_source.credentials = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                db.commit()
                logger.info("Token refreshed and saved successfully")
            
            service = build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            logger.error(f"Error building Gmail service: {e}")
            if 'invalid_grant' in str(e) or 'Token has been expired or revoked' in str(e):
                # Token is invalid, user needs to reauthorize
                data_source.status = 'disconnected'
                data_source.error_message = "Token expired or revoked. Please reconnect your email."
                db.commit()
                raise ValueError("Email authentication expired. Please reconnect your email account.")
            raise
        
        # Get user's email address
        try:
            profile = service.users().getProfile(userId='me').execute()
            user_email = profile.get('emailAddress', '')
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            if 'invalid_grant' in str(e):
                data_source.status = 'disconnected'
                data_source.error_message = "Token expired or revoked. Please reconnect your email."
                db.commit()
                raise ValueError("Email authentication expired. Please reconnect your email account.")
            user_email = ''
        
        # Get emails from last 2 months (60 days) with nBrain+Priority label
        # Search for emails where user is either sender OR recipient
        two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y/%m/%d")
        
        # We'll search for threads where the user has participated and has the nBrain+Priority label
        query = f'after:{two_months_ago} label:nBrain+Priority'
        
        logger.info(f"Searching for emails with query: {query}")
        
        try:
            # Get all messages matching our criteria
            all_messages = []
            page_token = None
            
            while True:
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token,
                    maxResults=500  # Get more messages per page
                ).execute()
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                
                page_token = results.get('nextPageToken')
                if not page_token or len(all_messages) >= 1000:  # Limit to 1000 messages
                    break
            
            logger.info(f"Found {len(all_messages)} messages from last 2 months")
            
            action_items_found = 0
            processed_threads = set()  # Track processed thread IDs
            email_count = 0
            
            for message in all_messages:
                try:
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()
                    
                    # Get the thread ID
                    thread_id = msg.get('threadId')
                    
                    # Skip if we've already processed this thread
                    if thread_id in processed_threads:
                        continue
                    
                    processed_threads.add(thread_id)
                    
                    # Get the full thread to analyze the conversation
                    thread = service.users().threads().get(
                        userId='me',
                        id=thread_id
                    ).execute()
                    
                    # Check if this is a bidirectional conversation
                    has_sent = False
                    has_received = False
                    
                    for thread_msg in thread.get('messages', []):
                        headers = thread_msg.get('payload', {}).get('headers', [])
                        from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
                        to_header = next((h['value'] for h in headers if h['name'] == 'To'), '')
                        
                        if user_email and user_email in from_header:
                            has_sent = True
                        if user_email and user_email in to_header:
                            has_received = True
                    
                    # Only process if it's bidirectional (user both sent and received in this thread)
                    if not (has_sent and has_received):
                        continue
                    
                    # Process all messages in the thread
                    for thread_msg in thread.get('messages', []):
                        # Extract email content
                        email_data = self._parse_email(thread_msg)
                        
                        # Store email content for vector search
                        self._store_email_for_search(email_data, user_id, db)
                        
                        # Store in oracle_emails table for display
                        self._store_email_for_display(email_data, user_id, thread_id, db)
                        email_count += 1
                        
                        # Only extract action items from emails in the last 2 weeks
                        email_date = email_data.get('date')
                        if email_date:
                            try:
                                # Parse the email date
                                from email.utils import parsedate_to_datetime
                                parsed_date = parsedate_to_datetime(email_date)
                                two_weeks_ago = datetime.now(parsed_date.tzinfo) - timedelta(days=14)
                                
                                if parsed_date >= two_weeks_ago:
                                    # Extract action items only from recent emails
                                    action_items = self._extract_action_items(email_data)
                                    
                                    for action in action_items:
                                        # Check if action item already exists
                                        existing = db.query(OracleActionItem).filter(
                                            OracleActionItem.user_id == user_id,
                                            OracleActionItem.source_id == thread_msg['id'],
                                            OracleActionItem.title == action['title']
                                        ).first()
                                        
                                        # Also check for similar action items to avoid near-duplicates
                                        if not existing:
                                            # Get all existing action items for this user
                                            all_user_actions = db.query(OracleActionItem).filter(
                                                OracleActionItem.user_id == user_id,
                                                OracleActionItem.status == 'pending'
                                            ).all()
                                            
                                            # Check if a similar action item already exists
                                            is_duplicate = False
                                            for existing_action in all_user_actions:
                                                if self._are_titles_similar(
                                                    action['title'].lower(), 
                                                    existing_action.title.lower()
                                                ):
                                                    is_duplicate = True
                                                    break
                                            
                                            if not is_duplicate:
                                                new_action = OracleActionItem(
                                                    user_id=user_id,
                                                    title=action['title'],
                                                    source=email_data['from'],
                                                    source_type='email',
                                                    source_id=thread_msg['id'],
                                                    due_date=action.get('due_date'),
                                                    priority=action.get('priority', 'medium'),
                                                    meta_data={
                                                        'subject': email_data['subject'],
                                                        'date': email_data['date'],
                                                        'thread_id': thread_id,
                                                        'context': action.get('context', ''),
                                                        'description': action.get('description', ''),
                                                        'from_email': email_data['from'],
                                                        'to_email': email_data['to']
                                                    }
                                                )
                                                db.add(new_action)
                                                action_items_found += 1
                            except Exception as e:
                                logger.error(f"Error parsing email date: {e}")
                
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {e}")
                    continue
            
            # Update sync status
            data_source.last_sync = datetime.utcnow()
            data_source.item_count = email_count
            db.commit()
            
            logger.info(f"Synced {len(processed_threads)} email threads ({email_count} total messages), found {action_items_found} action items")
            return action_items_found
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def _parse_email(self, message: Dict) -> Dict[str, Any]:
        """Parse Gmail message into structured data"""
        headers = message['payload'].get('headers', [])
        
        email_data = {
            'id': message['id'],
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
        
        return body
    
    def _extract_action_items(self, email_data: Dict) -> List[Dict]:
        """Extract action items from email content using patterns and AI"""
        action_items = []
        content = email_data['body'] + '\n' + email_data['subject']
        from_email = email_data.get('from', '')
        subject = email_data.get('subject', '')
        
        # Skip automated emails and payment reminders
        automated_senders = [
            'failed-payments@stripe.com',
            'noreply@',
            'no-reply@',
            'notifications@',
            'updates@',
            'alerts@'
        ]
        
        # Check if it's an automated email
        is_automated = any(sender in from_email.lower() for sender in automated_senders)
        
        # Skip if it's a payment reminder or automated notification
        if is_automated or 'payment' in subject.lower() and 'failed' in subject.lower():
            return []
        
        # Use AI to extract action items if available
        try:
            from .llm_handler import get_llm_handler
            llm = get_llm_handler()
            
            prompt = f"""
            Analyze this email and extract ONLY clear, actionable items that require a response or action.
            Skip generic phrases like "feel free to contact me" unless they're part of a specific request.
            
            Email from: {from_email}
            Subject: {subject}
            Content: {content[:1000]}
            
            For each action item, provide:
            1. A clear, actionable task title (e.g., "Fix Cursor Billing Issue", "Send Edwin Payment via Venmo")
            2. A detailed task description explaining what needs to be done and why
            3. Context about who's involved and what they're asking for
            4. Priority (high/medium/low)
            
            Format as JSON array with objects containing: title, description, context, priority
            
            Example format:
            [{{
                "title": "Fix Cursor Billing Issue",
                "description": "The Cursor subscription payment is failing. Need to update payment method to avoid service interruption.",
                "context": "Cursor support has sent multiple payment failure notifications",
                "priority": "high"
            }}]
            
            Return empty array if no clear action items found.
            """
            
            response = llm.generate_text(prompt)
            # Parse AI response
            try:
                import json
                ai_actions = json.loads(response)
                for action in ai_actions:
                    if isinstance(action, dict) and 'title' in action:
                        action_items.append({
                            'title': action['title'][:200],
                            'description': action.get('description', ''),
                            'context': action.get('context', ''),
                            'priority': action.get('priority', 'medium'),
                            'due_date': self._extract_due_date(content)
                        })
            except:
                # Fall back to pattern matching if AI fails
                pass
                
        except Exception as e:
            logger.debug(f"AI extraction not available, using patterns: {e}")
        
        # If no AI results or AI failed, use pattern matching
        if not action_items:
            # Improved pattern matching for action items
            action_patterns = [
                # Direct requests
                (r'(?:please|could you|can you|will you|would you)\s+([^.!?]+)', 'request'),
                # Specific actions
                (r'(?:send me|provide|share|forward)\s+([^.!?]+)', 'send'),
                # Commitments or tasks
                (r'(?:I need|we need|need to)\s+([^.!?]+)', 'need'),
                # Questions that require action
                (r'(?:when can|how do we|what about)\s+([^.!?]+)\?', 'question'),
                # Explicit action items
                (r'(?:action item|todo|task):\s*([^.!?\n]+)', 'explicit'),
            ]
            
            for pattern, pattern_type in action_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if isinstance(match, str) and len(match.strip()) > 15:
                        # Clean up the match
                        title = match.strip()
                        # Remove trailing punctuation
                        title = re.sub(r'[,;]+$', '', title)
                        
                        # Skip generic phrases
                        generic_phrases = [
                            'at your convenience',
                            'if you have any questions',
                            'let me know',
                            'feel free',
                            'reach out'
                        ]
                        
                        if any(phrase in title.lower() for phrase in generic_phrases):
                            continue
                        
                        # Create more descriptive title based on pattern type
                        if pattern_type == 'send':
                            title = f"Send {title}"
                        elif pattern_type == 'question':
                            title = f"Respond to: {title}"
                        
                        # Generate a better title using key information
                        from_name = re.sub(r'<.*?>', '', from_email).strip()
                        
                        # Try to create a more actionable title
                        if 'payment' in title.lower():
                            if 'cursor' in from_email.lower():
                                title = "Fix Cursor Billing Issue"
                                description = "Update payment information to complete your Cursor subscription purchase"
                            else:
                                title = f"Process Payment for {from_name}"
                                description = f"{from_name} has requested payment processing"
                        elif 'send' in title.lower() and 'list' in title.lower():
                            title = f"Send Contact List to {from_name}"
                            description = f"{from_name} has requested a list of names, emails, and phone numbers"
                        elif 'venmo' in title.lower() or 'zelle' in title.lower():
                            title = f"Send Payment to {from_name} via Venmo/Zelle"
                            description = f"{from_name} has requested payment through Venmo or Zelle"
                        else:
                            # Default description
                            description = f"Action requested by {from_name} regarding: {title}"
                        
                        action_items.append({
                            'title': title[:200],
                            'description': description,
                            'context': f"Request from {from_name} in email about '{subject}'",
                            'priority': self._determine_priority(content),
                            'due_date': self._extract_due_date(content)
                        })
        
        # Remove duplicates based on similar titles
        seen_titles = set()
        unique_actions = []
        
        for action in action_items:
            # Normalize title for comparison
            normalized_title = action['title'].lower().strip()
            
            # Check for similar existing titles
            is_duplicate = False
            for seen in seen_titles:
                # Check if titles are very similar (e.g., differ only by a few words)
                if self._are_titles_similar(normalized_title, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(normalized_title)
                unique_actions.append(action)
        
        return unique_actions[:3]  # Limit to 3 most relevant action items per email
    
    def _are_titles_similar(self, title1: str, title2: str) -> bool:
        """Check if two titles are similar enough to be considered duplicates"""
        # Remove common words
        common_words = {'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with'}
        
        words1 = set(word for word in title1.split() if word not in common_words)
        words2 = set(word for word in title2.split() if word not in common_words)
        
        # If more than 70% of words overlap, consider them similar
        if not words1 or not words2:
            return False
            
        overlap = len(words1.intersection(words2))
        similarity = overlap / min(len(words1), len(words2))
        
        return similarity > 0.7
    
    def _determine_priority(self, content: str) -> str:
        """Determine priority based on keywords"""
        high_priority_keywords = ['urgent', 'asap', 'immediately', 'critical', 'important']
        low_priority_keywords = ['when you can', 'no rush', 'whenever', 'if possible']
        
        content_lower = content.lower()
        
        for keyword in high_priority_keywords:
            if keyword in content_lower:
                return 'high'
        
        for keyword in low_priority_keywords:
            if keyword in content_lower:
                return 'low'
        
        return 'medium'
    
    def _extract_due_date(self, content: str) -> Optional[datetime]:
        """Extract due date from content"""
        # Simple date extraction - in production, use a more robust date parser
        date_patterns = [
            r'(?:by|before|until)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:deadline|due date|due by):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    # Simple date parsing - enhance this in production
                    date_str = match.group(1)
                    # This is a simplified example - use dateutil or similar in production
                    return datetime.strptime(date_str, '%m/%d/%Y')
                except:
                    pass
        
        return None
    
    def search_oracle(self, query: str, user_id: str, sources: List[str], db: Session) -> List[Dict]:
        """Search across all connected data sources"""
        results = []
        
        # For now, search action items and insights
        # In production, this would integrate with vector search across all content
        
        # Search action items
        action_items = db.query(OracleActionItem).filter(
            OracleActionItem.user_id == user_id,
            OracleActionItem.title.ilike(f'%{query}%')
        ).limit(10).all()
        
        for item in action_items:
            results.append({
                'title': item.title,
                'content': f"Action item from {item.source}",
                'source': item.source,
                'timestamp': item.created_at.isoformat(),
                'type': 'action_item'
            })
        
        # Search insights
        insights = db.query(OracleInsight).filter(
            OracleInsight.user_id == user_id,
            OracleInsight.content.ilike(f'%{query}%')
        ).limit(10).all()
        
        for insight in insights:
            results.append({
                'title': insight.category.replace('_', ' ').title(),
                'content': insight.content,
                'source': insight.source,
                'timestamp': insight.created_at.isoformat(),
                'type': 'insight'
            })
        
        return results
    
    def generate_insights(self, user_id: str, db: Session) -> List[Dict]:
        """Generate insights from user's data"""
        insights = []
        
        # Email activity insight
        email_source = db.query(OracleDataSource).filter(
            OracleDataSource.user_id == user_id,
            OracleDataSource.source_type == 'email'
        ).first()
        
        if email_source and email_source.item_count > 0:
            insight = OracleInsight(
                user_id=user_id,
                content=f"You've received {email_source.item_count} emails in the last 7 days.",
                source="Email Analysis",
                category="email_trend"
            )
            db.add(insight)
            insights.append(insight)
        
        # Action items insight
        pending_actions = db.query(OracleActionItem).filter(
            OracleActionItem.user_id == user_id,
            OracleActionItem.status == 'pending'
        ).count()
        
        if pending_actions > 0:
            insight = OracleInsight(
                user_id=user_id,
                content=f"You have {pending_actions} pending action items to complete.",
                source="Task Analysis",
                category="productivity"
            )
            db.add(insight)
            insights.append(insight)
        
        db.commit()
        
        return insights

    def _store_email_for_search(self, email_data: Dict, user_id: str, db: Session):
        """Store email content for vector search (placeholder for future enhancement)"""
        # TODO: Implement vector storage using Pinecone or similar
        # This would involve:
        # 1. Creating embeddings of the email content
        # 2. Storing in vector database with metadata
        # 3. Enabling semantic search across all emails
        pass

# Global instance - use lazy initialization
_oracle_handler_instance = None

def get_oracle_handler():
    """Get or create the global OracleHandler instance"""
    global _oracle_handler_instance
    if _oracle_handler_instance is None:
        _oracle_handler_instance = OracleHandler()
    return _oracle_handler_instance

# For backward compatibility
oracle_handler = get_oracle_handler 