#!/usr/bin/env python3
"""
Simple Gmail debug script for Render shell
Run with: python simple_gmail_debug.py
"""
import os
import sys

# Set environment variable for file storage
os.environ['REDIS_URL'] = os.environ.get('REDIS_URL', '')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.oracle_v2_storage import oracle_storage
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    USER_ID = '2908bb63-ebad-48d0-997d-5ed153aef0c2'
    
    print("="*60)
    print("Gmail Debug Script")
    print("="*60)
    
    # Get credentials
    creds_dict = oracle_storage.get_user_credentials(USER_ID)
    if not creds_dict:
        print("ERROR: No credentials found!")
        sys.exit(1)
    
    print(f"✓ Credentials found with keys: {list(creds_dict.keys())}")
    
    # Build service
    try:
        creds = Credentials(**creds_dict)
        service = build('gmail', 'v1', credentials=creds)
        print("✓ Gmail service built successfully")
    except Exception as e:
        print(f"✗ Failed to build service: {type(e).__name__}: {e}")
        sys.exit(1)
    
    # List all labels
    try:
        labels_response = service.users().labels().list(userId='me').execute()
        labels = labels_response.get('labels', [])
        print(f"\n✓ Found {len(labels)} labels:")
        
        # Look for nBrain labels
        nbrain_labels = []
        for label in labels:
            if 'nBrain' in label['name'] or 'nbrain' in label['name'].lower():
                nbrain_labels.append(label)
                print(f"  - {label['name']} (ID: {label['id']})")
        
        if not nbrain_labels:
            print("\n⚠️  No 'nBrain' labels found!")
            print("\nAll labels:")
            for label in labels[:20]:  # Show first 20
                print(f"  - {label['name']} (ID: {label['id']})")
            if len(labels) > 20:
                print(f"  ... and {len(labels) - 20} more")
    
    except Exception as e:
        print(f"\n✗ Failed to list labels: {type(e).__name__}: {e}")
        sys.exit(1)
    
    # Test specific label queries
    print("\n" + "="*60)
    print("Testing label queries:")
    print("="*60)
    
    test_queries = [
        'label:nBrain+Priority',
        'label:"nBrain Priority"',
        'label:nBrain-Priority',
        'in:nBrain+Priority',
        'in:"nBrain Priority"'
    ]
    
    for query in test_queries:
        try:
            result = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=1
            ).execute()
            count = result.get('resultSizeEstimate', 0)
            print(f"  {query:<30} → {count} messages")
        except Exception as e:
            print(f"  {query:<30} → ERROR: {e}")
    
    # If we found nBrain labels, test with their IDs
    if nbrain_labels:
        print("\nTesting with label IDs:")
        for label in nbrain_labels:
            query = f'label:{label["id"]}'
            try:
                result = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=1
                ).execute()
                count = result.get('resultSizeEstimate', 0)
                print(f"  {label['name']:<30} → {count} messages")
            except Exception as e:
                print(f"  {label['name']:<30} → ERROR: {e}")
    
    print("\n" + "="*60)
    print("Debug complete!")
    print("="*60)
    
except Exception as e:
    print(f"\nFATAL ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc() 