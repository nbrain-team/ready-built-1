"""
Super Agent Handler - Manages AI-powered workflows
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from sqlalchemy.orm import Session
from .database import User
from .client_portal_models import Client, ClientCommunication

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    logger.warning("GEMINI_API_KEY not found. Super Agent AI features will be limited.")
    model = None

class SuperAgentHandler:
    """Handles Super Agent workflows and AI interactions"""
    
    def __init__(self):
        self.workflows = {
            'social_media': self.handle_social_media_workflow,
            'document_generation': self.handle_document_workflow,
            'task_management': self.handle_task_workflow,
            'communication': self.handle_communication_workflow,
            'google_docs_content': self.handle_google_docs_workflow,
            'video_avatar': self.handle_video_avatar_workflow,
            'task_suggestion': self.handle_task_suggestion_workflow
        }
    
    def process_message(
        self, 
        message: str, 
        workflow_id: Optional[str], 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Process a message from the user"""
        
        if workflow_id and workflow_id in self.workflows:
            # Handle specific workflow
            return self.workflows[workflow_id](message, context, user, db)
        else:
            # Detect workflow from message
            detected_workflow = self.detect_workflow(message)
            if detected_workflow:
                # Check if this is social media workflow with platform already specified
                if detected_workflow['id'] == 'social_media':
                    message_lower = message.lower()
                    # Check if platform is already mentioned
                    for platform in ['facebook', 'linkedin', 'twitter']:
                        if platform in message_lower:
                            # Start the workflow with platform already set
                            context['platform'] = platform
                            return {
                                'workflow_detected': detected_workflow,
                                'context_update': {'platform': platform},
                                'response': f"I'll help you create a {platform} post. What's the topic or message you'd like to share?"
                            }
                
                return {
                    'workflow_detected': detected_workflow,
                    'response': f"I can help you with {detected_workflow['name']}. Let's get started!\n\n{detected_workflow['first_question']}"
                }
            else:
                return {
                    'response': "I can help you with:\n• Creating social media posts\n• Generating documents\n• Managing tasks\n• Sending communications\n\nWhat would you like to do?"
                }
    
    def detect_workflow(self, message: str) -> Optional[Dict[str, Any]]:
        """Detect which workflow the user wants to use"""
        message_lower = message.lower()
        
        # Check if this is a follow-up scheduling request
        if any(phrase in message_lower for phrase in ['post next', 'post for', 'schedule for', 'post on']):
            # Don't detect a new workflow if we're in the middle of scheduling
            return None
        
        workflows = [
            {
                'id': 'social_media',
                'name': 'Social Media Management',
                'keywords': ['facebook', 'linkedin', 'twitter', 'social media', 'post', 'share', 'tweet', 'linkedin post', 'facebook post', 'twitter post', 'create a post'],
                'first_question': 'Which platform would you like to post to? (Facebook, LinkedIn, Twitter)'
            },
            {
                'id': 'document_generation',
                'name': 'Document Generation',
                'keywords': ['document', 'proposal', 'report', 'create', 'generate', 'write'],
                'first_question': 'What type of document would you like to create? (Proposal, Report, Email)'
            },
            {
                'id': 'google_docs_content',
                'name': 'Create Content & Save to Google Docs',
                'keywords': ['google doc', 'google docs', 'gdoc', 'save to doc', 'create doc'],
                'first_question': 'What type of content would you like to create? (e.g., Blog Post, Meeting Notes, Project Plan, Report)'
            },
            {
                'id': 'video_avatar',
                'name': 'Create Video Avatar',
                'keywords': ['video avatar', 'video', 'avatar', 'heygen', 'create video', 'video message'],
                'first_question': 'What would you like your video avatar to talk about?'
            },
            {
                'id': 'task_management',
                'name': 'Task Management',
                'keywords': ['task', 'todo', 'assign', 'create task', 'update task'],
                'first_question': 'Would you like to create a new task or update an existing one?'
            },
            {
                'id': 'task_suggestion',
                'name': 'Task Suggestions',
                'keywords': ['suggest task', 'task suggestion', 'what should i do', 'tasks for', 'marketing task', 'sales task'],
                'first_question': 'I can suggest tasks based on client data. Which client would you like task suggestions for?'
            },
            {
                'id': 'communication',
                'name': 'Communication',
                'keywords': ['email', 'send', 'message', 'meeting', 'schedule', 'calendar'],
                'first_question': 'Would you like to send an email or schedule a meeting?'
            }
        ]
        
        for workflow in workflows:
            for keyword in workflow['keywords']:
                if keyword in message_lower:
                    return workflow
        
        return None
    
    def handle_social_media_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle social media posting workflow"""
        
        # Check if this is the initial message with topic
        message_lower = message.lower()
        
        # Clean up voice input artifacts
        # Remove duplicate words and clean up common voice recognition errors
        words = message_lower.split()
        cleaned_words = []
        prev_word = ""
        for word in words:
            if word != prev_word:  # Remove immediate duplicates
                cleaned_words.append(word)
                prev_word = word
        message_lower = ' '.join(cleaned_words)
        
        # Check if this is the initial workflow trigger with platform already specified
        if 'platform' not in context and any(phrase in message_lower for phrase in ['create a linkedin', 'create a facebook', 'create a twitter', 'create an email', 'linkedin post', 'facebook post', 'twitter post', 'email campaign']):
            # Extract platform from the initial message
            platform = None
            for p in ['facebook', 'linkedin', 'twitter', 'email']:
                if p in message_lower:
                    platform = p
                    break
            
            if platform:
                # Check if topic is also in the message (e.g., "linkedin post about RAG")
                if ' about ' in message_lower:
                    topic_parts = message.split(' about ', 1)
                    if len(topic_parts) > 1:
                        topic = topic_parts[1].strip()
                        # We have both platform and topic, generate content directly
                        context['platform'] = platform
                        context['topic'] = topic
                        return self._generate_social_content(platform, topic, context, user, db)
                else:
                    # Platform detected in initial message, ask for topic
                    return {
                        'context_update': {'platform': platform},
                        'response': f"I'll help you create a {platform} post. What's the topic or message you'd like to share?"
                    }
        
        # If we're starting fresh and the message contains "about", extract the topic
        if 'platform' not in context and ' about ' in message_lower:
            topic_parts = message.split(' about ', 1)
            if len(topic_parts) > 1:
                topic = topic_parts[1].strip()
                
                # Check if a specific platform is mentioned
                platform = None
                for p in ['facebook', 'linkedin', 'twitter', 'email']:
                    if p in message_lower:
                        platform = p
                        break
                
                if platform:
                    # We have both platform and topic
                    context['platform'] = platform
                    context['topic'] = topic
                    # Skip directly to content generation
                    return self._generate_social_content(platform, topic, context, user, db)
                else:
                    # We have topic but no platform, ask for platform
                    return {
                        'context_update': {'topic': topic},
                        'response': f"I'll create a social media post about {topic}. Which platform would you like to post to? (Facebook, LinkedIn, or Twitter)"
                    }
        
        # State machine for social media workflow
        if 'platform' not in context:
            # Step 1: Get platform
            # Extract platform from message even if it has extra words
            platform = None
            for p in ['facebook', 'linkedin', 'twitter', 'email']:
                if p in message_lower:
                    platform = p
                    break
            
            if platform:
                # Check if we already have a topic
                if 'topic' in context:
                    context['platform'] = platform
                    return self._generate_social_content(platform, context['topic'], context, user, db)
                else:
                    return {
                        'context_update': {'platform': platform},
                        'response': f"Great! I'll help you create a {platform} post. What's the topic or message you'd like to share?"
                    }
            else:
                return {
                    'response': "Please specify: Facebook, LinkedIn, Twitter, or Email?"
                }
        
        elif 'topic' not in context:
            # Step 2: Get topic and generate content
            topic = message
            context['topic'] = topic
            return self._generate_social_content(context['platform'], topic, context, user, db)
        
        elif 'generated_content' in context and 'post' in message.lower():
            # Step 3: Confirm posting
            return {
                'context_update': {'awaiting_confirmation': True},
                'response': f"I'm about to post this to {context['platform']}. Please confirm by typing 'yes' or 'confirm'."
            }
        
        elif context.get('generated_content') and not context.get('awaiting_confirmation'):
            # Handle scheduling or modification requests
            message_lower = message.lower()
            
            # Check if user wants to schedule for a specific time
            if any(word in message_lower for word in ['schedule', 'post for', 'post on', 'next', 'tomorrow', 'post next']):
                # Parse date from message
                from datetime import datetime, timedelta
                import dateparser
                
                scheduled_date = None
                
                # Clean up the message for better parsing
                clean_message = message
                for phrase in ['post for', 'post on', 'schedule for', 'schedule on', 'post']:
                    clean_message = clean_message.replace(phrase, '')
                clean_message = clean_message.strip()
                
                logger.info(f"Parsing date from message: '{message}' -> cleaned: '{clean_message}'")
                
                # Try to parse the date with dateparser - it's quite smart
                # Use PREFER_DATES_FROM='future' to ensure "next Thursday" goes to the future
                # Also set RELATIVE_BASE to ensure relative dates are calculated from today
                parsed_date = dateparser.parse(
                    clean_message, 
                    settings={
                        'PREFER_DATES_FROM': 'future',
                        'RELATIVE_BASE': datetime.now(),
                        'TIMEZONE': 'UTC',
                        'RETURN_AS_TIMEZONE_AWARE': False,
                        'PREFER_DAY_OF_MONTH': 'first',  # For dates like "August 3"
                        'DATE_ORDER': 'MDY'  # Month-Day-Year order
                    }
                )
                
                if parsed_date:
                    # For specific dates (like "August 3"), ensure we're getting the right year
                    now = datetime.now()
                    if parsed_date.date() < now.date():
                        # If the date is in the past, assume next year
                        if parsed_date.month < now.month or (parsed_date.month == now.month and parsed_date.day < now.day):
                            parsed_date = parsed_date.replace(year=now.year + 1)
                    
                    # Ensure the date is in the future for relative dates
                    if parsed_date.date() <= now.date() and 'next' in message_lower:
                        # If the parsed date is today or in the past, but the user said "next",
                        # add a week to get the next occurrence
                        parsed_date = parsed_date + timedelta(weeks=1)
                    
                    # If no time was specified, use 10 AM as default
                    if parsed_date.hour == 0 and parsed_date.minute == 0:
                        parsed_date = parsed_date.replace(hour=10, minute=0)
                        
                    scheduled_date = parsed_date
                    logger.info(f"Parsed date: {scheduled_date.strftime('%Y-%m-%d %H:%M')}")
                else:
                    # Fallback parsing for specific patterns
                    if 'tomorrow' in message_lower:
                        scheduled_date = datetime.now() + timedelta(days=1)
                        scheduled_date = scheduled_date.replace(hour=10, minute=0)
                    elif 'next week' in message_lower:
                        scheduled_date = datetime.now() + timedelta(weeks=1)
                        scheduled_date = scheduled_date.replace(hour=10, minute=0)
                    elif 'next' in message_lower and any(day in message_lower for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                        # Handle "next [day of week]" manually
                        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        for i, day in enumerate(days):
                            if day in message_lower:
                                today = datetime.now()
                                days_ahead = i - today.weekday()
                                if days_ahead <= 0:  # Target day already happened this week
                                    days_ahead += 7
                                scheduled_date = today + timedelta(days=days_ahead)
                                scheduled_date = scheduled_date.replace(hour=10, minute=0)
                                break
                    else:
                        # Default to 1 hour from now
                        scheduled_date = datetime.now() + timedelta(hours=1)
                
                # Save to social media calendar
                try:
                    from .social_media_models import SocialMediaPost, PostStatus, SocialPlatform
                    
                    # Fix the platform enum mapping - use the enum values directly
                    platform_map = {
                        'linkedin': SocialPlatform.LINKEDIN,
                        'facebook': SocialPlatform.FACEBOOK, 
                        'twitter': SocialPlatform.TWITTER,
                        'email': SocialPlatform.EMAIL
                    }
                    
                    platform_enum = platform_map.get(context['platform'].lower())
                    if not platform_enum:
                        raise ValueError(f"Invalid platform: {context['platform']}")
                    
                    post = SocialMediaPost(
                        platform=platform_enum,
                        content=context['generated_content'],
                        scheduled_date=scheduled_date,
                        status=PostStatus.SCHEDULED,
                        client_id=context.get('client_id'),
                        created_by=user.id
                    )
                    
                    db.add(post)
                    db.commit()
                    
                    # Format the date nicely for the response
                    date_str = scheduled_date.strftime('%A, %B %d at %I:%M %p')
                    
                    return {
                        'workflow_complete': True,
                        'response': f"✅ Successfully scheduled your {context['platform']} post for {date_str}!\n\nPost content:\n{context['generated_content'][:100]}...\n\nThe post has been added to your Marketing Calendar.",
                        'action': {
                            'type': 'social_media_scheduled',
                            'platform': context['platform'],
                            'content': context['generated_content'],
                            'post_id': post.id,
                            'scheduled_date': scheduled_date.isoformat()
                        }
                    }
                except Exception as e:
                    logger.error(f"Error scheduling social media post: {e}")
                    return {
                        'response': f"Error scheduling post: {str(e)}. Please try again."
                    }
            
            # Check if user just says "post" or "yes"
            elif message_lower in ['post', 'yes', 'post it', 'post this', 'confirm']:
                return {
                    'context_update': {'awaiting_confirmation': True},
                    'response': f"I'll post this to {context['platform']} now. Please confirm by typing 'yes' or 'confirm'."
                }
            
            # Otherwise, assume they want to modify the content
            else:
                return {
                    'response': "Would you like to:\n1. Post this now (say 'post it')\n2. Schedule for later (e.g., 'post for next Thursday')\n3. Make changes (describe what to change)"
                }
        
        elif context.get('awaiting_confirmation') and message.lower() in ['yes', 'confirm']:
            # Step 4: Post to social media immediately
            try:
                # Save to social media calendar
                from .social_media_models import SocialMediaPost, PostStatus, SocialPlatform
                from datetime import datetime, timedelta
                
                # Schedule for 1 hour from now by default
                scheduled_date = datetime.now() + timedelta(hours=1)
                
                # Fix the platform enum mapping - use the enum values directly
                platform_map = {
                    'linkedin': SocialPlatform.LINKEDIN,
                    'facebook': SocialPlatform.FACEBOOK, 
                    'twitter': SocialPlatform.TWITTER,
                    'email': SocialPlatform.EMAIL
                }
                
                platform_enum = platform_map.get(context['platform'].lower())
                if not platform_enum:
                    raise ValueError(f"Invalid platform: {context['platform']}")
                
                post = SocialMediaPost(
                    platform=platform_enum,
                    content=context['generated_content'],
                    scheduled_date=scheduled_date,
                    status=PostStatus.SCHEDULED,
                    client_id=context.get('client_id'),
                    created_by=user.id
                )
                
                db.add(post)
                db.commit()
                
                return {
                    'workflow_complete': True,
                    'response': f"✅ Successfully scheduled your {context['platform']} post!\n\nThe post has been added to your Marketing Calendar and is scheduled for {scheduled_date.strftime('%B %d at %I:%M %p')}.\n\nYou can view and manage all your scheduled posts in the Marketing Calendar.",
                    'action': {
                        'type': 'social_media_scheduled',
                        'platform': context['platform'],
                        'content': context['generated_content'],
                        'post_id': post.id,
                        'scheduled_date': scheduled_date.isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Error scheduling social media post: {e}")
                return {
                    'response': f"Error scheduling post: {str(e)}. Please try again."
                }
        
        else:
            # Handle other cases
            return {
                'response': "Would you like to:\n1. Post this content (say 'post it')\n2. Schedule for later (e.g., 'post for next Thursday')\n3. Create new content (describe what you want)"
            }
    
    def _generate_social_content(self, platform: str, topic: str, context: Dict[str, Any], user: User, db: Session) -> Dict[str, Any]:
        """Generate social media content using AI"""
        # Get client context if available
        client_context = ""
        client_name = None
        if context.get('client_id'):
            client = db.query(Client).filter(Client.id == context['client_id']).first()
            if client:
                client_name = client.name
                # Get recent communications to understand tone
                recent_comms = db.query(ClientCommunication).filter(
                    ClientCommunication.client_id == client.id,
                    ClientCommunication.type == 'email'
                ).order_by(ClientCommunication.created_at.desc()).limit(5).all()
                
                if recent_comms:
                    client_context = f"\nClient: {client.name}\nIndustry: {client.industry or 'Not specified'}\n"
        
        # Check if client name was mentioned in the topic
        if not client_name and 'client' in topic.lower():
            # Extract client name from topic like "for client nbrain"
            parts = topic.lower().split('client')
            if len(parts) > 1:
                potential_client = parts[1].strip().split()[0] if parts[1].strip() else None
                if potential_client:
                    client_context = f"\nClient: {potential_client}\n"
        
        # Generate post using AI
        if model:
            try:
                prompt = f"""Generate a {platform} post about: {topic}
                
