"""
Video processing using Cloudinary - cloud-based solution for reliable video processing
"""
import logging
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..database import SessionLocal
from . import models
from core import llm_handler

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


async def process_campaign(
    campaign_id: str,
    video_path: str,
    platforms: List[str],
    duration_weeks: int,
    client_id: str
):
    """Process a video campaign using Cloudinary"""
    logger.info(f"Starting Cloudinary video processing for campaign: {campaign_id}")
    
    with SessionLocal() as db:
        try:
            # Update campaign status
            campaign = db.query(models.Campaign).filter(
                models.Campaign.id == campaign_id
            ).first()
            
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            logger.info(f"Setting campaign {campaign_id} to PROCESSING status")
            campaign.status = models.CampaignStatus.PROCESSING
            campaign.progress = 10
            db.commit()
            logger.info(f"Campaign {campaign_id} progress set to 10%")
            
            # Upload video to Cloudinary
            logger.info(f"Uploading video to Cloudinary from path: {video_path}")
            try:
                upload_result = cloudinary.uploader.upload_large(
                    video_path,
                    resource_type="video",
                    public_id=f"campaigns/{campaign_id}/main_video",
                    overwrite=True
                )
                
                video_url = upload_result['secure_url']
                duration = upload_result.get('duration', 90)  # Video duration in seconds
                logger.info(f"Video uploaded successfully. URL: {video_url}, Duration: {duration}s")
            except Exception as e:
                logger.error(f"Failed to upload video to Cloudinary: {str(e)}")
                campaign.status = models.CampaignStatus.FAILED
                campaign.error_message = f"Video upload failed: {str(e)}"
                db.commit()
                raise
            
            # Generate clips using Cloudinary transformations
            clips = []
            clip_duration = 30  # 30-second clips
            num_clips = min(3, int(duration / clip_duration))
            
            for i in range(num_clips):
                # Check if campaign was cancelled/deleted
                db.refresh(campaign)
                if campaign.status == models.CampaignStatus.FAILED and campaign.error_message == "Cancelled by user":
                    logger.info(f"Campaign {campaign_id} was cancelled, stopping processing")
                    return
                
                start_time = i * clip_duration
                end_time = min(start_time + clip_duration, duration)
                
                # Generate clip URL using Cloudinary transformations
                clip_public_id = f"campaigns/{campaign_id}/clip_{i+1}"
                
                # Create clip transformation
                clip_url, _ = cloudinary_url(
                    upload_result['public_id'],
                    resource_type="video",
                    transformation=[
                        {'start_offset': start_time, 'end_offset': end_time},
                        {'quality': 'auto', 'fetch_format': 'mp4'}
                    ]
                )
                
                # Generate thumbnail at middle of clip
                thumbnail_time = start_time + (end_time - start_time) / 2
                thumbnail_url, _ = cloudinary_url(
                    upload_result['public_id'],
                    resource_type="video",
                    transformation=[
                        {'start_offset': thumbnail_time},
                        {'width': 640, 'height': 360, 'crop': 'fill'},
                        {'quality': 'auto', 'fetch_format': 'jpg'}
                    ]
                )
                
                # Create database entry
                db_clip = models.VideoClip(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    title=f"Clip {i+1}",
                    description=f"Segment {i+1} from video",
                    duration=end_time - start_time,
                    start_time=start_time,
                    end_time=end_time,
                    video_url=clip_url,
                    thumbnail_url=thumbnail_url,
                    content_type="general",
                    suggested_caption=f"Check out this amazing content!",
                    suggested_hashtags=["#video", "#content", "#socialmedia"]
                )
                db.add(db_clip)
                clips.append(db_clip)
                
                # Update progress
                campaign.progress = 30 + (i + 1) * 20
                db.commit()
            
            logger.info(f"Created {len(clips)} video clips")
            
            # Analyze video content and generate AI captions
            await analyze_and_generate_captions(clips, platforms, duration_weeks, client_id, campaign, db, upload_result)
            
            # Update campaign status
            campaign.status = models.CampaignStatus.READY
            campaign.progress = 100
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing campaign: {str(e)}", exc_info=True)
            campaign.status = models.CampaignStatus.FAILED
            campaign.error_message = str(e)
            db.commit()
            raise


