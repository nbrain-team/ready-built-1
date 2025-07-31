"""
Social Media Calendar Models
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from .database import Base

class PostStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class SocialPlatform(enum.Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    EMAIL = "email"

class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(Enum(SocialPlatform, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    content = Column(Text, nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    published_date = Column(DateTime, nullable=True)
    status = Column(Enum(PostStatus, values_callable=lambda obj: [e.value for e in obj]), default=PostStatus.DRAFT)
    
    # Client relationship
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    client = relationship("Client", backref="social_media_posts")
    
    # User who created the post
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", backref="social_media_posts")
    
    # Campaign information
    campaign_name = Column(String, nullable=True)
    
    # Media attachments (URLs to images/videos)
    media_urls = Column(JSON, nullable=True)
    
    # Platform-specific data (hashtags, mentions, etc.)
    platform_data = Column(JSON, nullable=True)
    
    # Analytics data (after publishing)
    analytics_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Error message if posting failed
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SocialMediaPost {self.platform.value} - {self.status.value}>" 