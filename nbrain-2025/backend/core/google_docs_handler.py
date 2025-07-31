import os
from typing import Dict, Any, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleDocsHandler:
    def __init__(self):
        """Initialize Google Docs API client"""
        self.creds = None
        self.service = None
        
        # Try to get credentials from environment variable first (containing JSON string)
        creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH')
        
        if creds_json:
            try:
                # Parse JSON credentials from environment variable
                creds_info = json.loads(creds_json)
                self.creds = service_account.Credentials.from_service_account_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/documents', 
                           'https://www.googleapis.com/auth/drive']
                )
                self.service = build('docs', 'v1', credentials=self.creds)
                self.drive_service = build('drive', 'v3', credentials=self.creds)
                logger.info("Google Docs service initialized from environment JSON")
            except Exception as e:
                logger.error(f"Failed to initialize from environment JSON: {e}")
                
        elif creds_path and os.path.exists(creds_path):
            # Fall back to file path method
            self.creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/documents', 
                       'https://www.googleapis.com/auth/drive']
            )
            self.service = build('docs', 'v1', credentials=self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            logger.info("Google Docs service initialized from file path")
        else:
            logger.warning("No Google service account credentials found. Google Docs creation will be disabled.")
    
    def create_agent_spec_doc(self, spec: Dict[str, Any]) -> Dict[str, str]:
        """Create a professionally formatted Google Doc from agent specification"""
        if not self.service:
            return {
                'success': False,
                'error': 'Google Docs service not configured',
                'message': 'Google service account credentials are not set up. Please contact your administrator to configure Google API access.',
                'details': 'The system requires GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_PATH environment variables to be set.'
            }
        
        try:
            # Create the document
            doc_title = f"AI Agent Specification: {spec.get('title', 'Untitled')}"
            document = self.service.documents().create(body={'title': doc_title}).execute()
            doc_id = document.get('documentId')
            
            # Build requests for formatting
            requests = []
            current_index = 1
            
            # Title formatting
            title_text = f"{spec.get('title', 'AI Agent Specification')}\n\n"
            self._add_text(requests, current_index, title_text, 12, True, True)
            current_index += len(title_text)
            
            # Executive Summary
            self._add_heading(requests, current_index, "Executive Summary")
            current_index += 19
            
            summary_text = f"{spec.get('summary', '')}\n\n"
            self._add_text(requests, current_index, summary_text, 10, False)
            current_index += len(summary_text)
            
            # Business Case & ROI
            self._add_heading(requests, current_index, "Business Case & ROI")
            current_index += 21
            
            # Business case content as formatted list
            business_content = self._format_business_case()
            self._add_text(requests, current_index, business_content, 10, False)
            current_index += len(business_content)
            
            # Implementation Steps
            self._add_heading(requests, current_index, "Implementation Steps")
            current_index += 22
            
            steps_content = self._format_steps(spec.get('steps', []))
            self._add_text(requests, current_index, steps_content, 10, False)
            current_index += len(steps_content)
            
            # Technical Stack
            self._add_heading(requests, current_index, "Technical Stack")
            current_index += 17
            
            tech_content = self._format_technical_stack(spec.get('agent_stack', {}))
            self._add_text(requests, current_index, tech_content, 10, False)
            current_index += len(tech_content)
            
            # Client Requirements
            self._add_heading(requests, current_index, "Client Requirements")
            current_index += 21
            
            req_content = self._format_requirements(spec.get('client_requirements', []))
            self._add_text(requests, current_index, req_content, 10, False)
            current_index += len(req_content)
            
            # Security Considerations (if present)
            if spec.get('security_considerations'):
                self._add_heading(requests, current_index, "Security Considerations")
                current_index += 24
                
                sec_content = self._format_security(spec.get('security_considerations', {}))
                self._add_text(requests, current_index, sec_content, 10, False)
                current_index += len(sec_content)
            
            # Future Enhancements (if present)
            if spec.get('future_enhancements') and len(spec.get('future_enhancements', [])) > 0:
                self._add_heading(requests, current_index, "Future Enhancement Opportunities")
                current_index += 34
                
                future_content = self._format_future_enhancements(spec.get('future_enhancements', []))
                self._add_text(requests, current_index, future_content, 10, False)
                current_index += len(future_content)
            
            # Cost Estimate (if present)
            if spec.get('implementation_estimate'):
                self._add_heading(requests, current_index, "Implementation Cost Estimate")
                current_index += 30
                
                cost_content = self._format_cost_estimate(spec.get('implementation_estimate', {}))
                self._add_text(requests, current_index, cost_content, 10, False)
                current_index += len(cost_content)
            
            # Execute all requests
            if requests:
                self.service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            # Make the document publicly accessible
            self.drive_service.permissions().create(
                fileId=doc_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            # Get the document URL
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return {
                'success': True,
                'doc_id': doc_id,
                'doc_url': doc_url,
                'message': 'Google Doc created successfully'
            }
            
        except HttpError as error:
            logger.error(f"An error occurred creating Google Doc: {error}")
            return {
                'success': False,
                'error': str(error),
                'message': 'Failed to create Google Doc'
            } 

    def _add_text(self, requests: List[Dict], index: int, text: str, size: int, bold: bool, center: bool = False):
        """Add text with specific formatting"""
        if not text:
            return
            
        # Insert text
        requests.append({
            'insertText': {
                'location': {'index': index},
                'text': text
            }
        })
        
        # Apply text style
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                'textStyle': {
                    'fontSize': {'magnitude': size, 'unit': 'PT'},
                    'bold': bold,
                    'foregroundColor': {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}
                },
                'fields': 'fontSize,bold,foregroundColor'
            }
        })
        
        # Center if needed
        if center:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                    'paragraphStyle': {'alignment': 'CENTER'},
                    'fields': 'alignment'
                }
            })
    
    def _add_heading(self, requests: List[Dict], index: int, heading: str):
        """Add a heading with standard formatting"""
        heading_text = f"{heading}\n\n"
        self._add_text(requests, index, heading_text, 10, True)
    
    def _format_business_case(self) -> str:
        """Format business case as a structured list"""
        content = "Current State Challenges:\n"
        content += "1. Manual processes consuming valuable human resources\n"
        content += "2. Inconsistent quality and response times\n"
        content += "3. Limited scalability with growing demands\n"
        content += "4. High operational costs and error rates\n\n"
        
        content += "Future State Benefits:\n"
        content += "1. 24/7 automated operations with consistent quality\n"
        content += "2. Instant response times and infinite scalability\n"
        content += "3. 90% reduction in operational costs\n"
        content += "4. Data-driven insights for continuous improvement\n\n"
        
        content += "Key Performance Indicators:\n"
        content += "• Efficiency Gains: 90% reduction in processing time\n"
        content += "• Cost Savings: 85% lower operational costs\n"
        content += "• Quality Improvement: 99% consistency in outputs\n\n"
        
        return content
    
    def _format_steps(self, steps: List[str]) -> str:
        """Format implementation steps as numbered list"""
        content = ""
        for i, step in enumerate(steps, 1):
            content += f"{i}. {step}\n"
        content += "\n"
        return content
    
    def _format_technical_stack(self, stack: Dict[str, Any]) -> str:
        """Format technical stack as structured list"""
        content = ""
        
        # Process each component
        for key, value in stack.items():
            component_name = key.replace('_', ' ').title()
            content += f"\n{component_name}:\n"
            
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    sub_name = sub_key.replace('_', ' ').title()
                    content += f"• {sub_name}: {sub_value or 'To be determined'}\n"
            elif isinstance(value, list):
                for item in value:
                    content += f"• {item}\n"
            else:
                content += f"• {value or 'To be determined'}\n"
        
        content += "\n"
        return content
    
    def _format_requirements(self, requirements: List[str]) -> str:
        """Format requirements as numbered list"""
        content = ""
        for i, req in enumerate(requirements, 1):
            content += f"{i}. {req}\n"
        content += "\n"
        return content
    
    def _format_security(self, security: Dict[str, Any]) -> str:
        """Format security considerations"""
        content = ""
        
        for category, details in security.items():
            cat_name = category.replace('_', ' ').title()
            content += f"\n{cat_name}:\n"
            
            if isinstance(details, dict):
                for key, value in details.items():
                    key_name = key.replace('_', ' ').title()
                    content += f"• {key_name}: {value or 'To be determined'}\n"
            else:
                content += f"• {details or 'To be determined'}\n"
        
        content += "\n"
        return content
    
    def _format_future_enhancements(self, enhancements: List[Any]) -> str:
        """Format future enhancements"""
        content = ""
        
        for i, enhancement in enumerate(enhancements, 1):
            if isinstance(enhancement, dict):
                content += f"\n{i}. {enhancement.get('enhancement', 'Enhancement')}\n"
                content += f"   Description: {enhancement.get('description', 'To be determined')}\n"
                if enhancement.get('impact'):
                    content += f"   Business Impact: {enhancement.get('impact')}\n"
                if enhancement.get('implementation_effort'):
                    content += f"   Implementation Effort: {enhancement.get('implementation_effort')}\n"
            else:
                content += f"{i}. {enhancement}\n"
        
        content += "\n"
        return content
    
    def _format_cost_estimate(self, estimate: Dict[str, Any]) -> str:
        """Format cost estimate"""
        content = ""
        
        if 'traditional_approach' in estimate:
            trad = estimate['traditional_approach']
            content += "Traditional Development Approach:\n"
            content += f"• Total Hours: {trad.get('hours', 'N/A')}\n"
            content += f"• Total Cost: {trad.get('total_cost', 'N/A')}\n\n"
        
        if 'ai_powered_approach' in estimate:
            ai = estimate['ai_powered_approach']
            content += "nBrain AI-Powered Approach:\n"
            content += f"• Total Hours: {ai.get('hours', 'N/A')}\n"
            content += f"• Total Cost: {ai.get('total_cost', 'N/A')}\n"
            content += f"• Cost Savings: {ai.get('cost_savings', '90% reduction')}\n\n"
        
        content += "ROI Summary:\n"
        content += "• Immediate cost savings of 90% compared to traditional development\n"
        content += "• Faster time to market with AI-accelerated development\n"
        content += "• Ongoing operational efficiency improvements\n\n"
        
        return content

    def create_content_doc(self, doc_data: Dict[str, Any]) -> Dict[str, str]:
        """Create a Google Doc with general content (blog posts, meeting notes, etc.)"""
        if not self.service:
            raise Exception("Google Docs service not initialized. Please configure Google credentials.")
        
        try:
            # Create the document
            doc_title = doc_data.get('title', 'Untitled Document')
            document = self.service.documents().create(body={'title': doc_title}).execute()
            doc_id = document.get('documentId')
            
            # Build requests for formatting
            requests = []
            current_index = 1
            
            # Title formatting
            title_text = f"{doc_title}\n\n"
            self._add_text(requests, current_index, title_text, 14, True, True)
            current_index += len(title_text)
            
            # Add metadata if available
            if doc_data.get('content_type') or doc_data.get('client_name'):
                metadata_text = ""
                if doc_data.get('content_type'):
                    metadata_text += f"Document Type: {doc_data['content_type']}\n"
                if doc_data.get('client_name'):
                    metadata_text += f"Client: {doc_data['client_name']}\n"
                if doc_data.get('created_by'):
                    metadata_text += f"Created by: {doc_data['created_by']}\n"
                metadata_text += f"Date: {datetime.utcnow().strftime('%B %d, %Y')}\n\n"
                
                self._add_text(requests, current_index, metadata_text, 9, False)
                current_index += len(metadata_text)
            
            # Add horizontal line
            self._add_text(requests, current_index, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", 10, False)
            current_index += 52
            
            # Content
            content = doc_data.get('content', '')
            
            # Process content to handle markdown-style formatting
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    # Check if it's a heading (starts with #)
                    if line.startswith('# '):
                        heading_text = line[2:] + '\n\n'
                        self._add_text(requests, current_index, heading_text, 12, True)
                        current_index += len(heading_text)
                    elif line.startswith('## '):
                        heading_text = line[3:] + '\n\n'
                        self._add_text(requests, current_index, heading_text, 11, True)
                        current_index += len(heading_text)
                    elif line.startswith('### '):
                        heading_text = line[4:] + '\n\n'
                        self._add_text(requests, current_index, heading_text, 10, True)
                        current_index += len(heading_text)
                    elif line.startswith('- ') or line.startswith('• '):
                        # Bullet point
                        bullet_text = '• ' + line[2:] + '\n'
                        self._add_text(requests, current_index, bullet_text, 10, False)
                        current_index += len(bullet_text)
                    elif line.strip().startswith(tuple(str(i) + '.' for i in range(1, 10))):
                        # Numbered list
                        list_text = line + '\n'
                        self._add_text(requests, current_index, list_text, 10, False)
                        current_index += len(list_text)
                    else:
                        # Regular paragraph
                        para_text = line + '\n'
                        self._add_text(requests, current_index, para_text, 10, False)
                        current_index += len(para_text)
                else:
                    # Empty line
                    self._add_text(requests, current_index, '\n', 10, False)
                    current_index += 1
            
            # Execute all requests
            if requests:
                self.service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            # Make the document publicly accessible
            self.drive_service.permissions().create(
                fileId=doc_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            # Get the document URL
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return {
                'success': True,
                'doc_id': doc_id,
                'doc_url': doc_url,
                'message': 'Google Doc created successfully'
            }
            
        except HttpError as error:
            logger.error(f"An error occurred creating Google Doc: {error}")
            return {
                'success': False,
                'error': str(error),
                'message': 'Failed to create Google Doc'
            }

# Singleton instance
google_docs_handler = GoogleDocsHandler() 