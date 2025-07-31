"""
Social Media Calendar API Endpoints
"""

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import os

from .database import get_db, User
from .auth import get_current_active_user
from .social_media_models import SocialMediaPost, PostStatus, SocialPlatform

logger = logging.getLogger(__name__)

class SocialPostCreate(BaseModel):
    platform: str
    content: str
    scheduledDate: datetime
    publishedDate: Optional[datetime] = None
    status: str = "scheduled"
    clientId: Optional[str] = None
    campaignName: Optional[str] = None
    mediaUrls: Optional[List[str]] = None

class SocialPostUpdate(BaseModel):
    platform: Optional[str] = None
    content: Optional[str] = None
    scheduledDate: Optional[datetime] = None
    publishedDate: Optional[datetime] = None
    status: Optional[str] = None
    clientId: Optional[str] = None
    campaignName: Optional[str] = None
    mediaUrls: Optional[List[str]] = None

class SocialPostResponse(BaseModel):
    id: str
    platform: str
    content: str
    scheduledDate: datetime
    publishedDate: Optional[datetime]
    status: str
    clientId: Optional[str]
    clientName: Optional[str]
    campaignName: Optional[str]
    mediaUrls: Optional[List[str]]
    createdAt: datetime
    updatedAt: datetime
    
    @classmethod
    def from_orm(cls, post: SocialMediaPost):
        return cls(
            id=str(post.id),
            platform=post.platform.value,
            content=post.content,
            scheduledDate=post.scheduled_date,
            publishedDate=post.published_date,
            status=post.status.value,
            clientId=str(post.client_id) if post.client_id else None,
            clientName=post.client.name if post.client else None,
            campaignName=post.campaign_name,
            mediaUrls=post.media_urls,
            createdAt=post.created_at,
            updatedAt=post.updated_at
        )
    
    class Config:
        from_attributes = True

class BulkGenerateRequest(BaseModel):
    platforms: List[str]
    topics: List[str]
    durationWeeks: int
    emailCount: int
    startDate: str
    clientId: Optional[str] = None
    clientName: Optional[str] = None

