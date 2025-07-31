"""
Read.ai Webhook Handler
Processes webhook data from Read.ai and integrates with Oracle and Client Portal
"""

import logging
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .readai_models import ReadAIIntegration, ReadAIMeeting
from .client_portal_models import Client, ClientCommunication
from .oracle_handler import OracleActionItem, OracleInsight, oracle_handler
from .database import get_db

logger = logging.getLogger(__name__)


class ReadAIHandler:
    """Handles Read.ai webhook processing and data integration"""
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature from Read.ai"""
        if not secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True
            
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook(self, webhook_data: Dict[str, Any], user_id: str, db: Session) -> Dict[str, Any]:
        """Process incoming webhook from Read.ai"""
        try:
            # Get or create integration
            integration = db.query(ReadAIIntegration).filter(
                ReadAIIntegration.user_id == user_id
            ).first()
            
            if not integration:
                integration = ReadAIIntegration(
                    user_id=user_id,
                    integration_status='active'
                )
                db.add(integration)
                db.flush()
            
            # Update last webhook timestamp
            integration.last_webhook_at = datetime.utcnow()
            
            # Extract meeting data from webhook
            meeting_data = self._extract_meeting_data(webhook_data)
            
            # Check if meeting already exists
            existing_meeting = db.query(ReadAIMeeting).filter(
                ReadAIMeeting.readai_meeting_id == meeting_data['readai_meeting_id']
            ).first()
            
            if existing_meeting:
                # Update existing meeting
                for key, value in meeting_data.items():
                    setattr(existing_meeting, key, value)
                meeting = existing_meeting
                logger.info(f"Updated existing Read.ai meeting: {meeting.meeting_title}")
            else:
                # Create new meeting record
                meeting = ReadAIMeeting(
                    integration_id=integration.id,
                    webhook_received_at=datetime.utcnow(),
                    raw_webhook_data=webhook_data,
                    **meeting_data
                )
                db.add(meeting)
                logger.info(f"Created new Read.ai meeting: {meeting.meeting_title}")
            
            # Associate with client if possible
            client = self._find_associated_client(meeting, db)
            if client:
                meeting.client_id = client.id
                logger.info(f"Associated meeting with client: {client.name}")
                
                # Create communication record
                self._create_client_communication(meeting, client, db)
            
            # Create Oracle action items
            if meeting.action_items:
                self._create_oracle_action_items(meeting, user_id, db)
            
            # Generate Oracle insights
            self._generate_oracle_insights(meeting, user_id, db)
            
            db.commit()
            
            return {
                "success": True,
                "meeting_id": meeting.id,
                "client_associated": bool(client),
                "action_items_created": len(meeting.action_items or [])
            }
            
        except Exception as e:
            logger.error(f"Error processing Read.ai webhook: {e}", exc_info=True)
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_meeting_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meeting data from webhook payload"""
        # This will need to be adapted based on Read.ai's actual webhook format
        # For now, creating a flexible structure that can handle various formats
        
        meeting_data = {
            'readai_meeting_id': webhook_data.get('meeting_id', webhook_data.get('id')),
            'meeting_title': webhook_data.get('title', 'Untitled Meeting'),
            'meeting_url': webhook_data.get('meeting_url'),
            'meeting_platform': webhook_data.get('platform', webhook_data.get('meeting_platform')),
            'participants': webhook_data.get('participants', []),
            'host_email': webhook_data.get('host_email'),
            'start_time': self._parse_datetime(webhook_data.get('start_time')),
            'end_time': self._parse_datetime(webhook_data.get('end_time')),
            'duration_minutes': webhook_data.get('duration_minutes'),
            'transcript': webhook_data.get('transcript'),
            'summary': webhook_data.get('summary'),
            'key_points': webhook_data.get('key_points', []),
            'action_items': webhook_data.get('action_items', []),
            'sentiment_score': webhook_data.get('sentiment_score'),
            'engagement_score': webhook_data.get('engagement_score')
        }
        
        # Calculate duration if not provided
        if not meeting_data['duration_minutes'] and meeting_data['start_time'] and meeting_data['end_time']:
            duration = meeting_data['end_time'] - meeting_data['start_time']
            meeting_data['duration_minutes'] = duration.total_seconds() / 60
        
        return meeting_data
    
    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from webhook"""
        if not dt_string:
            return None
            
        # Try common datetime formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse datetime: {dt_string}")
        return None
    
    def _find_associated_client(self, meeting: ReadAIMeeting, db: Session) -> Optional[Client]:
        """Find client associated with the meeting based on participants"""
        if not meeting.participants:
            return None
        
        # Extract all participant emails
        participant_emails = []
        for participant in meeting.participants:
            if isinstance(participant, dict):
                email = participant.get('email')
                if email:
                    participant_emails.append(email.lower())
            elif isinstance(participant, str) and '@' in participant:
                participant_emails.append(participant.lower())
        
        if not participant_emails:
            return None
        
        # Search for clients with matching domains or email addresses
        for email in participant_emails:
            domain = email.split('@')[1] if '@' in email else None
            
            # Check by domain
            if domain:
                client = db.query(Client).filter(
                    Client.domain == domain
                ).first()
                if client:
                    return client
            
            # Check by email in sync_email_addresses
            clients = db.query(Client).filter(
                Client.sync_email_addresses.contains([email])
            ).all()
            if clients:
                return clients[0]
            
            # Check by primary contact email
            client = db.query(Client).filter(
                Client.primary_contact_email == email
            ).first()
            if client:
                return client
        
        return None
    
    def _create_client_communication(self, meeting: ReadAIMeeting, client: Client, db: Session):
        """Create client communication record from meeting"""
        communication = ClientCommunication(
            client_id=client.id,
            type='meeting',
            subject=f"Meeting: {meeting.meeting_title}",
            content=meeting.summary or meeting.transcript or "Meeting transcript pending",
            date=meeting.start_time,
            participants=meeting.participants,
            source='Read.ai',
            metadata={
                'readai_meeting_id': meeting.readai_meeting_id,
                'meeting_url': meeting.meeting_url,
                'platform': meeting.meeting_platform,
                'duration_minutes': meeting.duration_minutes,
                'key_points': meeting.key_points,
                'action_items': meeting.action_items
            }
        )
        db.add(communication)
        logger.info(f"Created client communication for meeting: {meeting.meeting_title}")
    
    def _create_oracle_action_items(self, meeting: ReadAIMeeting, user_id: str, db: Session):
        """Create Oracle action items from meeting action items"""
        if not meeting.action_items:
            return
        
        created_count = 0
        for item in meeting.action_items:
            if isinstance(item, dict):
                title = item.get('title', item.get('description', 'Action Item'))
                due_date = self._parse_datetime(item.get('due_date'))
                assignee = item.get('assignee')
            else:
                title = str(item)
                due_date = None
                assignee = None
            
            action_item = OracleActionItem(
                user_id=user_id,
                title=title,
                source=f"Read.ai: {meeting.meeting_title}",
                source_type='meeting',
                source_id=meeting.readai_meeting_id,
                due_date=due_date,
                priority='medium',
                status='pending',
                meta_data={
                    'assignee': assignee,
                    'meeting_date': meeting.start_time.isoformat() if meeting.start_time else None,
                    'client_id': meeting.client_id
                }
            )
            db.add(action_item)
            created_count += 1
        
        meeting.oracle_action_items_created = created_count
        meeting.synced_to_oracle = True
        logger.info(f"Created {created_count} Oracle action items from meeting")
    
    def _generate_oracle_insights(self, meeting: ReadAIMeeting, user_id: str, db: Session):
        """Generate Oracle insights from meeting data"""
        # Meeting summary insight
        if meeting.summary:
            insight = OracleInsight(
                user_id=user_id,
                content=f"Meeting Summary - {meeting.meeting_title}: {meeting.summary}",
                source=f"Read.ai Meeting",
                category='meeting_summary',
                meta_data={
                    'meeting_id': meeting.readai_meeting_id,
                    'meeting_date': meeting.start_time.isoformat() if meeting.start_time else None,
                    'participants': meeting.participants,
                    'client_id': meeting.client_id
                }
            )
            db.add(insight)
        
        # Key points as individual insights
        if meeting.key_points:
            for point in meeting.key_points[:3]:  # Limit to top 3 key points
                if isinstance(point, dict):
                    content = point.get('content', point.get('text', str(point)))
                else:
                    content = str(point)
                
                insight = OracleInsight(
                    user_id=user_id,
                    content=f"Key Discussion Point: {content}",
                    source=f"Read.ai: {meeting.meeting_title}",
                    category='meeting_highlight',
                    meta_data={
                        'meeting_id': meeting.readai_meeting_id,
                        'client_id': meeting.client_id
                    }
                )
                db.add(insight)
        
        logger.info(f"Generated Oracle insights for meeting: {meeting.meeting_title}")
    
    def search_meetings(self, query: str, user_id: str, client_id: Optional[str], db: Session) -> List[Dict[str, Any]]:
        """Search through Read.ai meeting transcripts"""
        meetings_query = db.query(ReadAIMeeting).join(ReadAIIntegration).filter(
            ReadAIIntegration.user_id == user_id
        )
        
        if client_id:
            meetings_query = meetings_query.filter(ReadAIMeeting.client_id == client_id)
        
        # Simple text search - in production, you'd want to use full-text search or vector embeddings
        search_term = f"%{query.lower()}%"
        meetings = meetings_query.filter(
            or_(
                ReadAIMeeting.meeting_title.ilike(search_term),
                ReadAIMeeting.transcript.ilike(search_term),
                ReadAIMeeting.summary.ilike(search_term)
            )
        ).order_by(ReadAIMeeting.start_time.desc()).limit(10).all()
        
        results = []
        for meeting in meetings:
            results.append({
                'id': meeting.id,
                'title': meeting.meeting_title,
                'date': meeting.start_time.isoformat() if meeting.start_time else None,
                'summary': meeting.summary,
                'client_id': meeting.client_id,
                'platform': meeting.meeting_platform,
                'duration_minutes': meeting.duration_minutes,
                'action_items': meeting.action_items,
                'participants': meeting.participants
            })
        
        return results


# Singleton instance
readai_handler = ReadAIHandler() 