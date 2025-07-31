#!/usr/bin/env python3
"""
Test script to debug calendar sync issues
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "https://adtv-backend-5u8n.onrender.com"
# API_BASE_URL = "http://localhost:8000"  # Uncomment for local testing

# You'll need to provide these values
AUTH_TOKEN = input("Enter your auth token (from localStorage.getItem('token')): ").strip()
CLIENT_ID = input("Enter the client ID: ").strip()

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

print(f"\n{'='*60}")
print("CALENDAR SYNC DEBUG TEST")
print(f"{'='*60}\n")

# 1. Check current calendar events
print("1. Checking current calendar events...")
response = requests.get(
    f"{API_BASE_URL}/clients/{CLIENT_ID}/debug-calendar-events",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Total calendar events: {data['total_events']}")
    print(f"  - Past events: {data['past_events_count']}")
    print(f"  - Future events: {data['future_events_count']}")
    print(f"  - Current UTC time: {data['current_utc_time']}")
    
    if data['future_events_count'] > 0:
        print(f"\n  ✓ Next event: {data['summary']['next_event']['subject']}")
        print(f"    Date: {data['summary']['next_event']['event_time']}")
    else:
        print("\n  ⚠️  No future events found!")
        
    if data['total_events'] > 0:
        print("\n  Recent events:")
        for i, event in enumerate(data['events'][:5]):
            status = "✓ FUTURE" if event['is_future'] else "  PAST"
            print(f"    {status} - {event['subject']} ({event['event_time']})")
else:
    print(f"✗ Error: {response.status_code} - {response.text}")

# 2. Check calendar sync status
print(f"\n{'='*60}")
print("2. Checking calendar sync configuration...")
response = requests.get(
    f"{API_BASE_URL}/clients/{CLIENT_ID}/calendar-sync-status",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Sync email addresses: {', '.join(data['sync_email_addresses']) if data['sync_email_addresses'] else 'None configured'}")
    print(f"✓ Connected calendar sources: {data['connected_calendar_sources']}")
    print(f"✓ Has sync emails: {data['sync_status']['has_sync_emails']}")
    print(f"✓ Has calendar sources: {data['sync_status']['has_calendar_sources']}")
    print(f"✓ Has synced events: {data['sync_status']['has_synced_events']}")
else:
    print(f"✗ Error: {response.status_code} - {response.text}")

# 3. Ask if user wants to force sync
print(f"\n{'='*60}")
force_sync = input("\nDo you want to force a fresh calendar sync? (y/n): ").strip().lower()

if force_sync == 'y':
    print("\n3. Forcing calendar sync...")
    response = requests.post(
        f"{API_BASE_URL}/clients/{CLIENT_ID}/force-calendar-sync",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Sync completed!")
        print(f"  - Old events removed: {data['old_events_removed']}")
        print(f"  - New events synced: {data['new_events_synced']}")
        print(f"  - Future events found: {data['future_events']}")
        
        if data['future_events'] == 0:
            print("\n⚠️  Still no future events found. This could mean:")
            print("  1. The client's email addresses are not attendees on future meetings")
            print("  2. The meetings are on a different calendar")
            print("  3. The meetings don't match the search criteria")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

# 4. Check upcoming meetings endpoint
print(f"\n{'='*60}")
print("4. Checking upcoming meetings endpoint...")
response = requests.get(
    f"{API_BASE_URL}/clients/{CLIENT_ID}/upcoming-meetings",
    headers=headers
)

if response.status_code == 200:
    meetings = response.json()
    print(f"✓ Found {len(meetings)} upcoming meetings")
    
    if meetings:
        for meeting in meetings[:3]:
            print(f"\n  Meeting: {meeting['title']}")
            print(f"  Time: {meeting['startTime']}")
            print(f"  Attendees: {len(meeting['attendees'])}")
else:
    print(f"✗ Error: {response.status_code} - {response.text}")

print(f"\n{'='*60}")
print("DEBUGGING COMPLETE")
print(f"{'='*60}\n") 