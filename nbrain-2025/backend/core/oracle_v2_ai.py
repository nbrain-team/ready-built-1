"""
Oracle V2 AI Module - Advanced action item extraction using LLMs
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import uuid

logger = logging.getLogger(__name__)

class OracleAI:
    """AI-powered features for Oracle V2"""
    
    def __init__(self):
        self.llm_handler = None
        try:
            from .llm_handler import get_llm_handler
            self.llm_handler = get_llm_handler()
            logger.info("LLM handler initialized for Oracle AI")
        except Exception as e:
            logger.warning(f"LLM not available, using pattern-based extraction: {e}")
    
    def extract_action_items_advanced(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract action items using AI with fallback to patterns"""
        
        # Always try pattern extraction first to ensure we get some results
        pattern_items = self._extract_with_patterns(email_data)
        
        if not self.llm_handler:
            return pattern_items
        
        try:
            prompt = f"""
            Analyze this email and extract SPECIFIC action items that require a response or action.
            Be very selective - only include items that are clearly actionable tasks.
            
            Email Details:
            From: {email_data.get('from', '')}
            To: {email_data.get('to', '')}
            Subject: {email_data.get('subject', '')}
            Date: {email_data.get('date', '')}
            Body: {email_data.get('body', '')[:2000]}
            
            For each action item, determine:
            1. A clear, specific task title (max 100 chars)
            2. Priority: high (urgent/deadline), medium (important), low (nice to have)
            3. Due date if mentioned (format: YYYY-MM-DD)
            4. Category: email_reply, document_request, meeting_schedule, payment, task, other
            5. Relevant context or details
            
            Rules:
            - Only include items that require action from the email recipient
            - Be specific about what needs to be done
            - If no clear action items exist, return empty list
            - Don't include FYI items or general information
            
            Return as JSON array with this structure:
            [
                {
                    "title": "Clear action title",
                    "priority": "high|medium|low",
                    "due_date": "YYYY-MM-DD or null",
                    "category": "category_name",
                    "context": "Relevant details",
                    "source": "email"
                }
            ]
            """
            
            response = self.llm_handler.generate(prompt)
            items = self._parse_llm_response(response)
            
            # Add email metadata
            for item in items:
                item['email_id'] = email_data.get('id')
                item['email_subject'] = email_data.get('subject')
                item['email_from'] = email_data.get('from')
                
            return items
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return pattern_items
    
    async def extract_action_items_from_email(self, subject: str, content: str, from_email: str) -> List[Dict[str, Any]]:
        """Extract action items from email - async wrapper for compatibility"""
        email_data = {
            'subject': subject,
            'body': content,
            'from': from_email,
            'to': '',  # Not provided in this interface
            'date': datetime.now().isoformat()
        }
        return self.extract_action_items_advanced(email_data)
    
    def _extract_with_patterns(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback pattern-based extraction"""
        action_items = []
        content = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        
        # Skip if content is too short
        if len(content.strip()) < 20:
            return []
        
        # Enhanced patterns - more specific and actionable
        patterns = [
            # Direct requests
            (r'(?:please|could you|can you|would you|will you)\s+([^.!?\n]{15,100})', 'email_reply', 'medium'),
            # Document/info requests  
            (r'(?:send|provide|share|forward|email)\s+(?:me|us)?\s*(?:the)?\s+([^.!?\n]{10,80})', 'document_request', 'high'),
            # Meeting requests
            (r'(?:schedule|set up|arrange|book)\s+(?:a|an)?\s*(?:meeting|call|discussion)\s+([^.!?\n]{0,50})', 'meeting_schedule', 'high'),
            # Payment related
            (r'(?:pay|payment|invoice|bill|charge|fee)\s+([^.!?\n]{10,80})', 'payment', 'high'),
            # Deadlines
            (r'(?:by|before|until|deadline|due)\s+([^.!?\n]{10,80})', 'task', 'high'),
            # Action verbs at start of sentence
            (r'^(?:Review|Approve|Sign|Complete|Submit|Prepare)\s+([^.!?\n]{10,80})', 'task', 'medium'),
            # Questions that need answers
            (r'(?:what|when|where|how|why|which)\s+(?:is|are|will|would|should)\s+([^?]{10,80})\?', 'email_reply', 'medium'),
        ]
        
        seen_titles = set()
        
        for pattern, category, default_priority in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches[:2]:  # Max 2 per pattern
                title = match.strip()
                
                # Clean up title
                title = re.sub(r'\s+', ' ', title)
                title = title[:100]
                
                # Skip if too short or duplicate
                if len(title) < 10 or title.lower() in seen_titles:
                    continue
                
                # Skip common non-actionable phrases
                skip_phrases = ['let me know', 'feel free', 'if you have', 'any questions']
                if any(phrase in title.lower() for phrase in skip_phrases):
                    continue
                
                seen_titles.add(title.lower())
                
                # Detect priority
                priority = default_priority
                if any(word in content.lower() for word in ['urgent', 'asap', 'immediately', 'critical']):
                    priority = 'high'
                elif any(word in content.lower() for word in ['when you can', 'no rush', 'whenever']):
                    priority = 'low'
                
                # Generate a cleaner title
                clean_title = self._clean_action_title(title, category)
                
                action_items.append({
                    'id': str(uuid.uuid4()),  # Always include ID
                    'title': clean_title,
                    'priority': priority,
                    'due_date': self._extract_date(content),
                    'category': category,
                    'context': f"From {email_data.get('from', 'Unknown')}",
                    'source': email_data.get('from', 'Email'),  # Always include source
                    'source_email_id': email_data.get('id', ''),
                    'from_email': email_data.get('from', ''),
                    'to_email': email_data.get('to', ''),
                    'subject': email_data.get('subject', ''),
                    'thread_id': email_data.get('thread_id', email_data.get('id', '')),
                    'emailContent': email_data.get('body', ''),  # Include full email content
                    'body': email_data.get('body', ''),  # Also as body for compatibility
                    'date': email_data.get('date', '')
                })
        
        return action_items[:5]  # Max 5 items per email
    
    def _clean_action_title(self, title: str, category: str) -> str:
        """Clean up action item title to be more actionable"""
        # Remove common filler words at the start
        title = re.sub(r'^(?:please|could you|can you|would you|will you)\s+', '', title, flags=re.IGNORECASE)
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Add action verb if missing
        action_verbs = {
            'email_reply': 'Reply to',
            'document_request': 'Send',
            'meeting_schedule': 'Schedule',
            'payment': 'Process',
            'task': 'Complete'
        }
        
        # Check if title already starts with an action verb
        has_action_verb = any(title.lower().startswith(verb.lower()) for verb in 
                             ['reply', 'send', 'schedule', 'process', 'complete', 'review', 'approve', 'submit'])
        
        if not has_action_verb and category in action_verbs:
            title = f"{action_verbs[category]} {title.lower()}"
        
        return title
    
    def _parse_due_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse due date string to standard format"""
        if not date_str:
            return None
            
        try:
            # Try parsing common formats
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return None
    
    def _extract_date(self, content: str) -> Optional[str]:
        """Extract date from content"""
        # Simple date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return self._parse_due_date(match.group(1))
        
        # Relative dates
        today = datetime.now()
        relative_patterns = [
            (r'tomorrow', today + timedelta(days=1)),
            (r'next week', today + timedelta(days=7)),
            (r'next month', today + timedelta(days=30)),
            (r'end of week', today + timedelta(days=(4 - today.weekday()))),
        ]
        
        for pattern, date in relative_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return date.strftime('%Y-%m-%d')
        
        return None
    
    def categorize_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize emails by type and importance"""
        categories = {
            'urgent': [],
            'action_required': [],
            'informational': [],
            'automated': []
        }
        
        for email in emails:
            from_addr = email.get('from', '').lower()
            subject = email.get('subject', '').lower()
            body = email.get('body', '').lower()
            
            # Check if automated
            if any(x in from_addr for x in ['no-reply', 'noreply', 'notification', 'automated']):
                categories['automated'].append(email)
            # Check if urgent
            elif any(x in subject + body for x in ['urgent', 'asap', 'critical', 'emergency']):
                categories['urgent'].append(email)
            # Check if action required
            elif any(x in body for x in ['please', 'could you', 'need', 'require', 'request']):
                categories['action_required'].append(email)
            else:
                categories['informational'].append(email)
        
        return categories
    
    def generate_email_summary(self, email_data: Dict[str, Any]) -> str:
        """Generate a concise summary of an email"""
        if self.llm_handler:
            try:
                prompt = f"""
                Summarize this email in 1-2 sentences:
                From: {email_data.get('from', '')}
                Subject: {email_data.get('subject', '')}
                Body: {email_data.get('body', '')[:500]}
                
                Focus on: What is being asked/communicated and why it matters.
                """
                
                summary = self.llm_handler.generate_text(prompt, temperature=0.3, max_tokens=100)
                return summary.strip()
            except Exception as e:
                logger.error(f"Summary generation failed: {e}")
        
        # Fallback to simple extraction
        subject = email_data.get('subject', 'No subject')
        body_preview = email_data.get('body', '')[:100]
        return f"{subject} - {body_preview}..."
    
    def suggest_response(self, email_data: Dict[str, Any], action_item: Dict[str, Any]) -> str:
        """Suggest a response for an action item"""
        if self.llm_handler:
            try:
                prompt = f"""
                Suggest a brief, professional response for this action item:
                
                Action: {action_item.get('title', '')}
                Context: {action_item.get('context', '')}
                Original email subject: {email_data.get('subject', '')}
                
                Provide a 2-3 sentence response template the user can customize.
                """
                
                response = self.llm_handler.generate_text(prompt, temperature=0.7, max_tokens=150)
                return response.strip()
            except Exception as e:
                logger.error(f"Response suggestion failed: {e}")
        
        # Fallback templates
        category = action_item.get('category', 'other')
        templates = {
            'document_request': "I'll send you the requested document shortly. Let me gather the information and I'll have it to you by [DATE].",
            'meeting_schedule': "I'm available for a meeting. Here are some time slots that work for me: [TIMES]. Please let me know what works best for you.",
            'payment': "I've received your payment request and will process it soon. You should receive confirmation within [TIMEFRAME].",
            'email_reply': "Thank you for your email. I'll review this and get back to you with a detailed response by [DATE].",
            'task': "I'll take care of this task. I'll keep you updated on the progress and aim to complete it by [DATE].",
            'other': "Thank you for bringing this to my attention. I'll look into it and follow up with you soon."
        }
        
        return templates.get(category, templates['other'])

# Global AI instance
oracle_ai = OracleAI() 