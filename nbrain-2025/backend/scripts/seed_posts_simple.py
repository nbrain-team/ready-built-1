#!/usr/bin/env python3
"""
Simple seed script for Marketing Calendar using raw SQL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create engine
engine = create_engine(DATABASE_URL)

# Get current date info
now = datetime.now()
current_year = now.year
current_month = now.month

def seed_posts():
    """Seed posts using raw SQL to avoid ORM issues"""
    
    with engine.connect() as conn:
        # First, get a user ID
        result = conn.execute(text("SELECT id FROM users LIMIT 1"))
        user = result.fetchone()
        
        if not user:
            logger.error("No users found. Please create a user first.")
            return
            
        user_id = user[0]
        logger.info(f"Using user ID {user_id} as creator")
        
        # Delete existing posts for current month to avoid duplicates
        conn.execute(
            text("""
                DELETE FROM social_media_posts 
                WHERE EXTRACT(MONTH FROM scheduled_date) = :month 
                AND EXTRACT(YEAR FROM scheduled_date) = :year
            """),
            {"month": current_month, "year": current_year}
        )
        conn.commit()
        
        # Generate posts for the next 14 days
        posts_added = 0
        start_date = now + timedelta(days=1)
        
        for i in range(14):
            post_date = start_date + timedelta(days=i)
            
            # Skip if we've gone into next month
            if post_date.month != current_month:
                break
            
            # Create different posts for different days
            if i % 4 == 0:  # LinkedIn
                conn.execute(
                    text("""
                        INSERT INTO social_media_posts 
                        (platform, content, scheduled_date, status, created_by, created_at, updated_at)
                        VALUES (:platform, :content, :scheduled_date, :status, :created_by, NOW(), NOW())
                    """),
                    {
                        "platform": "linkedin",
                        "content": f"🚀 AI Insight #{i+1}: Agencies using AI report {20+i}% productivity gains. What's your experience with AI automation? Share below! #AgencyAI #Productivity",
                        "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 10, 0),
                        "status": "scheduled",
                        "created_by": user_id
                    }
                )
                posts_added += 1
                
            elif i % 4 == 1:  # Twitter
                conn.execute(
                    text("""
                        INSERT INTO social_media_posts 
                        (platform, content, scheduled_date, status, created_by, created_at, updated_at)
                        VALUES (:platform, :content, :scheduled_date, :status, :created_by, NOW(), NOW())
                    """),
                    {
                        "platform": "twitter",
                        "content": f"💡 Quick tip: Automate repetitive tasks with AI and save {3+i} hours/week! What would you do with the extra time? #AgencyLife #AI",
                        "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 14, 0),
                        "status": "scheduled",
                        "created_by": user_id
                    }
                )
                posts_added += 1
                
            elif i % 4 == 2:  # Facebook
                conn.execute(
                    text("""
                        INSERT INTO social_media_posts 
                        (platform, content, scheduled_date, status, created_by, created_at, updated_at)
                        VALUES (:platform, :content, :scheduled_date, :status, :created_by, NOW(), NOW())
                    """),
                    {
                        "platform": "facebook",
                        "content": f"🎯 Success Story: Our client increased efficiency by {30+i}% using our AI tools! Read the full case study in the comments 👇 #ClientSuccess #AI",
                        "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 11, 0),
                        "status": "scheduled",
                        "created_by": user_id
                    }
                )
                posts_added += 1
                
            else:  # Email
                conn.execute(
                    text("""
                        INSERT INTO social_media_posts 
                        (platform, content, scheduled_date, status, created_by, created_at, updated_at)
                        VALUES (:platform, :content, :scheduled_date, :status, :created_by, NOW(), NOW())
                    """),
                    {
                        "platform": "email",
                        "content": f"Subject: 🚀 Weekly AI Tips #{(i//4)+1}\n\nDiscover how leading agencies are using AI to transform their operations...",
                        "scheduled_date": datetime(post_date.year, post_date.month, post_date.day, 9, 0),
                        "status": "scheduled",
                        "created_by": user_id
                    }
                )
                posts_added += 1
        
        conn.commit()
        
        # Get summary
        result = conn.execute(
            text("""
                SELECT COUNT(*) FROM social_media_posts 
                WHERE EXTRACT(MONTH FROM scheduled_date) = :month 
                AND EXTRACT(YEAR FROM scheduled_date) = :year
            """),
            {"month": current_month, "year": current_year}
        )
        total = result.fetchone()[0]
        
        logger.info(f"\n✅ Successfully added {posts_added} posts!")
        logger.info(f"📅 Total posts for {now.strftime('%B %Y')}: {total}")

if __name__ == "__main__":
    try:
        seed_posts()
        print("\n✨ Marketing calendar seeded successfully!")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1) 