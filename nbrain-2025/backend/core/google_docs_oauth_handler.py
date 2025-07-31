import os
from typing import Dict, Any, List
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleDocsOAuthHandler:
    """Alternative Google Docs handler using OAuth2 (user authentication)"""
    
    CLIENT_SECRETS = {
        "web": {
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')]
        }
    }
    
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def get_auth_url(self) -> str:
        """Get the OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            self.CLIENT_SECRETS,
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.CLIENT_SECRETS['web']['redirect_uris'][0]
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return auth_url
    
    def handle_callback(self, code: str) -> Dict[str, Any]:
        """Handle the OAuth2 callback and get credentials"""
        flow = Flow.from_client_config(
            self.CLIENT_SECRETS,
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.CLIENT_SECRETS['web']['redirect_uris'][0]
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save credentials for later use
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        return creds_data
    
    def create_agent_spec_doc_with_creds(self, spec: Dict[str, Any], creds_data: Dict[str, Any]) -> Dict[str, str]:
        """Create a Google Doc using user credentials"""
        try:
            # Recreate credentials from saved data
            creds = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )
            
            # Refresh token if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            # Build services
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Create the document
            doc_title = f"AI Agent Specification: {spec.get('title', 'Untitled')}"
            document = docs_service.documents().create(body={'title': doc_title}).execute()
            doc_id = document.get('documentId')
            
            # Format content (same as service account version)
            content = self._format_document_content(spec)
            
            # Update document with content
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': content}
            ).execute()
            
            # Get the document URL
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return {
                'success': True,
                'doc_id': doc_id,
                'doc_url': doc_url,
                'message': 'Google Doc created successfully in your account'
            }
            
        except HttpError as error:
            logger.error(f"An error occurred creating Google Doc: {error}")
            return {
                'success': False,
                'error': str(error),
                'message': 'Failed to create Google Doc'
            }
    
    def _format_document_content(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format the spec into Google Docs API requests"""
        requests = []
        
        # Add title
        requests.extend([
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': f"{spec.get('title', 'AI Agent Specification')}\n\n"
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(spec.get('title', '')) + 1},
                    'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        # Add remaining content sections
        # (Similar to service account version - can reuse the formatting logic)
        
        return requests

# Export singleton
google_docs_oauth_handler = GoogleDocsOAuthHandler() 