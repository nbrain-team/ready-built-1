"""
Improved Calendar Sync for Client Portal
Better logic for finding calendar events related to clients
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ImprovedCalendarSync:
    """Enhanced calendar sync with inclusive search logic"""
    
    @staticmethod
    def search_calendar_events_for_client(source_id: str, client_emails: List[str], db: Session) -> List[Dict[str, Any]]:
        """
        Search for ANY calendar event that includes the client.
        
        Rules:
        1. Find events where ANY client email/domain is an attendee
        2. Include events organized by us with client attendees
        3. Include events organized by client with us as attendees
        4. Search both past (6 months) and future (1 year) events
        """
        logger.info(f"[ImprovedCalendarSync] Searching for client emails: {client_emails}")
        
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
            
            # Extended time range
            time_min = (datetime.now() - timedelta(days=180)).isoformat() + 'Z'
            time_max = (datetime.now() + timedelta(days=365)).isoformat() + 'Z'
            
            logger.info(f"[ImprovedCalendarSync] Time range: {time_min} to {time_max}")
            
            # Get ALL events in the time range
            all_events = []
            page_token = None
            
            while True:
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=2500,  # Max allowed by API
                    singleEvents=True,
                    orderBy='startTime',
                    pageToken=page_token
                ).execute()
                
                all_events.extend(events_result.get('items', []))
                page_token = events_result.get('nextPageToken')
                
                if not page_token:
                    break
            
            logger.info(f"[ImprovedCalendarSync] Found {len(all_events)} total calendar events")
            
            # Extract domains from client emails
            client_domains = set()
            client_emails_lower = [email.lower() for email in client_emails]
            
            for email in client_emails:
                if '@' in email:
                    domain = email.split('@')[1].lower()
                    client_domains.add(domain)
            
            logger.info(f"[ImprovedCalendarSync] Client domains: {client_domains}")
            
            # Track statistics
            stats = {
                'total_events': len(all_events),
                'future_events': 0,
                'matched_events': 0,
                'match_reasons': {}
            }
            
            current_time = datetime.now()
            matching_events = []
            
            for event in all_events:
                # Skip cancelled events
                if event.get('status') == 'cancelled':
                    continue
                
                # Check if future event
                start = event.get('start', {})
                if 'dateTime' in start:
                    try:
                        event_time = parser.parse(start['dateTime'])
                        if event_time.replace(tzinfo=None) > current_time.replace(tzinfo=None):
                            stats['future_events'] += 1
                    except:
                        pass
                
                # Extract all emails from the event
                event_emails = set()
                
                # Add organizer email
                organizer = event.get('organizer', {})
                if organizer.get('email'):
                    event_emails.add(organizer['email'].lower())
                
                # Add all attendee emails
                attendees = event.get('attendees', [])
                for attendee in attendees:
                    if attendee.get('email'):
                        event_emails.add(attendee['email'].lower())
                
                # Check for matches
                matched = False
                match_reasons = []
                
                # 1. Check exact email matches
                for client_email in client_emails_lower:
                    if client_email in event_emails:
                        matched = True
                        match_reasons.append(f"exact_email:{client_email}")
                
                # 2. Check domain matches
                for event_email in event_emails:
                    for domain in client_domains:
                        if domain in event_email:
                            matched = True
                            match_reasons.append(f"domain:{domain} in {event_email}")
                
                # 3. Check event title and description for client info
                event_text = (
                    event.get('summary', '') + ' ' + 
                    event.get('description', '')
                ).lower()
                
                for domain in client_domains:
                    if domain in event_text:
                        matched = True
                        match_reasons.append(f"domain_in_text:{domain}")
                
                # If matched, parse and add the event
                if matched:
                    event_data = ImprovedCalendarSync._parse_calendar_event(event)
                    if event_data:
                        matching_events.append(event_data)
                        stats['matched_events'] += 1
                        
                        # Track match reasons
                        for reason in match_reasons:
                            reason_type = reason.split(':')[0]
                            stats['match_reasons'][reason_type] = stats['match_reasons'].get(reason_type, 0) + 1
                        
                        # Log matched events
                        is_future = event_data.get('start_time') and event_data['start_time'].replace(tzinfo=None) > current_time.replace(tzinfo=None)
                        logger.info(f"[ImprovedCalendarSync] Matched {'FUTURE' if is_future else 'PAST'} event: {event.get('summary')} - Reasons: {match_reasons}")
            
            # Log statistics
            future_matched = sum(1 for e in matching_events if e.get('start_time') and e['start_time'].replace(tzinfo=None) > current_time.replace(tzinfo=None))
            logger.info(f"[ImprovedCalendarSync] Statistics:")
            logger.info(f"  - Total events searched: {stats['total_events']}")
            logger.info(f"  - Future events in calendar: {stats['future_events']}")
            logger.info(f"  - Matched events: {stats['matched_events']} ({future_matched} future, {stats['matched_events'] - future_matched} past)")
            logger.info(f"  - Match reasons: {stats['match_reasons']}")
            
            return matching_events
            
        except HttpError as error:
            logger.error(f'[ImprovedCalendarSync] Google Calendar API error: {error}')
            return []
        except Exception as e:
            logger.error(f'[ImprovedCalendarSync] Error searching calendar events: {e}')
            return []
    
    @staticmethod
    def _parse_calendar_event(event: Dict) -> Dict[str, Any]:
        """Parse Google Calendar event into our format"""
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
                'status': event.get('status', 'confirmed'),
                'html_link': event.get('htmlLink', '')
            }
        except Exception as e:
            logger.error(f"[ImprovedCalendarSync] Error parsing calendar event: {e}")
            return None 