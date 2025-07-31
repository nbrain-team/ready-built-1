from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import os
import shutil
import asyncio

from ..database import get_db, User
from ..auth import get_current_active_user
from . import models, schemas, services

router = APIRouter(tags=["ad-traffic"])


# Client endpoints
@router.get("/clients", response_model=List[schemas.Client])
async def get_clients(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all clients for the current user"""
    return services.get_user_clients(db, current_user.id)


@router.post("/clients", response_model=schemas.Client)
async def create_client(
    client: schemas.ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new client"""
    return services.create_client(db, client, current_user.id)


@router.get("/clients/{client_id}", response_model=schemas.Client)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific client"""
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/clients/{client_id}", response_model=schemas.Client)
async def update_client(
    client_id: str,
    client_update: schemas.ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a client"""
    client = services.update_client(db, client_id, client_update, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a client"""
    if not services.delete_client(db, client_id, current_user.id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}


# Post endpoints
@router.get("/clients/{client_id}/calendar", response_model=List[schemas.SocialPost])
async def get_client_posts(
    client_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all posts for a client within date range"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    posts = services.get_client_posts(db, client_id, start_date, end_date)
    
    # Add campaign names to posts
    for post in posts:
        if post.campaign_id:
            campaign = db.query(models.Campaign).filter_by(id=post.campaign_id).first()
            if campaign:
                post.campaign_name = campaign.name
    
    return posts


@router.post("/clients/{client_id}/posts", response_model=schemas.SocialPost)
async def create_post(
    client_id: str,
    post: schemas.PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new post for a client"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return services.create_post(db, post, client_id)


@router.put("/posts/{post_id}", response_model=schemas.SocialPost)
async def update_post(
    post_id: str,
    post_update: schemas.PostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a post"""
    post = services.update_post(db, post_id, post_update, current_user.id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a post"""
    if not services.delete_post(db, post_id, current_user.id):
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}


# Campaign endpoints
@router.get("/clients/{client_id}/campaigns", response_model=List[schemas.Campaign])
async def get_client_campaigns(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns for a client"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    campaigns = services.get_client_campaigns(db, client_id)
    return campaigns

@router.post("/clients/{client_id}/campaigns")
async def create_campaign(
    client_id: str,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    duration_weeks: int = Form(...),
    platforms: List[str] = Form(...),
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new video campaign"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== CAMPAIGN CREATION STARTED ===")
    logger.info(f"Client ID: {client_id}")
    logger.info(f"Campaign name: {name}")
    logger.info(f"Duration: {duration_weeks} weeks")
    logger.info(f"Platforms: {platforms}")
    logger.info(f"Video filename: {video.filename}")
    logger.info(f"Video content type: {video.content_type}")
    
    try:
        # Verify client ownership
        client = services.get_client(db, client_id, current_user.id)
        if not client:
            logger.error(f"Client {client_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate video file
        if not video.content_type.startswith("video/"):
            logger.error(f"Invalid video content type: {video.content_type}")
            raise HTTPException(status_code=400, detail="Invalid video file")
    except Exception as e:
        logger.error(f"Error during campaign validation: {str(e)}")
        raise
    
    # Save video file
    # Make sure we're saving to the backend/uploads directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_dir, "uploads", "campaigns", client_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(video.filename)[1]
    video_filename = f"{uuid.uuid4()}{file_extension}"
    video_path = os.path.join(upload_dir, video_filename)
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    # Store the relative path for URL generation
    relative_video_path = f"uploads/campaigns/{client_id}/{video_filename}"
    
    # Create campaign
    campaign_data = schemas.CampaignCreate(
        name=name,
        duration_weeks=duration_weeks,
        platforms=[schemas.Platform(p) for p in platforms]
    )
    
    campaign = services.create_campaign(db, campaign_data, client_id, relative_video_path)
    
    # Import logging
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Created campaign {campaign.id} for client {client_id}")
    logger.info(f"Video saved to: {video_path}")
    logger.info(f"File exists: {os.path.exists(video_path)}")
    logger.info(f"File size: {os.path.getsize(video_path) if os.path.exists(video_path) else 'N/A'}")
    
    # Start background processing
    # Don't pass the db session to background task - it will create its own
    logger.info(f"Adding background task for campaign {campaign.id}")
    
    # Check if we should process inline (for debugging/testing)
    process_inline = os.getenv('PROCESS_VIDEO_INLINE', 'false').lower() == 'true'
    
    if process_inline:
        logger.info("Processing video inline (not in background)")
        # Import asyncio to run the async function
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(services.process_campaign_video(
            campaign.id,
            video_path,
            client.id
        ))
    else:
        background_tasks.add_task(
            services.process_campaign_video,
            campaign.id,
            video_path,  # Pass full path instead of relative path
            client.id  # Pass client_id instead of client object
        )
        logger.info("Background task added successfully")
    
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=schemas.CampaignWithClips)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get campaign with its video clips"""
    campaign = services.get_campaign_with_clips(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.get("/campaigns/{campaign_id}/posts", response_model=List[schemas.SocialPost])
def get_campaign_posts(
    campaign_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all posts associated with a campaign"""
    posts = services.get_campaign_posts(db, campaign_id, current_user.id)
    return posts


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign and all associated data, regardless of status"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify campaign ownership
    campaign = services.get_campaign_with_clips(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    logger.info(f"Deleting campaign {campaign_id} with status {campaign.status}")
    
    # If campaign is processing, mark it as cancelled first
    if campaign.status == models.CampaignStatus.PROCESSING:
        campaign.status = models.CampaignStatus.FAILED
        campaign.error_message = "Cancelled by user"
        db.commit()
        logger.info(f"Marked processing campaign {campaign_id} as cancelled")
    
    # Delete associated posts first
    posts_deleted = db.query(models.SocialPost).filter(
        models.SocialPost.campaign_id == campaign_id
    ).delete()
    logger.info(f"Deleted {posts_deleted} posts for campaign {campaign_id}")
    
    # Delete video clips
    clips_deleted = db.query(models.VideoClip).filter(
        models.VideoClip.campaign_id == campaign_id
    ).delete()
    logger.info(f"Deleted {clips_deleted} video clips for campaign {campaign_id}")
    
    # Try to delete the video file if it exists
    try:
        if campaign.original_video_url:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            video_path = os.path.join(backend_dir, campaign.original_video_url)
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Deleted video file: {video_path}")
            
            # Also try to delete the campaign directory
            campaign_dir = os.path.dirname(video_path)
            if os.path.exists(campaign_dir) and os.path.isdir(campaign_dir):
                try:
                    os.rmdir(campaign_dir)  # Only removes if empty
                    logger.info(f"Deleted campaign directory: {campaign_dir}")
                except OSError:
                    pass  # Directory not empty, that's okay
    except Exception as e:
        logger.warning(f"Could not delete video files: {str(e)}")
    
    # Delete the campaign
    db.delete(campaign)
    db.commit()
    
    return {"message": f"Campaign {campaign_id} deleted successfully", "posts_deleted": posts_deleted, "clips_deleted": clips_deleted}


@router.get("/check-video-processor")
async def check_video_processor_status(
    current_user: User = Depends(get_current_active_user)
):
    """Check video processor configuration and status"""
    import os
    
    # Check Cloudinary config
    cloudinary_status = {
        "cloud_name_set": bool(os.getenv('CLOUDINARY_CLOUD_NAME')),
        "api_key_set": bool(os.getenv('CLOUDINARY_API_KEY')),
        "api_secret_set": bool(os.getenv('CLOUDINARY_API_SECRET')),
        "fully_configured": all([
            os.getenv('CLOUDINARY_CLOUD_NAME'),
            os.getenv('CLOUDINARY_API_KEY'),
            os.getenv('CLOUDINARY_API_SECRET')
        ])
    }
    
    # Check available processors
    available_processors = []
    
    try:
        from . import video_processor_cloudinary
        if cloudinary_status["fully_configured"]:
            available_processors.append("Cloudinary (Cloud-based)")
    except ImportError:
        pass
    
    try:
        from . import video_processor_ffmpeg
        available_processors.append("FFmpeg (Local)")
    except ImportError:
        pass
    
    try:
        from . import video_processor
        available_processors.append("MoviePy (Local)")
    except ImportError:
        pass
    
    return {
        "cloudinary_configuration": cloudinary_status,
        "available_processors": available_processors,
        "preferred_processor": available_processors[0] if available_processors else "None available",
        "upload_directory": os.path.exists("uploads"),
        "clips_directory": os.path.exists("uploads/clips")
    }


@router.get("/video-processor-status-public")
async def check_video_processor_status_public():
    """Public endpoint to check video processor configuration"""
    import os
    
    # Check Cloudinary config
    cloudinary_configured = all([
        os.getenv('CLOUDINARY_CLOUD_NAME'),
        os.getenv('CLOUDINARY_API_KEY'),
        os.getenv('CLOUDINARY_API_SECRET')
    ])
    
    # Check available processors
    processors = []
    
    try:
        from . import video_processor_cloudinary
        if cloudinary_configured:
            processors.append("Cloudinary")
    except:
        pass
    
    try:
        from . import video_processor_ffmpeg
        processors.append("FFmpeg")
    except:
        pass
    
    try:
        from . import video_processor
        processors.append("MoviePy")
    except:
        pass
    
    return {
        "status": "ok",
        "cloudinary_configured": cloudinary_configured,
        "available_processors": processors,
        "processor_count": len(processors)
    }


@router.get("/campaigns/{campaign_id}/debug")
async def debug_campaign_status(
    campaign_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check campaign processing status"""
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get video clips count
    clips_count = db.query(models.VideoClip).filter(
        models.VideoClip.campaign_id == campaign_id
    ).count()
    
    # Get posts count
    posts_count = db.query(models.SocialPost).filter(
        models.SocialPost.campaign_id == campaign_id
    ).count()
    
    return {
        "campaign_id": campaign.id,
        "status": campaign.status.value,
        "progress": campaign.progress,
        "error_message": campaign.error_message,
        "created_at": campaign.created_at.isoformat(),
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        "clips_count": clips_count,
        "posts_count": posts_count,
        "original_video_url": campaign.original_video_url
    }


@router.post("/campaigns/{campaign_id}/reprocess")
async def reprocess_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually trigger reprocessing of a campaign"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get campaign
    campaign = db.query(models.Campaign).join(
        models.AdTrafficClient
    ).filter(
        models.Campaign.id == campaign_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Build video path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_path = os.path.join(backend_dir, campaign.original_video_url)
    
    logger.info(f"Reprocessing campaign {campaign_id}")
    logger.info(f"Video path: {video_path}")
    logger.info(f"Video exists: {os.path.exists(video_path)}")
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video file not found at {video_path}")
    
    # Reset campaign status
    campaign.status = models.CampaignStatus.PROCESSING
    campaign.progress = 0
    campaign.error_message = None
    db.commit()
    
    # Get platforms
    platforms = [p.value for p in campaign.platforms]
    
    # Trigger processing
    background_tasks.add_task(
        services.process_campaign_video,
        campaign.id,
        video_path,
        campaign.client_id
    )
    
    return {"message": "Reprocessing started", "campaign_id": campaign_id} 


@router.get("/test-video-processing")
async def test_video_processing(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Test endpoint to verify video processing is working"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("TEST: Video processing test started")
    
    # Create a simple test function
    async def test_task():
        logger.info("TEST: Background task is running!")
        await asyncio.sleep(2)
        logger.info("TEST: Background task completed!")
    
    # Add the task
    background_tasks.add_task(test_task)
    
    return {
        "message": "Test background task added - check logs for 'TEST:' messages",
        "cloudinary_configured": all([
            os.getenv('CLOUDINARY_CLOUD_NAME'),
            os.getenv('CLOUDINARY_API_KEY'),
            os.getenv('CLOUDINARY_API_SECRET')
        ])
    } 