async def analyze_and_generate_captions(clips, platforms, duration_weeks, client_id, campaign, db, cloudinary_upload):
    """Analyze video content and generate contextual AI-powered captions"""
    import base64
    
    # Get video metadata for context
    video_context = f"""
Video Title: {campaign.name}
Duration: {cloudinary_upload.get('duration', 0)} seconds
Platforms: {', '.join(platforms)}
"""
    
    for i, db_clip in enumerate(clips):
        try:
            # Extract a frame from the middle of the clip for analysis
            frame_time = db_clip.start_time + (db_clip.duration / 2)
            
            # Generate a frame URL using Cloudinary transformation
            frame_url, _ = cloudinary_url(
                cloudinary_upload['public_id'],
                resource_type="video",
                transformation=[
                    {'start_offset': frame_time},
                    {'width': 800, 'height': 450, 'crop': 'fill'},
                    {'quality': 'auto', 'fetch_format': 'jpg'}
                ]
            )
            
            # Download and encode the frame for vision analysis
            response = requests.get(frame_url)
            if response.status_code == 200:
                frame_base64 = base64.b64encode(response.content).decode('utf-8')
                
                # Use vision-capable LLM to analyze the frame
                vision_prompt = f"""Analyze this video frame and describe what's happening in the scene. 
Focus on:
- Main subjects or people
- Actions taking place  
- Setting/location
- Key objects or details
- Overall mood/tone

This is frame from timestamp {frame_time:.1f}s of a video titled "{campaign.name}"."""
                
                try:
                    # Get frame analysis from vision model
                    frame_description = await llm_handler.analyze_image(frame_base64, vision_prompt)
                    logger.info(f"Frame analysis for clip {i+1}: {frame_description[:100]}...")
                except:
                    frame_description = f"Clip showing content from {db_clip.start_time:.0f}s to {db_clip.end_time:.0f}s"
            else:
                frame_description = f"Video segment {i+1}"
                
        except Exception as e:
            logger.warning(f"Could not analyze frame for clip {i+1}: {str(e)}")
            frame_description = f"Video segment {i+1}"
        
        # Generate contextual caption based on actual content
        prompt = f"""Generate an engaging social media caption for this specific video clip.

CONTEXT:
{video_context}

WHAT'S IN THIS CLIP:
{frame_description}

Clip timing: {db_clip.start_time:.0f}s - {db_clip.end_time:.0f}s (clip {i+1} of {len(clips)})

Create a caption that:
- Directly relates to what's shown in this specific clip
- Uses natural, conversational language
- Includes 2-3 relevant emojis
- Has a clear call to action
- Ends with 5-7 hashtags relevant to the content
- Stays under 280 characters for Twitter

Caption:"""
        
        try:
            caption = await llm_handler.generate_text(prompt)
            db_clip.suggested_caption = caption
            
            # Extract hashtags
            import re
            hashtags = re.findall(r'#\w+', caption)
            db_clip.suggested_hashtags = hashtags[:10]
            
            # Update clip with content description
            db_clip.description = frame_description[:200]  # Store abbreviated description
            
        except Exception as e:
            logger.error(f"Error generating caption for clip {i+1}: {str(e)}")
            # Fallback caption
            db_clip.suggested_caption = f"🎬 {campaign.name} - Part {i+1} 🔥\n\nDon't miss this moment!\n\n#VideoContent #SocialMedia #MustWatch"
            db_clip.suggested_hashtags = ["#video", "#content", "#socialmedia", "#viral", "#trending"]
    
    db.commit()
    
    # Create social posts schedule
    start_date = datetime.utcnow() + timedelta(days=1)
    posts_per_week = max(1, len(clips) // duration_weeks)
    
    current_date = start_date
    for i, clip in enumerate(clips):
        post = models.SocialPost(
            id=str(uuid.uuid4()),
            client_id=client_id,
            campaign_id=campaign.id,
            video_clip_id=clip.id,
            content=clip.suggested_caption,
            platforms=platforms,
            scheduled_time=current_date,
            status=models.PostStatus.SCHEDULED
        )
        db.add(post)
        
        # Schedule next post 2-3 days later
        current_date += timedelta(days=2 if i % 2 == 0 else 3)
    
    db.commit()
    logger.info(f"Created {len(clips)} scheduled posts") 