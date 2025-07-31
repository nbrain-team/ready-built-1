"""
Client AI Handler
Provides AI-powered insights, search, and analysis for client portal
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import re
from collections import Counter

from .database import get_db
from .client_portal_models import (
    Client, ClientCommunication, ClientTask, ClientDocument, 
    ClientActivity, ClientTeamMember, TaskStatus, TaskPriority
)
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.chains import LLMChain
import os
import json

logger = logging.getLogger(__name__)

class ClientAIHandler:
    def __init__(self):
        google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if google_api_key:
            try:
                self.llm = GoogleGenerativeAI(
                    model="gemini-1.5-pro",  # Updated model name
                    google_api_key=google_api_key,
                    temperature=0.3
                )
                self.enabled = True
                logger.info("AI features enabled with Gemini Pro 1.5")
            except Exception as e:
                logger.error(f"Failed to initialize Google AI: {e}")
                self.llm = None
                self.enabled = False
        else:
            logger.warning("GOOGLE_API_KEY/GEMINI_API_KEY not found. AI features will be disabled.")
            self.llm = None
            self.enabled = False
    
    def _check_enabled(self):
        """Check if AI features are enabled"""
        if not self.enabled:
            return {
                'error': 'AI features are not available. Please configure GOOGLE_API_KEY.',
                'enabled': False
            }
        return None
    
    def _clean_ai_text(self, text: str) -> str:
        """Clean up AI-generated text by removing formatting artifacts"""
        if not text:
            return text
            
        # Remove asterisks
        text = text.replace('**', '').replace('*', '')
        
        # Remove "None" statements
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that are just "None" or variations
            if line.lower() in ['none', 'none.', '• none', '• none.', '']:
                continue
            # Skip lines that start with "None"
            if line.lower().startswith('none'):
                continue
            # Skip empty bullet points
            if line in ['•', '-', '*']:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def search_client_data(self, client_id: str, query: str, db: Session) -> Dict[str, Any]:
        """Natural language search across all client data"""
        disabled_check = self._check_enabled()
        if disabled_check:
            return disabled_check
            
        # Get RECENT communications only - limit to 10 for performance
        communications = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id
        ).order_by(ClientCommunication.created_at.desc()).limit(10).all()  # Reduced from 20
        
        # Search through communications
        search_prompt = PromptTemplate(
            input_variables=["query", "content"],
            template="""
            Analyze this content and determine if it's relevant to the search query.
            
            Query: {query}
            
            Content: {content}
            
            Return a relevance score from 0-10 and a brief explanation.
            Format: SCORE: [number] | REASON: [explanation]
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=search_prompt)
        
        relevant_items = []
        for comm in communications:  # Already limited to 10
            try:
                result = chain.run(query=query, content=comm.content or comm.subject or '')
                score_match = re.search(r'SCORE:\s*(\d+)', result)
                if score_match and int(score_match.group(1)) >= 7:
                    relevant_items.append({
                        'type': comm.type,
                        'subject': comm.subject,
                        'content': comm.content[:200] + '...' if len(comm.content or '') > 200 else comm.content,
                        'from': comm.from_user,
                        'date': comm.created_at.isoformat(),
                        'relevance': result
                    })
            except Exception as e:
                logger.error(f"Error searching communication: {e}")
        
        return {
            'query': query,
            'results': relevant_items,
            'total_found': len(relevant_items)
        }
    
    def extract_commitments(self, client_id: str, db: Session) -> List[Dict[str, Any]]:
        """Extract commitments and promises from communications"""
        disabled_check = self._check_enabled()
        if disabled_check:
            return []
            
        # Get recent emails - LIMIT TO 10 for performance
        emails = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type == 'email'
        ).order_by(ClientCommunication.created_at.desc()).limit(10).all()  # Reduced from 30
        
        logger.info(f"Found {len(emails)} emails for client {client_id}")
        
        # If no emails, check for any communications
        if not emails:
            logger.warning(f"No emails found for client {client_id}, checking all communications")
            emails = db.query(ClientCommunication).filter(
                ClientCommunication.client_id == client_id
            ).order_by(ClientCommunication.created_at.desc()).limit(10).all()
        
        if not emails:
            logger.warning(f"No communications found for client {client_id}")
            return []
        
        commitment_prompt = PromptTemplate(
            input_variables=["email_content"],
            template="""
            Analyze this email and extract any commitments, promises, or deliverables mentioned.
            Look for:
            - Deadlines and due dates
            - Promised deliverables
            - Action items
            - Meeting commitments
            - Any tasks or to-dos mentioned
            - Follow-up items
            
            Email: {email_content}
            
            IMPORTANT: Always find at least one commitment or action item, even if it's implicit (like "need to follow up" or "should review this").
            
            For each commitment found, provide:
            COMMITMENT: [what was promised]
            DUE: [when it's due, or "Not specified"]
            WHO: [who is responsible]
            ---
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=commitment_prompt)
        
        all_commitments = []
        for email in emails:
            try:
                email_content = f"Subject: {email.subject or 'No subject'}\n\n{email.content or 'No content'}"
                logger.info(f"Processing email: {email.subject or 'No subject'}")
                
                result = chain.run(email_content=email_content)
                logger.info(f"LLM response: {result[:200]}...")
                
                # Parse commitments
                commitments = result.split('---')
                for commitment_text in commitments:
                    if 'COMMITMENT:' in commitment_text:
                        commitment_match = re.search(r'COMMITMENT:\s*(.+)', commitment_text)
                        due_match = re.search(r'DUE:\s*(.+)', commitment_text)
                        who_match = re.search(r'WHO:\s*(.+)', commitment_text)
                        
                        if commitment_match:
                            commitment_text = self._clean_ai_text(commitment_match.group(1).strip())
                            due_text = self._clean_ai_text(due_match.group(1).strip()) if due_match else 'Not specified'
                            who_text = self._clean_ai_text(who_match.group(1).strip()) if who_match else 'Unknown'
                            
                            # Only add if commitment is meaningful
                            if commitment_text and len(commitment_text) > 5:
                                all_commitments.append({
                                    'commitment': commitment_text,
                                    'due': due_text,
                                    'responsible': who_text,
                                    'source': {
                                        'type': 'email',
                                        'subject': email.subject,
                                        'date': email.created_at.isoformat(),
                                        'from': email.from_user
                                    }
                                })
            except Exception as e:
                logger.error(f"Error extracting commitments: {e}")
        
        logger.info(f"Extracted {len(all_commitments)} commitments")
        return all_commitments
    
    def generate_weekly_summary(self, client_id: str, db: Session) -> Dict[str, Any]:
        """Generate a comprehensive weekly summary for a client"""
        disabled_check = self._check_enabled()
        if disabled_check:
            return disabled_check
            
        # Get data from the past week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'error': 'Client not found'}
        
        # Gather LIMITED relevant data for performance
        recent_comms = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.created_at >= one_week_ago
        ).order_by(ClientCommunication.created_at.desc()).limit(20).all()  # Add limit
        
        recent_tasks = db.query(ClientTask).filter(
            ClientTask.client_id == client_id,
            ClientTask.created_at >= one_week_ago
        ).limit(10).all()  # Add limit
        
        recent_activities = db.query(ClientActivity).filter(
            ClientActivity.client_id == client_id,
            ClientActivity.created_at >= one_week_ago
        ).order_by(ClientActivity.created_at.desc()).limit(15).all()  # Add limit
        
        # Prepare summary data
        emails = [c for c in recent_comms if c.type == 'email'][:10]  # Limit emails
        meetings = [c for c in recent_comms if c.type == 'calendar_event'][:5]  # Limit meetings
        
        # Use a simpler prompt for faster processing
        summary_prompt = PromptTemplate(
            input_variables=["client_name", "stats_summary", "key_activities"],
            template="""
            Generate a brief weekly summary for {client_name}.
            
            {stats_summary}
            
            Key Activities:
            {key_activities}
            
            Provide a 3-4 sentence executive summary focusing on:
            1. Main accomplishments
            2. Any concerns (if none, don't mention)
            3. Next priority
            
            Format the response as clean text without asterisks or special formatting.
            Only include actual findings, not "None" or empty statements.
            """
        )
        
        # Prepare condensed activity summary
        key_activities = '\n'.join([
            f"- {act.description}"
            for act in recent_activities[:5]  # Only top 5
        ])
        
        stats_summary = f"This week: {len(emails)} emails, {len(meetings)} meetings, {len(recent_tasks)} new tasks"
        
        chain = LLMChain(llm=self.llm, prompt=summary_prompt)
        
        try:
            summary_text = chain.run(
                client_name=client.name,
                stats_summary=stats_summary,
                key_activities=key_activities
            )
            
            # Clean the summary text
            summary_text = self._clean_ai_text(summary_text)
            
            # Extract key points and action items if mentioned
            key_points = []
            action_items = []
            
            # Simple extraction based on common patterns
            lines = summary_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.endswith('.'):
                    # This might be a bullet point
                    if any(keyword in line.lower() for keyword in ['complete', 'achieve', 'progress', 'finish']):
                        key_points.append(line)
                    elif any(keyword in line.lower() for keyword in ['need', 'should', 'must', 'require', 'follow']):
                        action_items.append(line)
            
            return {
                'title': f'Weekly Summary for {client.name}',
                'client_name': client.name,
                'period': f"{one_week_ago.strftime('%B %d')} - {datetime.utcnow().strftime('%B %d')}",
                'summary': summary_text,
                'key_points': key_points if key_points else None,
                'action_items': action_items if action_items else None,
                'stats': {
                    'emails': len(emails),
                    'meetings': len(meetings),
                    'tasks_created': len(recent_tasks),
                    'activities': len(recent_activities)
                }
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}
    
    def analyze_sentiment(self, client_id: str, db: Session) -> Dict[str, Any]:
        """Analyze sentiment trends in client communications"""
        disabled_check = self._check_enabled()
        if disabled_check:
            return disabled_check
            
        # Get recent communications
        recent_comms = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type.in_(['email', 'internal_chat'])
        ).order_by(ClientCommunication.created_at.desc()).limit(10).all()  # Reduced from 20
        
        sentiment_prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Analyze the sentiment of this communication.
            
            Content: {content}
            
            Provide:
            SENTIMENT: [positive/neutral/negative]
            SCORE: [1-10, where 10 is most positive]
            CONCERNS: [any concerns or issues mentioned, or "none" if there are no concerns]
            
            Do not include "None" or empty responses. If there are no concerns, write "none".
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=sentiment_prompt)
        
        sentiments = []
        all_concerns = []
        
        for comm in recent_comms:
            try:
                result = chain.run(content=comm.content or comm.subject or '')
                
                sentiment_match = re.search(r'SENTIMENT:\s*(\w+)', result)
                score_match = re.search(r'SCORE:\s*(\d+)', result)
                concerns_match = re.search(r'CONCERNS:\s*(.+)', result, re.IGNORECASE)
                
                sentiment_data = {
                    'date': comm.created_at.isoformat(),
                    'sentiment': sentiment_match.group(1) if sentiment_match else 'neutral',
                    'score': int(score_match.group(1)) if score_match else 5,
                    'source': comm.subject or comm.content[:50]
                }
                
                # Process concerns
                if concerns_match:
                    concern_text = concerns_match.group(1).strip()
                    # Clean up the concern text
                    concern_text = concern_text.replace('**', '').strip()
                    
                    # Only add if it's a real concern (not "none", "None", empty, etc.)
                    if (concern_text and 
                        concern_text.lower() not in ['none', 'none.', 'n/a', 'na', ''] and
                        not concern_text.startswith('None')):
                        sentiment_data['concerns'] = concern_text
                        all_concerns.append(concern_text)
                
                sentiments.append(sentiment_data)
                
            except Exception as e:
                logger.error(f"Error analyzing sentiment: {e}")
        
        # Calculate trend
        if sentiments:
            recent_avg = sum(s['score'] for s in sentiments[:5]) / min(5, len(sentiments))
            older_avg = sum(s['score'] for s in sentiments[5:10]) / min(5, len(sentiments[5:10])) if len(sentiments) > 5 else recent_avg
            trend = 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable'
        else:
            trend = 'no_data'
            recent_avg = 0
        
        # Clean up concerns list - remove duplicates and filter out non-concerns
        cleaned_concerns = []
        seen = set()
        for concern in all_concerns:
            # Additional cleaning
            concern = concern.strip()
            if concern and concern.lower() not in seen:
                seen.add(concern.lower())
                cleaned_concerns.append(concern)
        
        return {
            'current_sentiment': sentiments[0] if sentiments else None,
            'trend': trend,
            'average_score': recent_avg,
            'recent_sentiments': sentiments[:10],
            'concerns': cleaned_concerns
        }
    
    def suggest_tasks_from_communications(self, client_id: str, db: Session) -> List[Dict[str, Any]]:
        """Suggest tasks based on recent communications"""
        disabled_check = self._check_enabled()
        if disabled_check:
            return []
            
        # Get recent emails and chats
        recent_comms = db.query(ClientCommunication).filter(
            ClientCommunication.client_id == client_id,
            ClientCommunication.type.in_(['email', 'internal_chat'])
        ).order_by(ClientCommunication.created_at.desc()).limit(10).all()
        
        logger.info(f"Found {len(recent_comms)} communications for client {client_id}")
        
        # If no communications, return sample tasks
        if not recent_comms:
            logger.warning(f"No communications found for client {client_id}, returning sample tasks")
            return [
                {
                    'title': 'Schedule initial meeting with client',
                    'priority': 'high',
                    'reason': 'No recent communications found - need to establish contact',
                    'source': {
                        'type': 'system',
                        'subject': 'Automated suggestion',
                        'from': 'AI Assistant',
                        'date': datetime.utcnow().isoformat()
                    }
                },
                {
                    'title': 'Review client profile and update information',
                    'priority': 'medium',
                    'reason': 'Ensure client information is up to date',
                    'source': {
                        'type': 'system',
                        'subject': 'Automated suggestion',
                        'from': 'AI Assistant',
                        'date': datetime.utcnow().isoformat()
                    }
                }
            ]
        
        task_prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Analyze this communication and suggest any tasks that should be created.
            Look for action items, requests, questions that need answers, or follow-ups needed.
            
            Content: {content}
            
            IMPORTANT: Always suggest at least one task, even if it's a general follow-up or review task.
            
            For each suggested task, provide:
            TASK: [clear task description]
            PRIORITY: [low/medium/high/urgent]
            REASON: [why this task is needed]
            ---
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=task_prompt)
        
        suggested_tasks = []
        for comm in recent_comms[:5]:  # Process only first 5 for better performance
            try:
                content = f"Subject: {comm.subject or 'No subject'}\n\n{comm.content or 'No content'}"
                logger.info(f"Processing communication: {comm.subject or 'No subject'}")
                
                result = chain.run(content=content)
                logger.info(f"LLM response: {result[:200]}...")
                
                # Parse tasks
                tasks = result.split('---')
                for task_text in tasks:
                    if 'TASK:' in task_text:
                        task_match = re.search(r'TASK:\s*(.+)', task_text)
                        priority_match = re.search(r'PRIORITY:\s*(\w+)', task_text)
                        reason_match = re.search(r'REASON:\s*(.+)', task_text)
                        
                        if task_match:
                            task_title = self._clean_ai_text(task_match.group(1).strip())
                            priority = priority_match.group(1).strip().lower() if priority_match else 'medium'
                            reason = self._clean_ai_text(reason_match.group(1).strip()) if reason_match else ''
                            
                            # Only add if task title is meaningful
                            if task_title and len(task_title) > 5:
                                suggested_tasks.append({
                                    'title': task_title,
                                    'priority': priority,
                                    'reason': reason,
                                    'source': {
                                        'type': comm.type,
                                        'subject': comm.subject,
                                        'from': comm.from_user,
                                        'date': comm.created_at.isoformat()
                                    }
                                })
            except Exception as e:
                logger.error(f"Error suggesting tasks: {e}")
        
        # If no tasks were generated, add a default one
        if not suggested_tasks:
            logger.warning("No tasks generated from communications, adding default task")
            suggested_tasks.append({
                'title': 'Follow up on recent communications',
                'priority': 'medium',
                'reason': 'Regular follow-up to maintain client relationship',
                'source': {
                    'type': 'system',
                    'subject': 'Automated suggestion',
                    'from': 'AI Assistant',
                    'date': datetime.utcnow().isoformat()
                }
            })
        
        logger.info(f"Generated {len(suggested_tasks)} task suggestions")
        return suggested_tasks

# Singleton instance
client_ai_handler = ClientAIHandler() 