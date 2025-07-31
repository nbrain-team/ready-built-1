"""
Debug Gmail labels - find out why labeled emails aren't showing
"""
import os
os.environ['REDIS_URL'] = os.environ.get('REDIS_URL', '')

from core.oracle_v2_storage import oracle_storage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

USER_ID = '2908bb63-ebad-48d0-997d-5ed153aef0c2'

# Get credentials
creds = Credentials(**oracle_storage.get_user_credentials(USER_ID))
service = build('gmail', 'v1', credentials=creds)

print("=== GMAIL LABEL DEBUGGING ===\n")

# 1. Get the nBrain Priority label details
labels = service.users().labels().list(userId='me').execute().get('labels', [])
nbrain_label = next((l for l in labels if 'nbrain' in l['name'].lower()), None)

if nbrain_label:
    print(f"Found label: {nbrain_label['name']}")
    print(f"Label ID: {nbrain_label['id']}")
    print(f"Label Type: {nbrain_label.get('type', 'user')}")
    
    # Get full label details
    label_detail = service.users().labels().get(userId='me', id=nbrain_label['id']).execute()
    print(f"Messages Total: {label_detail.get('messagesTotal', 0)}")
    print(f"Messages Unread: {label_detail.get('messagesUnread', 0)}")
    print(f"Threads Total: {label_detail.get('threadsTotal', 0)}")
else:
    print("No nBrain label found!")

print("\n=== TESTING DIFFERENT QUERY FORMATS ===")

# Test various query formats
queries = [
    f"label:{nbrain_label['id']}" if nbrain_label else None,
    f'label:"{nbrain_label["name"]}"' if nbrain_label else None,
    f"label:nBrain-Priority",
    f'label:"nBrain Priority"',
    f"in:nBrain-Priority",
    f'in:"nBrain Priority"',
    "has:userlabels",  # Any email with user labels
]

for query in queries:
    if query:
        try:
            print(f"\nQuery: {query}")
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5
            ).execute()
            count = len(results.get('messages', []))
            print(f"  Found: {count} emails")
            
            # If found, check first email
            if count > 0:
                msg_id = results['messages'][0]['id']
                msg = service.users().messages().get(userId='me', id=msg_id).execute()
                print(f"  First email labels: {msg.get('labelIds', [])}")
                
        except Exception as e:
            print(f"  Error: {e}")

print("\n=== CHECKING A SPECIFIC EMAIL ===")
# Get any recent email and check its labels
recent = service.users().messages().list(userId='me', maxResults=1).execute()
if recent.get('messages'):
    msg_id = recent['messages'][0]['id']
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    headers = msg['payload'].get('headers', [])
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    
    print(f"Random recent email: {subject[:60]}")
    print(f"Label IDs on this email: {msg.get('labelIds', [])}")
    
    # Get label names
    email_label_names = []
    for label_id in msg.get('labelIds', []):
        label_name = next((l['name'] for l in labels if l['id'] == label_id), label_id)
        email_label_names.append(label_name)
    print(f"Label names: {email_label_names}")

print("\n=== MANUAL LABEL CHECK ===")
print("To manually check in Gmail:")
print("1. Open Gmail")
print("2. Click on 'nBrain Priority' label in the left sidebar")
print("3. You should see all emails with this label")
print("4. Check if the label shows a count next to it")
print("\nIf you see emails there but not in the API, there might be a sync issue.") 