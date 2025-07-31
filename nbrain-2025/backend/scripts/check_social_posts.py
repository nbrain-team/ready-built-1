#!/usr/bin/env python3
"""
Check social media posts in the database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("No DATABASE_URL found in environment")
    sys.exit(1)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'social_media_posts'
            );
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("Table social_media_posts does not exist!")
        else:
            print("Table social_media_posts exists.")
            
            # Get all posts
            result = conn.execute(text("""
                SELECT id, platform, content, scheduled_date, status, created_at 
                FROM social_media_posts 
                ORDER BY scheduled_date DESC
                LIMIT 10;
            """))
            
            posts = result.fetchall()
            print(f"\nFound {len(posts)} posts (showing up to 10):")
            print("-" * 80)
            
            for post in posts:
                print(f"ID: {post[0]}")
                print(f"Platform: {post[1]}")
                print(f"Content: {post[2][:50]}...")
                print(f"Scheduled (UTC): {post[3]}")
                print(f"Scheduled (Local): {post[3].replace(tzinfo=pytz.UTC).astimezone()}")
                print(f"Status: {post[4]}")
                print(f"Created: {post[5]}")
                print("-" * 80)
                
            # Check for posts in current month
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM social_media_posts 
                WHERE EXTRACT(MONTH FROM scheduled_date) = :month
                AND EXTRACT(YEAR FROM scheduled_date) = :year;
            """), {"month": current_month, "year": current_year})
            
            count = result.scalar()
            print(f"\nPosts in {current_month}/{current_year}: {count}")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    engine.dispose() 