"""
Oracle Email Search Methods
Extensions to oracle_handler for client-specific email searching
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from sqlalchemy.orm import Session
from dateutil import parser

# Remove the circular import - we'll import it inside methods as needed

logger = logging.getLogger(__name__)

class OracleEmailSearchMixin:
    """Mixin class to add email search capabilities to OracleHandler"""
    
    def search_emails_by_participants(self, source_id: str, email_addresses: List[str], db: Session) -> List[Dict[str, Any]]:
        """Search emails that include specific participants (to, from, cc)"""
        logger.info(f"Searching emails by participants: {email_addresses}")
        
        # Import here to avoid circular dependency
        from .oracle_handler import OracleDataSource
        
        # Get the data source
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.id == source_id
        ).first()
        
        if not data_source or not data_source.credentials:
            logger.error(f"Data source {source_id} not found or not connected")
            return []
        
        try:
            # Build Gmail service
            creds = Credentials(**data_source.credentials)
            service = build('gmail', 'v1', credentials=creds)
            
            # Build query for Gmail API
            # Search for emails to/from/cc any of the provided addresses
            query_parts = []
            for email in email_addresses:
                query_parts.extend([
                    f'from:{email}',
                    f'to:{email}',
                    f'cc:{email}'
                ])
            
            # Combine with OR logic and limit to last 6 months
            date_limit = (datetime.now() - timedelta(days=180)).strftime("%Y/%m/%d")
            query = f'({" OR ".join(query_parts)}) after:{date_limit}'
            
            logger.info(f"Gmail query: {query}")
            
            # Execute search
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Limit to 100 most recent
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages[:50]:  # Process up to 50 emails
                try:
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()
                    
                    email_data = self._parse_email_for_client(msg)
                    if email_data:
                        emails.append(email_data)
                
                except Exception as e:
                    logger.error(f"Error parsing email {message['id']}: {e}")
                    continue
            
            logger.info(f"Found {len(emails)} emails for participants: {email_addresses}")
            return emails
            
        except HttpError as error:
            logger.error(f'Gmail API error: {error}')
            return []
        except Exception as e:
            error_msg = str(e)
            if 'refresh_token' in error_msg:
                logger.error(f'Gmail credentials expired. User needs to disconnect and reconnect Gmail in Oracle page.')
            else:
                logger.error(f'Error searching emails by participants: {e}')
            return []
    
    def search_emails_by_domains(self, source_id: str, domains: List[str], db: Session) -> List[Dict[str, Any]]:
        """Search emails from specific domains"""
        logger.info(f"Searching emails by domains: {domains}")
        
        # Import here to avoid circular dependency
        from .oracle_handler import OracleDataSource
        
        # Get the data source
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.id == source_id
        ).first()
        
        if not data_source or not data_source.credentials:
            logger.error(f"Data source {source_id} not found or not connected")
            return []
        
        try:
            # Build Gmail service
            creds = Credentials(**data_source.credentials)
            service = build('gmail', 'v1', credentials=creds)
            
            # Build query for Gmail API
            # Search for emails from any of the provided domains
            query_parts = []
            for domain in domains:
                query_parts.extend([
                    f'from:@{domain}',
                    f'to:@{domain}'
                ])
            
            # Combine with OR logic and limit to last 6 months
            date_limit = (datetime.now() - timedelta(days=180)).strftime("%Y/%m/%d")
            query = f'({" OR ".join(query_parts)}) after:{date_limit}'
            
            logger.info(f"Gmail query: {query}")
            
            # Execute search
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Limit to 100 most recent
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages[:50]:  # Process up to 50 emails
                try:
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()
                    
                    email_data = self._parse_email_for_client(msg)
                    if email_data:
                        emails.append(email_data)
                
                except Exception as e:
                    logger.error(f"Error parsing email {message['id']}: {e}")
                    continue
            
            logger.info(f"Found {len(emails)} emails for domains: {domains}")
            return emails
            
        except HttpError as error:
            logger.error(f'Gmail API error: {error}')
            return []
        except Exception as e:
            logger.error(f'Error searching emails by domains: {e}')
            return []
    
    def search_calendar_events_by_attendees(self, source_id: str, attendee_emails: List[str], db: Session) -> List[Dict[str, Any]]:
        """Search calendar events with specific attendees"""
        logger.info(f"Searching calendar events by attendees: {attendee_emails}")
        
        # Import here to avoid circular dependency
        from .oracle_handler import OracleDataSource
        
        # Get the data source
        data_source = db.query(OracleDataSource).filter(
            OracleDataSource.id == source_id
        ).first()
        
        if not data_source or not data_source.credentials:
            logger.error(f"Data source {source_id} not found or not connected")
            return []
        
        try:
            # Build Calendar service
            creds = Credentials(**data_source.credentials)
            service = build('calendar', 'v3', credentials=creds)
            
            # Get events from primary calendar
            # Look for events from 6 months ago to 6 months in the future
            time_min = (datetime.now() - timedelta(days=180)).isoformat() + 'Z'
            time_max = (datetime.now() + timedelta(days=180)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=250,  # Increased from 100 to capture more recurring events
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            matching_events = []
            
            logger.info(f"Found {len(events)} total calendar events to search through")
            
            # Extract domains from attendee emails for broader matching
            attendee_domains = []
            for email in attendee_emails:
                if '@' in email:
                    domain = email.split('@')[1].lower()
                    if domain not in attendee_domains:
                        attendee_domains.append(domain)
            
            logger.info(f"Looking for events with emails: {attendee_emails} or domains: {attendee_domains}")
            
            for event in events:
                # Skip cancelled events
                if event.get('status') == 'cancelled':
                    continue
                    
                # Check if any of the attendee emails are in this event
                attendees = event.get('attendees', [])
                attendee_emails_in_event = [a.get('email', '').lower() for a in attendees]
                
                # Also check organizer
                organizer_email = event.get('organizer', {}).get('email', '').lower()
                all_event_emails = attendee_emails_in_event + [organizer_email]
                
                # Also check the summary/title and description for domain names
                event_summary = event.get('summary', '').lower()
                event_description = event.get('description', '').lower()
                
                # Check for matches
                matched = False
                match_reason = ""
                
                for target_email in attendee_emails:
                    target_lower = target_email.lower()
                    # Check exact email match
                    if target_lower in all_event_emails:
                        matched = True
                        match_reason = f"attendee email: {target_email}"
                        break
                
                # If no direct email match, check for domain matches
                if not matched:
                    for domain in attendee_domains:
                        # Check if domain is in attendee emails
                        for event_email in all_event_emails:
                            if domain in event_email:
                                matched = True
                                match_reason = f"domain {domain} in attendee: {event_email}"
                                break
                        
                        # Check if domain is mentioned in the event title or description
                        if not matched and (domain in event_summary or domain in event_description):
                            matched = True
                            match_reason = f"domain {domain} in title/description"
                            logger.info(f"Found event by domain in title/description: {event.get('summary')}")
                
                if matched:
                    event_data = self._parse_calendar_event_for_client(event)
                    if event_data:
                        matching_events.append(event_data)
                        # Log the matched event for debugging
                        logger.debug(f"Matched event: {event.get('summary')} on {event_data.get('start_time')} - Reason: {match_reason}")
            
            logger.info(f"Found {len(matching_events)} matching calendar events")
            return matching_events
            
        except Exception as e:
            logger.error(f'Error searching calendar events: {e}')
            return []
    
    def _clean_email_content(self, content: str) -> str:
        """Clean email content of common artifacts"""
        if not content:
            return ""
        
        # Remove image placeholders like [image: icon]
        cleaned = re.sub(r'\[image:[^\]]+\]', '', content)
        
        # Remove cid: image references
        cleaned = re.sub(r'\[cid:[^\]]+\]', '', cleaned)
        
        # Clean up URLs in angle brackets but keep the URL
        cleaned = re.sub(r'<(https?://[^>]+)>', r'\1', cleaned)
        
        # Remove excessive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove excessive spaces
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        
        return cleaned.strip()
    
    def _parse_email_for_client(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into a format suitable for client portal"""
        try:
            # Get message metadata
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            to_emails = next((h['value'] for h in headers if h['name'] == 'To'), '')
            cc_emails = next((h['value'] for h in headers if h['name'] == 'Cc'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse date
            try:
                date = parser.parse(date_str)
            except:
                date = datetime.utcnow()
            
            # Extract email body
            body = self._extract_body(msg['payload'])
            
            # Clean the body content
            body = self._clean_email_content(body)
            
            # Parse recipient lists
            to_list = [email.strip() for email in to_emails.split(',') if email.strip()]
            cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
            
            return {
                'message_id': msg['id'],
                'thread_id': msg.get('threadId'),
                'subject': subject,
                'from': from_email,
                'to': to_list,
                'cc': cc_list,
                'date': date,
                'body': body,
                'summary': body[:200] + '...' if len(body) > 200 else body,
                'is_important': 'IMPORTANT' in msg.get('labelIds', [])
            }
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from Gmail message payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif 'parts' in part:
                    # Recursive search for nested parts
                    body = self._extract_body(part)
                    if body:
                        break
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        return body
    
    def _parse_calendar_event_for_client(self, event: Dict) -> Dict[str, Any]:
        """Parse calendar event for client portal format"""
        try:
            # Extract start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Handle all-day events vs timed events
            if 'dateTime' in start:
                start_time = parser.parse(start['dateTime'])
            elif 'date' in start:
                start_time = parser.parse(start['date'])
            else:
                start_time = None
            
            if 'dateTime' in end:
                end_time = parser.parse(end['dateTime'])
            elif 'date' in end:
                end_time = parser.parse(end['date'])
            else:
                end_time = None
            
            return {
                'event_id': event.get('id'),
                'summary': event.get('summary', 'Untitled Event'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start_time': start_time,
                'end_time': end_time,
                'organizer': event.get('organizer', {}),
                'attendees': event.get('attendees', []),
                'status': event.get('status', 'confirmed')
            }
        except Exception as e:
            logger.error(f"Error parsing calendar event: {e}")
            return None
    
    def _extract_emails_from_header(self, header_value: str) -> List[str]:
        """Extract email addresses from header value"""
        # Simple regex to extract emails
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        return re.findall(email_pattern, header_value)
    
    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:  # Handle nested parts
                    body += self._get_email_body(part)
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8', errors='ignore')
        
        return body.strip() 