{client_context}

Guidelines:
- For Facebook: Conversational, engaging, with emojis. 300-500 characters.
- For LinkedIn: Professional, insightful, thought leadership. 500-700 characters.
- For Twitter: Concise, punchy, with hashtags. Max 280 characters.
- For Email: Subject line + preview text + main content. Professional and actionable.

IMPORTANT: Generate ONLY ONE post for {platform}. Do not generate posts for other platforms.
Make it engaging and include relevant hashtags. Write in first person."""
                
                response = model.generate_content(prompt)
                generated_content = response.text.strip()
                
                # Clean up the content - remove any headers or labels
                lines = generated_content.split('\n')
                cleaned_lines = []
                skip_next = False
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                        
                    # Skip lines that are headers or labels
                    if any(label in line.lower() for label in [
                        'linkedin post:', 'facebook post:', 'twitter post:', 
                        '**linkedin', '**facebook', '**twitter', '##',
                        'post:', 'here\'s your', 'i\'ll help'
                    ]):
                        skip_next = True
                        continue
                    
                    # Skip line after header
                    if skip_next and line.startswith('**'):
                        skip_next = False
                        continue
                        
                    skip_next = False
                    cleaned_lines.append(line)
                
                # Join and clean up
                cleaned_content = '\n'.join(cleaned_lines).strip()
                # Remove any remaining markdown formatting
                cleaned_content = cleaned_content.replace('**', '')
                
                # Store the generated content in context for later use
                context['generated_content'] = cleaned_content
                context['platform'] = platform
                context['topic'] = topic
                
                return {
                    'context_update': {
                        'generated_content': cleaned_content,
                        'platform': platform,
                        'topic': topic
                    },
                    'response': f"Here's your {platform} post:\n\n{cleaned_content}\n\nWould you like to:\n1. Post this now (say 'post it')\n2. Schedule for later (e.g., 'post for next Thursday')\n3. Make changes (describe what to change)",
                    'generated_content': cleaned_content
                }
            except Exception as e:
                logger.error(f"Error generating content: {e}")
                return {
                    'response': "I encountered an error generating the post. Please try again."
                }
        else:
            # Fallback without AI
            return {
                'response': f"I'll help you create a {platform} post about {topic}. What key points would you like to include?"
            }
    
    def handle_document_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle document generation workflow"""
        
        if 'document_type' not in context:
            # Step 1: Get document type
            doc_type = message.lower().strip()
            if any(t in doc_type for t in ['proposal', 'report', 'email']):
                return {
                    'context_update': {'document_type': doc_type},
                    'response': f"I'll help you create a {doc_type}. What's the subject or purpose?"
                }
            else:
                return {
                    'response': "What type of document would you like to create? (Proposal, Report, Email)"
                }
        
        # Additional document workflow steps would go here
        return {
            'response': "Document generation workflow in progress..."
        }
    
    def handle_task_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle task management workflow"""
        
        if 'action' not in context:
            # Step 1: Determine action
            if 'create' in message.lower() or 'new' in message.lower():
                return {
                    'context_update': {'action': 'create'},
                    'response': "What's the task title or description?"
                }
            elif 'update' in message.lower() or 'edit' in message.lower():
                return {
                    'context_update': {'action': 'update'},
                    'response': "Which task would you like to update? Please provide the task name or ID."
                }
            else:
                return {
                    'response': "Would you like to create a new task or update an existing one?"
                }
        
        # Additional task workflow steps would go here
        return {
            'response': "Task management workflow in progress..."
        }
    
    def handle_communication_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle communication workflow"""
        
        if 'comm_type' not in context:
            # Step 1: Determine communication type
            if 'email' in message.lower():
                return {
                    'context_update': {'comm_type': 'email'},
                    'response': "Who would you like to send the email to?"
                }
            elif 'meeting' in message.lower() or 'calendar' in message.lower():
                return {
                    'context_update': {'comm_type': 'meeting'},
                    'response': "What's the meeting about and when would you like to schedule it?"
                }
            else:
                return {
                    'response': "Would you like to send an email or schedule a meeting?"
                }
        
        # Additional communication workflow steps would go here
        return {
            'response': "Communication workflow in progress..."
        }

    def handle_google_docs_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle Google Docs content creation workflow"""
        
        # State machine for Google Docs workflow
        if 'content_type' not in context:
            # Step 1: Get content type
            return {
                'context_update': {'content_type': message},
                'response': f"I'll help you create {message}. What's the title for this document?"
            }
        
        elif 'title' not in context:
            # Step 2: Get title
            return {
                'context_update': {'title': message},
                'response': f"Great! Now, please provide the main topic or outline for your {context['content_type']}. What should it cover?"
            }
        
        elif 'topic' not in context:
            # Step 3: Get topic/outline and generate content
            topic = message
            
            # Get client context if available
            client_name = None
            client_context = ""
            if context.get('client_id'):
                client = db.query(Client).filter(Client.id == context['client_id']).first()
                if client:
                    client_name = client.name
                    client_context = f"\nClient: {client.name}\nIndustry: {client.industry or 'Not specified'}\n"
            
            # Generate content using AI
            if model:
                try:
                    content_type = context['content_type']
                    title = context['title']
                    prompt = f"""Create a professional {content_type} with the following details:

