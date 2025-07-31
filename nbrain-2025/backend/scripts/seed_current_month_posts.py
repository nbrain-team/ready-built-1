#!/usr/bin/env python3
"""
Seed Marketing Calendar with posts for the current month
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import SessionLocal, User
from core.social_media_models import SocialMediaPost, PostStatus, SocialPlatform
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get current date info
now = datetime.now()
current_year = now.year
current_month = now.month

# Sample posts for the current month - dynamically generated for the rest of the month
def generate_current_month_posts():
    posts = []
    
    # Start from tomorrow
    start_date = now + timedelta(days=1)
    
    # Generate posts for the next 10 days
    for i in range(10):
        post_date = start_date + timedelta(days=i)
        
        # Skip if we've gone into the next month
        if post_date.month != current_month:
            break
            
        # Rotate through different platforms and content types
        if i % 4 == 0:
            posts.append({
                "platform": "linkedin",
                "content": f"🚀 AI Insight of the Day: Did you know that agencies using AI save an average of {15 + i}% on operational costs? Here's how you can too... #AgencyAI #Productivity",
                "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 10, 0),
                "status": "scheduled",
                "campaign": f"{post_date.strftime('%B')} Campaign"
            })
        elif i % 4 == 1:
            posts.append({
                "platform": "facebook",
                "content": f"💡 Quick tip #{i+1}: Automate your client reporting with AI! Our users report saving {3 + i} hours per week. What would you do with that extra time? 🤔",
                "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 14, 0),
                "status": "scheduled",
                "campaign": f"{post_date.strftime('%B')} Campaign"
            })
        elif i % 4 == 2:
            posts.append({
                "platform": "twitter",
                "content": f"🎯 Agency hack #{i+1}: Use AI to predict client churn before it happens. Prevention is better than cure! #AgencyTips #AI",
                "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 12, 0),
                "status": "scheduled",
                "campaign": f"{post_date.strftime('%B')} Campaign"
            })
        else:
            posts.append({
                "platform": "email",
                "content": f"Subject: 🚀 Your Weekly AI Insights #{i//4 + 1}\n\nDear Agency Partner,\n\nThis week's focus: How to leverage AI for better client retention...",
                "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 9, 0),
                "status": "scheduled",
                "campaign": "Email Campaign"
            })
    
    # Add some special posts for the end of the month
    end_of_month = datetime(current_year, current_month, 25, 10, 0)
    if end_of_month > now:
        posts.extend([
            {
                "platform": "linkedin",
                "content": f"📊 {now.strftime('%B')} Recap: Amazing month for AI in agencies! Here are the top 5 trends we've seen... #MonthlyRecap #AgencyAI",
                "scheduled_date": end_of_month,
                "status": "scheduled",
                "campaign": "Monthly Recap"
            },
            {
                "platform": "email",
                "content": f"Subject: 🎉 {now.strftime('%B')} Special - 30% off Premium Features!\n\nLimited time offer for agencies ready to scale with AI...",
                "scheduled_date": datetime(current_year, current_month, 26, 11, 0),
                "status": "scheduled",
                "campaign": "Promotional"
            }
        ])
    
    return posts

def seed_current_month():
    """Seed the marketing calendar with posts for the current month"""
    
    db = SessionLocal()
    
    try:
        # Get the first user to assign as creator
        user = db.query(User).first()
        if not user:
            logger.error("No users found in database. Please create a user first.")
            return
        
        logger.info(f"Using user {user.email} as content creator")
        logger.info(f"Creating posts for {now.strftime('%B %Y')}")
        
        # Generate posts for current month
        posts_to_add = generate_current_month_posts()
        
        # Add posts
        added_count = 0
        for post_data in posts_to_add:
            post = SocialMediaPost(
                platform=SocialPlatform[post_data['platform'].upper()],
                content=post_data['content'],
                scheduled_date=post_data['scheduled_date'],
                published_date=None,
                status=PostStatus[post_data['status'].upper()],
                created_by=user.id,
                campaign_name=post_data.get('campaign', 'Current Month Campaign')
            )
            db.add(post)
            added_count += 1
            logger.info(f"Added {post_data['platform']} post for {post_data['scheduled_date'].strftime('%B %d at %I:%M %p')}")
        
        db.commit()
        logger.info(f"Successfully added {added_count} posts for {now.strftime('%B %Y')}!")
        
        # Show summary
        total_posts = db.query(SocialMediaPost).count()
        current_month_posts = db.query(SocialMediaPost).filter(
            db.func.extract('month', SocialMediaPost.scheduled_date) == current_month,
            db.func.extract('year', SocialMediaPost.scheduled_date) == current_year
        ).count()
        
        logger.info(f"\nCalendar Summary:")
        logger.info(f"Total posts in database: {total_posts}")
        logger.info(f"Posts in {now.strftime('%B %Y')}: {current_month_posts}")
        
    except Exception as e:
        logger.error(f"Error seeding calendar: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_current_month() 