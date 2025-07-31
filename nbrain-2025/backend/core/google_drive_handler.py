"""
Google Drive Handler for Client Portal
Manages client folders and document synchronization
"""

import os
import json
import logging
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleDriveHandler:
    def __init__(self):
        """Initialize Google Drive API client"""
        self.service = None
        self.master_folder_id = "1LhDwdmi3LYT34aZ-3OlHXA-ytWGDJFle"  # Your master folder ID
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the Google Drive service with credentials"""
        try:
            # Try to get credentials from environment variable first (containing JSON string)
            creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH', 'google-credentials.json')
            
            if creds_json:
                try:
                    # Parse JSON credentials from environment variable
                    creds_info = json.loads(creds_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_info,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                    self.service = build('drive', 'v3', credentials=credentials)
                    logger.info("Google Drive service initialized from environment JSON")
                except Exception as e:
                    logger.error(f"Failed to initialize from environment JSON: {e}")
                    
            elif os.path.exists(creds_path):
                # Fall back to file path method
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                logger.info("Google Drive service initialized from file path")
            else:
                logger.error("No Google service account credentials found. Google Drive integration will be disabled.")
        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
    
    def create_client_folder(self, client_name: str) -> Optional[str]:
        """Create a folder for a client in the master folder"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None
        
        try:
            # Check if folder already exists
            existing = self._find_client_folder(client_name)
            if existing:
                logger.info(f"Folder already exists for client: {client_name}")
                return existing['id']
            
            # Create the folder
            file_metadata = {
                'name': client_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.master_folder_id]
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            logger.info(f"Created folder for client {client_name}: {folder.get('id')}")
            return folder.get('id')
            
        except HttpError as e:
            logger.error(f"Error creating folder for {client_name}: {e}")
            return None
    
    def _find_client_folder(self, client_name: str) -> Optional[Dict]:
        """Find a client's folder by name"""
        try:
            query = f"name='{client_name}' and '{self.master_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            return files[0] if files else None
            
        except HttpError as e:
            logger.error(f"Error finding folder for {client_name}: {e}")
            return None
    
    def list_client_documents(self, client_name: str) -> List[Dict]:
        """List all documents in a client's folder"""
        if not self.service:
            logger.error("Google Drive service not initialized")
            return []
        
        try:
            # First find the client folder
            client_folder = self._find_client_folder(client_name)
            if not client_folder:
                logger.info(f"No folder found for client: {client_name}")
                return []
            
            # List files in the folder
            query = f"'{client_folder['id']}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            # Format the results
            documents = []
            for file in files:
                documents.append({
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'type': self._get_file_type(file.get('mimeType')),
                    'mimeType': file.get('mimeType'),
                    'webViewLink': file.get('webViewLink'),
                    'modifiedTime': file.get('modifiedTime'),
                    'size': file.get('size', 0)
                })
            
            return documents
            
        except HttpError as e:
            logger.error(f"Error listing documents for {client_name}: {e}")
            return []
    
    def _get_file_type(self, mime_type: str) -> str:
        """Convert MIME type to friendly file type"""
        type_mapping = {
            'application/vnd.google-apps.document': 'Google Doc',
            'application/vnd.google-apps.spreadsheet': 'Google Sheet',
            'application/vnd.google-apps.presentation': 'Google Slides',
            'application/pdf': 'PDF',
            'image/': 'Image',
            'video/': 'Video',
            'application/vnd.openxmlformats-officedocument': 'Office Document'
        }
        
        for key, value in type_mapping.items():
            if mime_type.startswith(key):
                return value
        
        return 'File'
    
    def get_folder_link(self, client_name: str) -> Optional[str]:
        """Get the web link to a client's folder"""
        if not self.service:
            return None
        
        folder = self._find_client_folder(client_name)
        return folder.get('webViewLink') if folder else None

# Create a singleton instance
google_drive_handler = GoogleDriveHandler() 