Title: {title}
Topic/Outline: {topic}
{client_context}

Guidelines:
- Make it comprehensive and well-structured
- Use appropriate formatting with sections and subsections
- Include relevant details and insights
- Professional tone unless specified otherwise
- Length: Appropriate for the content type (longer for reports, shorter for meeting notes)

Format the output with clear headings and sections."""
                    
                    response = model.generate_content(prompt)
                    generated_content = response.text
                    
                    return {
                        'context_update': {
                            'topic': topic, 
                            'generated_content': generated_content,
                            'client_name': client_name
                        },
                        'response': f"Here's your {content_type}:\n\n{generated_content}\n\nWould you like me to save this to Google Docs, or would you like to make changes?",
                        'generated_content': generated_content
                    }
                except Exception as e:
                    logger.error(f"Error generating content: {e}")
                    return {
                        'response': "I encountered an error generating the content. Please try again."
                    }
            else:
                # Fallback without AI
                return {
                    'context_update': {'topic': topic},
                    'response': f"I'll help you create a {context['content_type']} about {topic}. What key points would you like to include?"
                }
        
        elif 'generated_content' in context and ('save' in message.lower() or 'yes' in message.lower()):
            # Step 4: Save to Google Docs
            try:
                # Import the Google Docs handler
                from .google_docs_handler import google_docs_handler
                
                # Prepare document data
                doc_data = {
                    'title': context['title'],
                    'content_type': context['content_type'],
                    'content': context['generated_content'],
                    'client_name': context.get('client_name'),
                    'created_by': user.email
                }
                
                # Create the Google Doc
                result = google_docs_handler.create_content_doc(doc_data)
                
                if result['success']:
                    # If we have a client, save the document reference
                    if context.get('client_id') and context.get('client_name'):
                        from .client_portal_models import ClientDocument
                        
                        # Create document record
                        document = ClientDocument(
                            client_id=context['client_id'],
                            name=context['title'],
                            type='google_doc',
                            file_path=result['doc_url'],
                            google_drive_id=result['doc_id'],
                            uploaded_by=user.id
                        )
                        db.add(document)
                        
                        # Create activity
                        from .client_portal_models import ClientActivity
                        activity = ClientActivity(
                            client_id=context['client_id'],
                            user_id=user.id,
                            activity_type="document_created",
                            description=f"Created Google Doc: {context['title']}",
                            meta_data={"document_id": result['doc_id'], "document_type": context['content_type']}
                        )
                        db.add(activity)
                        
                        db.commit()
                        
                        return {
                            'workflow_complete': True,
                            'response': f"✅ Successfully created and saved '{context['title']}' to Google Docs!\n\n📄 [View Document]({result['doc_url']})\n\nThe document has been added to {context['client_name']}'s documents section.",
                            'action': {
                                'type': 'google_doc_created',
                                'doc_url': result['doc_url'],
                                'doc_id': result['doc_id'],
                                'client_id': context['client_id']
                            }
                        }
                    else:
                        return {
                            'workflow_complete': True,
                            'response': f"✅ Successfully created '{context['title']}' in Google Docs!\n\n📄 [View Document]({result['doc_url']})",
                            'action': {
                                'type': 'google_doc_created',
                                'doc_url': result['doc_url'],
                                'doc_id': result['doc_id']
                            }
                        }
                else:
                    return {
                        'response': f"Error creating Google Doc: {result.get('error', 'Unknown error')}. Would you like to try again?"
                    }
                    
            except Exception as e:
                logger.error(f"Error saving to Google Docs: {e}")
                return {
                    'response': "I encountered an error saving to Google Docs. Please try again."
                }
        
        else:
            # Handle modifications or other inputs
            return {
                'response': "Would you like to modify the content or save it to Google Docs? Say 'save it' to create the document or describe the changes you'd like."
            }

    def handle_video_avatar_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle video avatar creation workflow"""
        
        # State machine for video avatar workflow
        if 'topic' not in context:
            # Step 1: Get topic
            return {
                'context_update': {'topic': message},
                'response': "I'll help you create a video avatar! Would you like me to:\n\n1. Create the script on my own\n2. Present a draft for your review first\n\nPlease type '1' or '2', or describe your preference."
            }
        
        elif 'creation_mode' not in context:
            # Step 2: Get creation mode
            if '1' in message or 'own' in message.lower() or 'create' in message.lower():
                context['creation_mode'] = 'auto'
            elif '2' in message or 'draft' in message.lower() or 'review' in message.lower():
                context['creation_mode'] = 'review'
            else:
                return {
                    'response': "Please choose:\n1. Create on my own\n2. Present draft first"
                }
            
            # Generate script
            script = self._generate_video_script(context['topic'], user, db)
            
            if context['creation_mode'] == 'review':
                return {
                    'context_update': {
                        'creation_mode': context['creation_mode'],
                        'script': script
                    },
                    'response': f"Here's the script I've created:\n\n---\n{script}\n---\n\nWould you like to:\n1. Use this script\n2. Make changes\n3. Start over"
                }
            else:
                # Auto mode - go straight to video generation
                return {
                    'context_update': {
                        'creation_mode': context['creation_mode'],
                        'script': script,
                        'script_approved': True
                    },
                    'response': f"I'm generating your video avatar with this script:\n\n{script[:200]}...\n\nThis will take a few moments. Once complete, would you like to schedule it to social media or save as a document?"
                }
        
        elif context.get('creation_mode') == 'review' and not context.get('script_approved'):
            # Step 3: Handle script review
            if '1' in message or 'use' in message.lower() or 'yes' in message.lower():
                context['script_approved'] = True
                return {
                    'context_update': {'script_approved': True},
                    'response': "Great! I'm generating your video avatar now. This will take a few moments.\n\nOnce complete, would you like to schedule it to social media or save as a document?"
                }
            elif '2' in message or 'change' in message.lower():
                return {
                    'response': "What changes would you like to make to the script?"
                }
            elif '3' in message or 'start over' in message.lower():
                return {
                    'context_update': {},
                    'response': "Let's start over. What would you like your video avatar to talk about?"
                }
            else:
                # Assume they're providing edits
                script = context['script'] + "\n\n" + message
                return {
                    'context_update': {'script': script},
                    'response': f"I've updated the script:\n\n---\n{script}\n---\n\nWould you like to use this script?"
                }
        
        elif context.get('script_approved') and not context.get('video_generated'):
            # Step 4: Generate video
            from .heygen_handler import heygen_handler
            
            # Generate video
            result = heygen_handler.generate_video(
                text=context['script'],
                title=f"Video about {context['topic'][:50]}"
            )
            
            if result.get('error'):
                return {
                    'response': f"Error generating video: {result['error']}. Would you like to try again?"
                }
            
            video_id = result.get('video_id')
            
            # Wait for video to complete (in production, this should be async)
            video_status = heygen_handler.wait_for_video(video_id)
            
            if video_status.get('error'):
                return {
                    'response': f"Error processing video: {video_status['error']}. Would you like to try again?"
                }
            
            return {
                'context_update': {
                    'video_generated': True,
                    'video_url': video_status.get('video_url'),
                    'thumbnail_url': video_status.get('thumbnail_url'),
                    'video_id': video_id
                },
                'response': f"✅ Your video avatar is ready!\n\n🎥 [View Video]({video_status.get('video_url')})\n\nWould you like to:\n1. Schedule to social media\n2. Save as a document\n\nYou can say things like 'Schedule for next Thursday on LinkedIn' or 'Save as document'"
            }
        
        elif context.get('video_generated'):
            # Step 5: Handle scheduling/saving
            message_lower = message.lower()
            
            if 'schedule' in message_lower or 'post' in message_lower:
                # Parse scheduling intent
                platform = None
                if 'linkedin' in message_lower:
                    platform = 'linkedin'
                elif 'twitter' in message_lower:
                    platform = 'twitter'
                elif 'facebook' in message_lower:
                    platform = 'facebook'
                
                # Parse date
                from datetime import datetime, timedelta
                import dateparser
                
                # Try to parse the date from the message
                scheduled_date = None
                if 'next' in message_lower:
                    # Handle "next Thursday", "next week", etc.
                    date_str = message_lower.split('next')[1].strip()
                    parsed_date = dateparser.parse(f"next {date_str}")
                    if parsed_date:
                        scheduled_date = parsed_date
                else:
                    # Try general date parsing
                    parsed_date = dateparser.parse(message)
                    if parsed_date:
                        scheduled_date = parsed_date
                
                if not scheduled_date:
                    scheduled_date = datetime.now() + timedelta(days=1)  # Default to tomorrow
                
                if not platform:
                    return {
                        'response': "Which platform would you like to post to? (LinkedIn, Twitter, or Facebook)"
                    }
                
                # Save to social media calendar
                try:
                    from .social_media_models import SocialMediaPost, PostStatus, SocialPlatform
                    
                    post_content = f"Check out my latest video: {context['video_url']}\n\n{context['topic']}"
                    
                    # Map platform string to enum
                    platform_map = {
                        'linkedin': SocialPlatform.LINKEDIN,
                        'facebook': SocialPlatform.FACEBOOK,
                        'twitter': SocialPlatform.TWITTER
                    }
                    
                    platform_enum = platform_map.get(platform.lower())
                    if not platform_enum:
                        raise ValueError(f"Invalid platform: {platform}")
                    
                    post = SocialMediaPost(
                        platform=platform_enum,
                        content=post_content,
                        scheduled_date=scheduled_date,
                        status=PostStatus.SCHEDULED,
                        client_id=context.get('client_id'),
                        created_by=user.id,
                        media_urls=[context['video_url']],
                        platform_data={'video_thumbnail': context.get('thumbnail_url')}
                    )
                    
                    db.add(post)
                    db.commit()
                    
                    return {
                        'workflow_complete': True,
                        'response': f"✅ Video scheduled for {scheduled_date.strftime('%A, %B %d at %I:%M %p')} on {platform.title()}!\n\nYou can view and manage it in your Marketing Calendar.",
                        'action': {
                            'type': 'video_scheduled',
                            'platform': platform,
                            'scheduled_date': scheduled_date.isoformat(),
                            'video_url': context['video_url']
                        }
                    }
                except Exception as e:
                    logger.error(f"Error scheduling video: {e}")
                    return {
                        'response': f"Error scheduling video: {str(e)}. Would you like to try again?"
                    }
            
            elif 'save' in message_lower or 'document' in message_lower:
                # Save as document
                try:
                    from .google_docs_handler import google_docs_handler
                    
                    doc_content = f"""Video Avatar: {context['topic']}

Video URL: {context['video_url']}

Script:
{context['script']}

Created: {datetime.now().strftime('%B %d, %Y')}
"""
                    
                    doc_data = {
                        'title': f"Video Avatar - {context['topic'][:50]}",
                        'content_type': 'Video Script',
                        'content': doc_content,
                        'client_name': None,
                        'created_by': user.email
                    }
                    
                    result = google_docs_handler.create_content_doc(doc_data)
                    
                    if result['success']:
                        return {
                            'workflow_complete': True,
                            'response': f"✅ Video and script saved to Google Docs!\n\n📄 [View Document]({result['doc_url']})\n🎥 [View Video]({context['video_url']})",
                            'action': {
                                'type': 'video_saved_doc',
                                'doc_url': result['doc_url'],
                                'video_url': context['video_url']
                            }
                        }
                    else:
                        return {
                            'response': f"Error saving document: {result.get('error')}. Would you like to try again?"
                        }
                except Exception as e:
                    logger.error(f"Error saving video document: {e}")
                    return {
                        'response': f"Error saving document: {str(e)}. Would you like to try again?"
                    }
            
            else:
                return {
                    'response': "Would you like to:\n1. Schedule to social media (e.g., 'Schedule for next Thursday on LinkedIn')\n2. Save as a document"
                }
        
        return {
            'response': "I'm not sure what you'd like to do. Please let me know if you want to schedule the video or save it as a document."
        }
    
    def handle_task_suggestion_workflow(
        self, 
        message: str, 
        context: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle task suggestion workflow based on client data"""
        
        # Check if client is already specified in the message
        message_lower = message.lower()
        
        # Extract client name from message patterns like "suggest a task for [client]"
        client_name = None
        for pattern in ['for ', 'client ', 'about ']:
            if pattern in message_lower:
                parts = message_lower.split(pattern)
                if len(parts) > 1:
                    potential_name = parts[1].strip()
                    # Clean up the name
                    for end_word in ['please', 'thanks', '?', '.', '!']:
                        if end_word in potential_name:
                            potential_name = potential_name.split(end_word)[0].strip()
                    if potential_name:
                        client_name = potential_name
                        break
        
        # Check for task type specification
        task_type = None
        if 'marketing' in message_lower:
            task_type = 'marketing'
        elif 'sales' in message_lower:
            task_type = 'sales'
        elif 'follow up' in message_lower or 'follow-up' in message_lower:
            task_type = 'follow_up'
        elif 'technical' in message_lower or 'development' in message_lower:
            task_type = 'technical'
        
        if client_name:
            # Try to find the client
            client = db.query(Client).filter(
                Client.name.ilike(f'%{client_name}%')
            ).first()
            
            if not client:
                # Try to find clients and suggest
                clients = db.query(Client).filter(
                    Client.name.ilike(f'%{client_name}%')
                ).limit(5).all()
                
                if clients:
                    client_list = '\n'.join([f"• {c.name}" for c in clients])
                    return {
                        'response': f"I found these clients matching '{client_name}':\n\n{client_list}\n\nWhich one did you mean?"
                    }
                else:
                    return {
                        'response': f"I couldn't find a client named '{client_name}'. Would you like to see a list of all clients?"
                    }
            
            # We have a client, now generate task suggestions
            return self._generate_task_suggestions(client, task_type, user, db)
        
        elif 'client_id' not in context:
            # No client specified, ask for one
            clients = db.query(Client).order_by(Client.name).limit(10).all()
            
            if not clients:
                return {
                    'response': "I don't see any clients in the system. Would you like to create a new client first?"
                }
            
            client_list = '\n'.join([f"• {c.name}" for c in clients])
            return {
                'response': f"Which client would you like task suggestions for?\n\n{client_list}\n\nJust type the client name or say 'suggest a task for [client name]'"
            }
        
        else:
            # We have context, generate suggestions
            client = db.query(Client).filter(Client.id == context['client_id']).first()
            if client:
                return self._generate_task_suggestions(client, task_type, user, db)
            else:
                return {
                    'response': "I couldn't find that client. Please specify which client you'd like task suggestions for."
                }
    
    def _generate_task_suggestions(
        self, 
        client: Client, 
        task_type: Optional[str],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Generate AI-powered task suggestions based on client data"""
        
        # Import the client AI handler
        from .client_ai_handler import client_ai_handler
        
        try:
            # Get AI task suggestions
            suggestions = client_ai_handler.suggest_tasks(client.id, db)
            
            if suggestions.get('error'):
                return {
                    'response': f"Error generating suggestions: {suggestions['error']}"
                }
            
            tasks = suggestions.get('tasks', [])
            
            # Filter by task type if specified
            if task_type and tasks:
                filtered_tasks = []
                for task in tasks:
                    task_lower = task.get('title', '').lower() + ' ' + task.get('description', '').lower()
                    if task_type == 'marketing' and any(word in task_lower for word in ['marketing', 'content', 'social', 'campaign', 'brand']):
                        filtered_tasks.append(task)
                    elif task_type == 'sales' and any(word in task_lower for word in ['sales', 'proposal', 'pitch', 'deal', 'contract']):
                        filtered_tasks.append(task)
                    elif task_type == 'follow_up' and any(word in task_lower for word in ['follow', 'check', 'meeting', 'call', 'email']):
                        filtered_tasks.append(task)
                    elif task_type == 'technical' and any(word in task_lower for word in ['technical', 'development', 'implementation', 'integration']):
                        filtered_tasks.append(task)
                
                if filtered_tasks:
                    tasks = filtered_tasks
                else:
                    # If no tasks match the filter, mention it but show all tasks
                    task_type_msg = f"\n\nI couldn't find specific {task_type} tasks, but here are other suggestions:"
            else:
                task_type_msg = ""
            
            if not tasks:
                return {
                    'response': f"I couldn't generate task suggestions for {client.name} at this time. Try syncing their emails first to get more data."
                }
            
            # Format the response
            response = f"Here are my AI-suggested tasks for **{client.name}**:{task_type_msg if task_type else ''}\n\n"
            
            for i, task in enumerate(tasks[:5], 1):  # Show top 5 tasks
                priority_emoji = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(task.get('priority', 'medium'), '🟡')
                
                response += f"{i}. {priority_emoji} **{task['title']}**\n"
                response += f"   {task['description']}\n"
                response += f"   *Priority: {task['priority'].title()} | Due: {task['due_date']}*\n\n"
            
            response += "\nWould you like to:\n"
            response += "• Create one of these tasks (type the number)\n"
            response += "• Get more details about a task\n"
            response += "• See different suggestions\n"
            response += "• Filter by type (marketing, sales, follow-up, technical)"
            
            return {
                'context_update': {
                    'client_id': client.id,
                    'client_name': client.name,
                    'suggested_tasks': tasks[:5]
                },
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Error generating task suggestions: {e}")
            return {
                'response': f"I encountered an error generating task suggestions. Please try again."
            }
    
    def _generate_video_script(self, topic: str, user: User, db: Session) -> str:
        """Generate a video script based on the topic"""
        if model:
            try:
                prompt = f"""Create a professional video script for a talking avatar about: {topic}

Guidelines:
- Keep it conversational and engaging
- 60-90 seconds when spoken (approximately 150-200 words)
- Use personal pronouns (I, we, you)
- Include a clear introduction, main points, and call to action
- Make it suitable for professional social media (LinkedIn, Twitter)
- Natural speaking rhythm with appropriate pauses

Format: Write only the spoken script, no stage directions or notes."""
                
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                logger.error(f"Error generating video script: {e}")
                return f"Hello! Today I want to talk to you about {topic}. [Script generation failed - please provide your own script]"
        else:
            return f"Hello! Today I want to talk to you about {topic}. [AI not available - please provide your own script]"

# Create singleton instance
super_agent_handler = SuperAgentHandler() 