def setup_social_media_endpoints(app):
    """Add Social Media Calendar endpoints to the FastAPI app"""
    
    @app.get("/social-media/posts", response_model=List[SocialPostResponse])
    async def get_social_posts(
        month: Optional[int] = None,
        year: Optional[int] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get social media posts with filters"""
        query = db.query(SocialMediaPost)
        
        # Filter by date range if month/year provided
        if month and year:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            query = query.filter(
                SocialMediaPost.scheduled_date >= start_date,
                SocialMediaPost.scheduled_date < end_date
            )
        
        # Other filters
        if platform:
            query = query.filter(SocialMediaPost.platform == SocialPlatform(platform))
        if status:
            query = query.filter(SocialMediaPost.status == PostStatus(status))
        if client_id:
            query = query.filter(SocialMediaPost.client_id == client_id)
        
        posts = query.order_by(SocialMediaPost.scheduled_date).all()
        
        # Convert to response format
        response_posts = []
        for post in posts:
            response_posts.append(SocialPostResponse(
                id=post.id,
                platform=post.platform.value,
                content=post.content,
                scheduledDate=post.scheduled_date,
                publishedDate=post.published_date,
                status=post.status.value,
                clientId=post.client_id,
                clientName=post.client.name if post.client else None,
                campaignName=post.campaign_name,
                mediaUrls=post.media_urls,
                createdAt=post.created_at,
                updatedAt=post.updated_at
            ))
        
        return response_posts
    
    @app.post("/social-media/posts")
    def create_social_media_post(
        post: SocialPostCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create a new social media post"""
        try:
            db_post = SocialMediaPost(
                platform=SocialPlatform[post.platform.upper()],
                content=post.content,
                scheduled_date=post.scheduledDate,
                status=PostStatus[post.status.upper()],
                client_id=post.clientId,
                created_by=current_user.id
            )
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            
            return SocialPostResponse.from_orm(db_post)
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.put("/social-media/posts/{post_id}", response_model=SocialPostResponse)
    async def update_social_post(
        post_id: str,
        update: SocialPostUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Update a social media post"""
        post = db.query(SocialMediaPost).filter(SocialMediaPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Update fields if provided
        if update.platform:
            post.platform = SocialPlatform(update.platform)
        if update.content:
            post.content = update.content
        if update.scheduledDate:
            post.scheduled_date = update.scheduledDate
        if update.status:
            post.status = PostStatus(update.status)
        if update.clientId is not None:
            post.client_id = update.clientId
        if update.campaignName is not None:
            post.campaign_name = update.campaignName
        if update.mediaUrls is not None:
            post.media_urls = update.mediaUrls
        
        db.commit()
        db.refresh(post)
        
        return SocialPostResponse(
            id=post.id,
            platform=post.platform.value,
            content=post.content,
            scheduledDate=post.scheduled_date,
            publishedDate=post.published_date,
            status=post.status.value,
            clientId=post.client_id,
            clientName=post.client.name if post.client else None,
            campaignName=post.campaign_name,
            mediaUrls=post.media_urls,
            createdAt=post.created_at,
            updatedAt=post.updated_at
        )
    
    @app.delete("/social-media/posts/{post_id}")
    async def delete_social_post(
        post_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Delete a social media post"""
        post = db.query(SocialMediaPost).filter(SocialMediaPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        db.delete(post)
        db.commit()
        
        return {"message": "Post deleted successfully"}
    
    @app.get("/social-media/upcoming")
    async def get_upcoming_posts(
        days: int = 7,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Get upcoming posts for the next N days"""
        end_date = datetime.utcnow() + timedelta(days=days)
        
        posts = db.query(SocialMediaPost).filter(
            SocialMediaPost.scheduled_date >= datetime.utcnow(),
            SocialMediaPost.scheduled_date <= end_date,
            SocialMediaPost.status == PostStatus.SCHEDULED
        ).order_by(SocialMediaPost.scheduled_date).all()
        
        # Group by date
        posts_by_date = {}
        for post in posts:
            date_key = post.scheduled_date.date().isoformat()
            if date_key not in posts_by_date:
                posts_by_date[date_key] = []
            
            posts_by_date[date_key].append({
                "id": post.id,
                "platform": post.platform.value,
                "content": post.content,
                "time": post.scheduled_date.strftime("%H:%M"),
                "clientName": post.client.name if post.client else None
            })
        
        return posts_by_date 

    @app.post("/social-media/bulk-generate")
    async def bulk_generate_calendar(
        request: BulkGenerateRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Generate bulk social media content based on topics and scheduling preferences"""
        
        try:
            import google.generativeai as genai
            
            # Configure Gemini if not already done
            GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
            if GEMINI_API_KEY:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-pro')
            else:
                raise HTTPException(status_code=500, detail="AI service not configured")
            
            start_date = datetime.fromisoformat(request.startDate.replace('Z', '+00:00'))
            posts_created = []
            
            # Get client context if provided
            client_context = ""
            if request.clientId and request.clientName:
                # Try to get relevant context from vectorized documents
                try:
                    from .vector_search import search_client_documents
                    
                    # Search for brand voice and style guidelines
                    brand_docs = search_client_documents(
                        client_id=request.clientId,
                        query="brand voice style guidelines messaging tone",
                        top_k=3
                    )
                    
                    if brand_docs:
                        client_context = f"\nClient: {request.clientName}\n"
                        client_context += "Brand Context from Documents:\n"
                        for doc in brand_docs:
                            client_context += f"- {doc.get('content', '')[:200]}...\n"
                except Exception as e:
                    logger.warning(f"Could not fetch client documents: {e}")
                    client_context = f"\nClient: {request.clientName}\n"
            
            # Calculate end date
            end_date = start_date + timedelta(weeks=request.durationWeeks)
            
            # Generate content for each platform
            for platform in request.platforms:
                if platform == 'email':
                    # Distribute emails evenly across the duration
                    if request.emailCount > 0:
                        email_interval = (request.durationWeeks * 7) / request.emailCount
                        for i in range(request.emailCount):
                            # Schedule emails on optimal days (Tuesday/Thursday)
                            email_date = start_date + timedelta(days=int(i * email_interval))
                            # Adjust to next Tuesday or Thursday
                            while email_date.weekday() not in [1, 3]:  # Tuesday or Thursday
                                email_date += timedelta(days=1)
                            
                            # Pick a topic cyclically
                            topic = request.topics[i % len(request.topics)]
                            
                            # Generate email content
                            prompt = f"""Create an email campaign for {request.clientName or 'nBrain'} about: {topic}
{client_context}
Guidelines:
- Professional tone for agency owners
- Include compelling subject line
- Preview text (50-100 chars)
- Main content (200-300 words)
- Clear call-to-action
- Format: Subject: [subject]\nPreview: [preview]\n\n[content]
- If client context is provided, match their brand voice and style"""
                            
                            response = model.generate_content(prompt)
                            content = response.text.strip()
                            
                            post = SocialMediaPost(
                                platform=SocialPlatform.EMAIL,
                                content=content,
                                scheduled_date=email_date.replace(hour=9, minute=0),
                                status=PostStatus.SCHEDULED,
                                created_by=current_user.id,
                                client_id=request.clientId,
                                campaign_name="Bulk Generated Campaign"
                            )
                            db.add(post)
                            posts_created.append(post)
                
                else:
                    # Social media posts - follow best practices for each platform
                    current = start_date
                    topic_index = 0
                    
                    while current < end_date:
                        should_post = False
                        post_time = None
                        
                        if platform == 'linkedin' and current.weekday() in [1, 3]:  # Tue, Thu
                            should_post = True
                            post_time = current.replace(hour=10, minute=0)
                        elif platform == 'twitter' and current.weekday() in [0, 2, 4]:  # Mon, Wed, Fri
                            # Vary posting times for Twitter
                            hour = [9, 14, 18][topic_index % 3]
                            should_post = True
                            post_time = current.replace(hour=hour, minute=0)
                        elif platform == 'facebook' and current.weekday() in [2, 5, 6]:  # Wed, Sat, Sun
                            should_post = True
                            post_time = current.replace(hour=19 if current.weekday() == 2 else 14, minute=0)
                        
                        if should_post and post_time:
                            topic = request.topics[topic_index % len(request.topics)]
                            topic_index += 1
                            
                            # Generate content using AI
                            prompt = f"""Create a {platform} post for {request.clientName or 'nBrain'} about: {topic}
{client_context}
Guidelines:
- For LinkedIn: Professional, insightful, thought leadership. 500-700 characters.
- For Twitter: Concise, engaging, with hashtags. Max 280 characters.
- For Facebook: Conversational, engaging, with emojis. 300-500 characters.

Write in first person as {request.clientName or 'nBrain'}. Include relevant hashtags.
If client context is provided, match their brand voice and style."""
                            
                            response = model.generate_content(prompt)
                            content = response.text.strip()
                            
                            # Clean up any platform labels from the response
                            for label in ['LinkedIn:', 'Twitter:', 'Facebook:', 'Post:']:
                                content = content.replace(label, '').strip()
                            
                            post = SocialMediaPost(
                                platform=SocialPlatform[platform.upper()],
                                content=content,
                                scheduled_date=post_time,
                                status=PostStatus.SCHEDULED,
                                created_by=current_user.id,
                                client_id=request.clientId,
                                campaign_name="Bulk Generated Campaign"
                            )
                            db.add(post)
                            posts_created.append(post)
                        
                        current += timedelta(days=1)
            
            db.commit()
            
            return {
                "success": True,
                "posts_created": len(posts_created),
                "message": f"Successfully created {len(posts_created)} posts across {len(request.platforms)} platforms"
            }
            
        except Exception as e:
            logger.error(f"Error generating bulk content: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) 