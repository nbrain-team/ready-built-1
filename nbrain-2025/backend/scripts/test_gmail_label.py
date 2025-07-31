"""
Test Gmail label queries directly
Run this in Render shell to debug label issues
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

# Get user ID from command line or use default
USER_ID = sys.argv[1] if len(sys.argv) > 1 else "2908bb63-ebad-48d0-997d-5ed153aef0c2"

def test_gmail_labels():
    """Test different Gmail label queries"""
    
    # Import Oracle storage
    from core.oracle_v2_storage import oracle_storage
    
    # Get credentials
    credentials = oracle_storage.get_user_credentials(USER_ID)
    if not credentials:
        print(f"No credentials found for user {USER_ID}")
        return
    
    print(f"Found credentials for user {USER_ID}")
    
    # Build Gmail service
    creds = Credentials(**credentials)
    service = build('gmail', 'v1', credentials=creds)
    
    # First, list all labels
    print("\n=== ALL GMAIL LABELS ===")
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        print(f"Total labels: {len(labels)}")
        for label in sorted(labels, key=lambda x: x['name']):
            print(f"  - {label['name']} (ID: {label['id']})")
            if 'nbrain' in label['name'].lower():
                print(f"    ^^^ FOUND nBrain LABEL! ^^^")
    except Exception as e:
        print(f"Error listing labels: {e}")
    
    # Test different query formats
    print("\n=== TESTING QUERIES ===")
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")
    
    queries_to_test = [
        f'after:{seven_days_ago} label:nBrain+Priority',
        f'after:{seven_days_ago} label:"nBrain+Priority"',
        f'after:{seven_days_ago} label:nBrain-Priority',
        f'after:{seven_days_ago} label:"nBrain Priority"',
        f'after:{seven_days_ago} in:nBrain+Priority',
        f'after:{seven_days_ago} in:"nBrain Priority"',
        f'after:{seven_days_ago}',  # All emails from last 7 days
    ]
    
    for query in queries_to_test:
        print(f"\nTrying query: {query}")
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            print(f"  Found {len(messages)} emails")
            
            # Get details of first email if found
            if messages:
                msg = service.users().messages().get(
                    userId='me',
                    id=messages[0]['id']
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                # Check labels on this email
                email_labels = msg.get('labelIds', [])
                print(f"  First email: {subject[:50]}...")
                print(f"  From: {from_email}")
                print(f"  Labels on email: {email_labels}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n=== CHECKING SPECIFIC LABEL ID ===")
    # Try to find nBrain label by ID
    nbrain_labels = [l for l in labels if 'nbrain' in l['name'].lower()]
    if nbrain_labels:
        for nb_label in nbrain_labels:
            label_id = nb_label['id']
            label_name = nb_label['name']
            print(f"\nTrying with label ID: {label_id} (Name: {label_name})")
            
            try:
                # Query using label ID
                query = f'after:{seven_days_ago} label:{label_id}'
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=10
                ).execute()
                
                messages = results.get('messages', [])
                print(f"  Found {len(messages)} emails with label ID")
                
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    test_gmail_labels() 