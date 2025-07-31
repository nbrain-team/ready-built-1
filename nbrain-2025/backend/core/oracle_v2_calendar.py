"""
Oracle V2 Calendar Module - Google Calendar integration
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class OracleCalendar:
    """Calendar integration for Oracle V2"""
    
    def sync_calendar_events(self, user_id: str, credentials: Dict[str, Any], 
                            days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Sync calendar events and extract action items"""
        
        try:
            # Build Calendar service
            creds = Credentials(**credentials)
            service = build('calendar', 'v3', credentials=creds)
            
            # Time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Get events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process events for action items
            action_items = []
            calendar_events = []
            
            for event in events:
                event_data = self._parse_event(event)
                calendar_events.append(event_data)
                
                # Extract action items from events
                actions = self._extract_event_actions(event_data)
                action_items.extend(actions)
            
            logger.info(f"Synced {len(events)} calendar events, found {len(action_items)} action items")
            
            return {
                'events': calendar_events,
                'action_items': action_items
            }
            
        except HttpError as error:
            logger.error(f'Calendar API error: {error}')
            raise
        except Exception as e:
            logger.error(f'Calendar sync error: {e}')
            raise
    
    def _parse_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Google Calendar event"""
        
        # Get start time
        start = event.get('start', {})
        start_time = start.get('dateTime', start.get('date'))
        
        # Get end time
        end = event.get('end', {})
        end_time = end.get('dateTime', end.get('date'))
        
        # Get attendees
        attendees = []
        for attendee in event.get('attendees', []):
            attendees.append({
                'email': attendee.get('email', ''),
                'name': attendee.get('displayName', ''),
                'response': attendee.get('responseStatus', 'needsAction'),
                'organizer': attendee.get('organizer', False)
            })
        
        return {
            'id': event.get('id', ''),
            'summary': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start': start_time,
            'end': end_time,
            'attendees': attendees,
            'organizer': event.get('organizer', {}).get('email', ''),
            'status': event.get('status', 'confirmed'),
            'htmlLink': event.get('htmlLink', ''),
            'reminders': event.get('reminders', {}),
            'created': event.get('created', ''),
            'updated': event.get('updated', '')
        }
    
    def _extract_event_actions(self, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract action items from calendar events"""
        
        action_items = []
        summary = event_data.get('summary', '').lower()
        description = event_data.get('description', '').lower()
        
        # Check for meeting preparation
        if any(word in summary for word in ['meeting', 'call', 'discussion', 'review']):
            # Meeting prep action
            action_items.append({
                'title': f"Prepare for: {event_data.get('summary', 'Meeting')}",
                'priority': 'high',
                'due_date': self._get_prep_date(event_data.get('start')),
                'category': 'meeting_prep',
                'context': f"Meeting on {self._format_date(event_data.get('start'))}",
                'source_calendar_id': event_data.get('id'),
                'attendees': [a['email'] for a in event_data.get('attendees', [])]
            })
        
        # Check for presentation/demo
        if any(word in summary for word in ['presentation', 'demo', 'pitch']):
            action_items.append({
                'title': f"Prepare presentation for: {event_data.get('summary', 'Event')}",
                'priority': 'high',
                'due_date': self._get_prep_date(event_data.get('start')),
                'category': 'presentation_prep',
                'context': f"Event on {self._format_date(event_data.get('start'))}",
                'source_calendar_id': event_data.get('id')
            })
        
        # Check for deadlines in description
        if 'deadline' in description or 'due' in description:
            action_items.append({
                'title': f"Complete tasks for: {event_data.get('summary', 'Event')}",
                'priority': 'high',
                'due_date': self._format_date_iso(event_data.get('start')),
                'category': 'deadline',
                'context': event_data.get('description', ''),
                'source_calendar_id': event_data.get('id')
            })
        
        # Check for follow-up needed
        if 'follow up' in description or 'follow-up' in description:
            action_items.append({
                'title': f"Follow up after: {event_data.get('summary', 'Event')}",
                'priority': 'medium',
                'due_date': self._get_followup_date(event_data.get('end')),
                'category': 'follow_up',
                'context': f"Follow up needed after event on {self._format_date(event_data.get('start'))}",
                'source_calendar_id': event_data.get('id')
            })
        
        return action_items
    
    def _get_prep_date(self, event_start: str) -> Optional[str]:
        """Get preparation date (1 day before event)"""
        try:
            event_date = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
            prep_date = event_date - timedelta(days=1)
            return prep_date.strftime('%Y-%m-%d')
        except:
            return None
    
    def _get_followup_date(self, event_end: str) -> Optional[str]:
        """Get follow-up date (1 day after event)"""
        try:
            event_date = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
            followup_date = event_date + timedelta(days=1)
            return followup_date.strftime('%Y-%m-%d')
        except:
            return None
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display"""
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date.strftime('%B %d, %Y at %I:%M %p')
        except:
            return date_str
    
    def _format_date_iso(self, date_str: str) -> str:
        """Format date to ISO format"""
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date.strftime('%Y-%m-%d')
        except:
            return None
    
    def create_event(self, user_id: str, credentials: Dict[str, Any],
                    event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event"""
        
        try:
            creds = Credentials(**credentials)
            service = build('calendar', 'v3', credentials=creds)
            
            # Build event
            event = {
                'summary': event_data.get('summary', 'New Event'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data.get('start'),
                    'timeZone': event_data.get('timezone', 'UTC'),
                },
                'end': {
                    'dateTime': event_data.get('end'),
                    'timeZone': event_data.get('timezone', 'UTC'),
                },
                'attendees': [
                    {'email': email} for email in event_data.get('attendees', [])
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            if event_data.get('location'):
                event['location'] = event_data['location']
            
            # Create event
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(f"Created calendar event: {created_event.get('id')}")
            return created_event
            
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            raise
    
    def get_busy_times(self, user_id: str, credentials: Dict[str, Any],
                      days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get busy time slots from calendar"""
        
        try:
            creds = Credentials(**credentials)
            service = build('calendar', 'v3', credentials=creds)
            
            # Time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Get free/busy info
            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}]
            }
            
            freebusy_result = service.freebusy().query(body=body).execute()
            
            busy_times = []
            calendars = freebusy_result.get('calendars', {})
            
            for cal_id, cal_data in calendars.items():
                for busy in cal_data.get('busy', []):
                    busy_times.append({
                        'start': busy.get('start'),
                        'end': busy.get('end')
                    })
            
            return busy_times
            
        except Exception as e:
            logger.error(f"Failed to get busy times: {e}")
            return []

# Global calendar instance
oracle_calendar = OracleCalendar() 