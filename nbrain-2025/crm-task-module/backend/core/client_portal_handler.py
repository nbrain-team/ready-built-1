"""
Client Portal Handler
Manages client operations and CRM integration
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .database import CRMOpportunity
from .client_portal_models import (
    Client, ClientStatus, ClientTask, ClientCommunication,
    ClientDocument, ClientTeamMember, ClientActivity,
    TaskStatus, TaskPriority
)
from .oracle_handler import oracle_handler, OracleDataSource
from .oracle_email_search import OracleEmailSearchMixin
import re
from .google_drive_handler import google_drive_handler
from .database import User

logger = logging.getLogger(__name__)

class ClientPortalHandler:
    def __init__(self):
        # Create an instance of the email search mixin for content cleaning
        self.email_helper = OracleEmailSearchMixin()
    
    def _clean_email_content(self, content: str) -> str:
        """Clean email content using the Oracle email helper"""
        if hasattr(self.email_helper, '_clean_email_content'):
            return self.email_helper._clean_email_content(content)
        return content
    
    def create_client_from_crm(self, opportunity_id: str, db: Session) -> Client:
        """Create a client from a CRM opportunity"""
        # Get the opportunity
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Check if already converted
        existing = db.query(Client).filter(
            Client.crm_opportunity_id == opportunity_id
        ).first()
        
        if existing:
            raise ValueError(f"Opportunity already converted to client: {existing.name}")
        
        # Parse contract value
        contract_value = None
        if opportunity.actual_contract_value:
            try:
                # Remove currency symbols and commas
                value_str = opportunity.actual_contract_value.replace('$', '').replace(',', '').strip()
                contract_value = float(value_str)
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse contract value: {opportunity.actual_contract_value}")
        
        # Create the client
        client = Client(
            name=opportunity.client_opportunity,
            status=ClientStatus.ACTIVE,
            project_value=contract_value,
            start_date=datetime.utcnow(),
            estimated_end_date=datetime.utcnow() + timedelta(days=90),  # Default 90 days
            crm_opportunity_id=opportunity_id,
            imported_from_crm=True,
            crm_import_date=datetime.utcnow(),
            health_score=85,  # Default health score
            last_communication=datetime.utcnow(),
            total_tasks=0,
            completed_tasks=0
        )
        
        db.add(client)
        db.commit()
        db.refresh(client)
        
        # Create initial activity
        activity = ClientActivity(
            client_id=client.id,
            activity_type="client_created",
            description=f"Client created from CRM opportunity: {opportunity.client_opportunity}",
            meta_data={"opportunity_id": opportunity_id}
        )
        db.add(activity)
        db.commit()
        
        # Create Google Drive folder for the client
        try:
            folder_id = google_drive_handler.create_client_folder(client.name)
            if folder_id:
                logger.info(f"Created Google Drive folder for client {client.name}")
                activity = ClientActivity(
                    client_id=client.id,
                    activity_type="drive_folder_created",
                    description=f"Google Drive folder created for client",
                    meta_data={"folder_id": folder_id}
                )
                db.add(activity)
                db.commit()
        except Exception as e:
            logger.error(f"Error creating Google Drive folder for {client.name}: {e}")
        
        # Perform initial sync
        try:
            self.sync_oracle_emails_to_client(client.id, db)
            self.sync_oracle_calendar_to_client(client.id, db)
        except Exception as e:
            logger.error(f"Error during initial sync for client {client.id}: {e}")
        
        logger.info(f"Created client {client.name} from CRM opportunity {opportunity_id}")
        return client
    
    def sync_email_communications(self, client_id: str, email_addresses: List[str], db: Session):
        """Sync email communications for a client based on email addresses"""
        # This will integrate with the Oracle email sync functionality
        # For now, it's a placeholder
        pass
    
    def sync_oracle_emails_to_client(self, client_id: str, db: Session):
        """Sync emails from Oracle to client communications - from ALL team members"""
        try:
            # Get the client
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.error(f"Client {client_id} not found")
                return
            
            # Get ALL connected email sources from Oracle across ALL users
            # This allows team members to see emails from all connected accounts
            email_sources = db.query(OracleDataSource).filter(
                OracleDataSource.source_type == "email",
                OracleDataSource.status == "connected"
            ).all()
            
            if not email_sources:
                logger.warning("No connected email sources found across any users.")
                # Create an activity to inform the user
                activity = ClientActivity(
                    client_id=client_id,
                    activity_type="sync_failed",
                    description="Email sync failed: No Gmail accounts connected by any team member. Please connect Gmail in the Oracle page.",
                    meta_data={"reason": "no_email_source"}
                )
                db.add(activity)
                db.commit()
                return
            
            logger.info(f"Found {len(email_sources)} connected email sources across all users")
            
            # Build search criteria
            search_emails = []
            search_domains = []
            
            # PRIORITY 1: Use sync_email_addresses if available
            if hasattr(client, 'sync_email_addresses') and client.sync_email_addresses:
                search_emails.extend(client.sync_email_addresses)
                logger.info(f"Using sync_email_addresses: {search_emails}")
            
            # PRIORITY 2: Add primary contact email
            if client.primary_contact_email and client.primary_contact_email not in search_emails:
                search_emails.append(client.primary_contact_email)
                # Extract domain from email
                domain = client.primary_contact_email.split('@')[-1]
                if domain and domain not in search_domains:
                    search_domains.append(domain)
            
            # PRIORITY 3: Add client's domain field if available
            if client.domain and client.domain not in search_domains:
                search_domains.append(client.domain)
            
            # PRIORITY 4: Check website URL for domain
            if client.company_website:
                # Extract domain from website
                website_domain = client.company_website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                if website_domain and website_domain not in search_domains:
                    search_domains.append(website_domain)
            
            # Also check CRM opportunity for additional emails and domains
            if client.crm_opportunity_id:
                opportunity = db.query(CRMOpportunity).filter(
                    CRMOpportunity.id == client.crm_opportunity_id
                ).first()
                if opportunity:
                    if opportunity.contact_email and opportunity.contact_email not in search_emails:
                        search_emails.append(opportunity.contact_email)
                        # Extract domain
                        domain = opportunity.contact_email.split('@')[-1]
                        if domain and domain not in search_domains:
                            search_domains.append(domain)
                    
                    if opportunity.website_url:
                        website_domain = opportunity.website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                        if website_domain and website_domain not in search_domains:
                            search_domains.append(website_domain)
            
            if not search_emails and not search_domains:
                logger.info(f"No email addresses or domains found for client {client.name}")
                return
            
            logger.info(f"Searching for emails with addresses: {search_emails} and domains: {search_domains}")
            
            # Track which user's email source we're syncing from for logging
            synced_from_users = []
            
            # Get emails from Oracle - from ALL connected email sources
            for email_source in email_sources:
                try:
                    # Get the user who owns this email source
                    source_user = db.query(User).filter(
                        User.id == email_source.user_id
                    ).first()
                    
                    if source_user:
                        synced_from_users.append(source_user.email)
                        logger.info(f"Syncing emails from {source_user.email}'s Gmail account")
                    
                    # Search by specific email addresses
                    emails_by_address = []
                    if search_emails:
                        # Check if method exists
                        if hasattr(oracle_handler, 'search_emails_by_participants'):
                            emails_by_address = oracle_handler.search_emails_by_participants(
                                email_source.id,
                                search_emails,
                                db
                            )
                        else:
                            logger.warning("search_emails_by_participants method not implemented in oracle_handler")
                    
                    # Search by domains
                    emails_by_domain = []
                    if search_domains:
                        # Check if method exists
                        if hasattr(oracle_handler, 'search_emails_by_domains'):
                            emails_by_domain = oracle_handler.search_emails_by_domains(
                                email_source.id,
                                search_domains,
                                db
                            )
                        else:
                            logger.warning("search_emails_by_domains method not implemented in oracle_handler")
                    
                    # Combine and deduplicate emails
                    all_emails = {}
                    for email in emails_by_address + emails_by_domain:
                        message_id = email.get('message_id')
                        if message_id:
                            all_emails[message_id] = email
                    
                    # Process unique emails
                    for email_data in all_emails.values():
                        # Check if we already have this email
                        existing = db.query(ClientCommunication).filter(
                            ClientCommunication.email_message_id == email_data.get('message_id'),
                            ClientCommunication.client_id == client_id
                        ).first()
                        
                        if not existing:
                            # Clean email content before saving
                            cleaned_content = self._clean_email_content(email_data.get('body', ''))
                            
                            # Create new communication entry
                            communication = ClientCommunication(
                                client_id=client_id,
                                type="email",
                                subject=email_data.get('subject', 'No subject'),
                                content=cleaned_content,
                                summary=email_data.get('summary'),
                                from_user=email_data.get('from'),
                                to_users=email_data.get('to', []),
                                cc_users=email_data.get('cc', []),
                                email_thread_id=email_data.get('thread_id'),
                                email_message_id=email_data.get('message_id'),
                                is_important=email_data.get('is_important', False),
                                created_at=email_data.get('date').replace(tzinfo=None) if email_data.get('date') and hasattr(email_data.get('date'), 'replace') else datetime.utcnow()
                            )
                            
                            # Add synced_by field if the column exists
                            if hasattr(ClientCommunication, 'synced_by'):
                                communication.synced_by = source_user.email if source_user else None
                            
                            db.add(communication)
                            logger.debug(f"Added email to session: {email_data.get('subject', 'No subject')} - Message ID: {email_data.get('message_id')}")
                            
                            # Update client's last communication if this is more recent
                            if not client.last_communication or (communication.created_at and communication.created_at.replace(tzinfo=None) > (client.last_communication.replace(tzinfo=None) if client.last_communication else datetime.min)):
                                client.last_communication = communication.created_at.replace(tzinfo=None) if communication.created_at else datetime.utcnow()
                        else:
                            logger.debug(f"Email already exists: {email_data.get('subject', 'No subject')} - Message ID: {email_data.get('message_id')}")
                    
                    logger.info(f"Synced {len(all_emails)} emails for client {client.name} from {source_user.email if source_user else 'unknown user'}")
                    
                except Exception as e:
                    logger.error(f"Error syncing emails from source {email_source.id}: {e}")
                    continue
            
            # Create activity log showing which users' accounts were synced
            if synced_from_users:
                activity = ClientActivity(
                    client_id=client_id,
                    activity_type="emails_synced",
                    description=f"Emails synced from team members: {', '.join(set(synced_from_users))}",
                    meta_data={"synced_from": list(set(synced_from_users))}
                )
                db.add(activity)
            
            # Don't commit here - let the endpoint handle the transaction
            # db.commit()
            
        except Exception as e:
            logger.error(f"Error syncing Oracle emails to client {client_id}: {e}")
            # Don't rollback here either - let the endpoint handle it
            # db.rollback()
            raise  # Re-raise the exception so the endpoint can handle it
    
    def sync_oracle_calendar_to_client(self, client_id: str, db: Session):
        """Sync calendar events from Oracle to client activities - from ALL team members"""
        try:
            # Get the client
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.error(f"Client {client_id} not found")
                return
            
            # Get ALL connected calendar sources from Oracle across ALL users
            # This allows team members to see calendar events from all connected accounts
            calendar_sources = db.query(OracleDataSource).filter(
                OracleDataSource.source_type == "calendar",
                OracleDataSource.status == "connected"
            ).all()
            
            if not calendar_sources:
                logger.info("No connected calendar sources found across any users")
                return
            
            logger.info(f"Found {len(calendar_sources)} connected calendar sources across all users")
            
            # Build search criteria (same as email)
            search_emails = []
            
            # PRIORITY 1: Use sync_email_addresses if available
            if hasattr(client, 'sync_email_addresses') and client.sync_email_addresses:
                search_emails.extend(client.sync_email_addresses)
                logger.info(f"Using sync_email_addresses for calendar: {search_emails}")
            
            # PRIORITY 2: Add primary contact email
            if client.primary_contact_email and client.primary_contact_email not in search_emails:
                search_emails.append(client.primary_contact_email)
            
            # Also check CRM opportunity
            if client.crm_opportunity_id:
                opportunity = db.query(CRMOpportunity).filter(
                    CRMOpportunity.id == client.crm_opportunity_id
                ).first()
                if opportunity and opportunity.contact_email and opportunity.contact_email not in search_emails:
                    search_emails.append(opportunity.contact_email)
            
            if not search_emails:
                logger.info(f"No email addresses found for calendar sync for client {client.name}")
                return
            
            logger.info(f"Searching for calendar events with attendees: {search_emails}")
            
            # Track which user's calendar source we're syncing from for logging
            synced_from_users = []
            
            # Get calendar events from Oracle - from ALL connected calendar sources
            for calendar_source in calendar_sources:
                try:
                    # Get the user who owns this calendar source
                    source_user = db.query(User).filter(
                        User.id == calendar_source.user_id
                    ).first()
                    
                    if source_user:
                        synced_from_users.append(source_user.email)
                        logger.info(f"Syncing calendar events from {source_user.email}'s Google Calendar")
                    
                    # Use improved calendar sync
                    from .improved_calendar_sync import ImprovedCalendarSync
                    
                    # Search for events with client attendees
                    events = ImprovedCalendarSync.search_calendar_events_for_client(
                        calendar_source.id,
                        search_emails,
                        db
                    )
                    
                    for event_data in events:
                        # Create communication entry for calendar events
                        existing = db.query(ClientCommunication).filter(
                            ClientCommunication.email_message_id == event_data.get('event_id'),
                            ClientCommunication.client_id == client_id,
                            ClientCommunication.type == "calendar_event"
                        ).first()
                        
                        if not existing:
                            # Format attendees list
                            attendees = event_data.get('attendees', [])
                            attendee_emails = [a.get('email') for a in attendees if a.get('email')]
                            
                            communication = ClientCommunication(
                                client_id=client_id,
                                type="calendar_event",
                                subject=event_data.get('summary', 'Calendar Event'),
                                content=f"Location: {event_data.get('location', 'N/A')}\n\n{event_data.get('description', '')}",
                                from_user=event_data.get('organizer', {}).get('email', 'Unknown'),
                                to_users=attendee_emails,
                                email_message_id=event_data.get('event_id'),  # Use event ID as message ID
                                created_at=event_data.get('start_time').replace(tzinfo=None) if event_data.get('start_time') and hasattr(event_data.get('start_time'), 'replace') else datetime.utcnow()
                            )
                            db.add(communication)
                            
                            # Create activity for upcoming meetings
                            if event_data.get('start_time') and event_data.get('start_time') > datetime.utcnow():
                                activity = ClientActivity(
                                    client_id=client_id,
                                    activity_type="upcoming_meeting",
                                    description=f"Meeting: {event_data.get('summary', 'Untitled')}",
                                    meta_data={
                                        "event_id": event_data.get('event_id'),
                                        "start_time": event_data.get('start_time').isoformat(),
                                        "end_time": event_data.get('end_time').isoformat() if event_data.get('end_time') else None,
                                        "location": event_data.get('location'),
                                        "synced_from": source_user.email if source_user else None
                                    }
                                )
                                db.add(activity)
                    
                    logger.info(f"Synced {len(events)} calendar events for client {client.name} from {source_user.email if source_user else 'unknown user'}")
                    
                except Exception as e:
                    logger.error(f"Error syncing calendar from source {calendar_source.id}: {e}")
                    continue
            
            # Create activity log showing which users' calendars were synced
            if synced_from_users:
                activity = ClientActivity(
                    client_id=client_id,
                    activity_type="calendars_synced",
                    description=f"Calendar events synced from team members: {', '.join(set(synced_from_users))}",
                    meta_data={"synced_from": list(set(synced_from_users))}
                )
                db.add(activity)
            
            # Don't commit here - let the endpoint handle the transaction
            # db.commit()
            
        except Exception as e:
            logger.error(f"Error syncing Oracle calendar to client {client_id}: {e}")
            # Don't rollback here either - let the endpoint handle it
            # db.rollback()
            raise  # Re-raise the exception so the endpoint can handle it
    
    def auto_create_tasks_from_emails(self, client_id: str, db: Session):
        """Automatically create tasks from email action items"""
        try:
            # Get recent email communications
            recent_emails = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id,
                ClientCommunication.type == "email"
            ).order_by(ClientCommunication.created_at.desc()).limit(20).all()
            
            for email in recent_emails:
                # Use AI to extract action items from email content
                if email.content:
                    action_items = []
                    if hasattr(oracle_handler, 'extract_action_items_from_text'):
                        action_items = oracle_handler.extract_action_items_from_text(email.content)
                    else:
                        logger.warning("extract_action_items_from_text method not implemented in oracle_handler")
                        continue
                    
                    for action_item in action_items:
                        # Check if task already exists
                        existing_task = db.query(ClientTask).filter(
                            ClientTask.client_id == client_id,
                            ClientTask.title == action_item['title']
                        ).first()
                        
                        if not existing_task:
                            # Create new task
                            task = ClientTask(
                                client_id=client_id,
                                title=action_item['title'],
                                description=f"Extracted from email: {email.subject}\n\n{action_item.get('description', '')}",
                                priority=TaskPriority.MEDIUM,
                                status=TaskStatus.TODO
                            )
                            db.add(task)
                            
                            # Update client task count
                            client = db.query(Client).filter(Client.id == client_id).first()
                            if client:
                                client.total_tasks += 1
            
            db.commit()
            logger.info(f"Auto-created tasks from emails for client {client_id}")
            
        except Exception as e:
            logger.error(f"Error auto-creating tasks from emails: {e}")
            db.rollback()
    
    def calculate_health_score(self, client_id: str, db: Session) -> int:
        """Calculate client health score based on various factors"""
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return 0
        
        score = 100
        
        # Factor 1: Task completion rate
        if client.total_tasks > 0:
            completion_rate = (client.completed_tasks / client.total_tasks) * 100
            if completion_rate < 50:
                score -= 20
            elif completion_rate < 75:
                score -= 10
        
        # Factor 2: Communication frequency
        if client.last_communication:
            days_since_communication = (datetime.utcnow() - client.last_communication).days
            if days_since_communication > 14:
                score -= 20
            elif days_since_communication > 7:
                score -= 10
        else:
            score -= 30  # No communication recorded
        
        # Factor 3: Project timeline
        if client.estimated_end_date and client.estimated_end_date < datetime.utcnow():
            score -= 15  # Project is overdue
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def get_client_summary(self, client_id: str, db: Session) -> Dict[str, Any]:
        """Get comprehensive client summary including all related data"""
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None
        
        # Get team members count
        team_count = db.query(ClientTeamMember).filter(
            ClientTeamMember.client_id == client_id,
            ClientTeamMember.is_active == True
        ).count()
        
        # Get recent activities
        recent_activities = db.query(ClientActivity).filter(
            ClientActivity.client_id == client_id
        ).order_by(ClientActivity.created_at.desc()).limit(10).all()
        
        # Get task summary
        tasks = db.query(ClientTask).filter(
            ClientTask.client_id == client_id
        ).all()
        
        task_summary = {
            "total": len(tasks),
            "todo": len([t for t in tasks if t.status == TaskStatus.TODO]),
            "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "overdue": len([t for t in tasks if t.due_date and t.due_date < datetime.utcnow() and t.status != TaskStatus.COMPLETED])
        }
        
        return {
            "client": client,
            "health_score": self.calculate_health_score(client_id, db),
            "team_count": team_count,
            "task_summary": task_summary,
            "recent_activities": recent_activities
        }

# Singleton instance
client_portal_handler = ClientPortalHandler() 