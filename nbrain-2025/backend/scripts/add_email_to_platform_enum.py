#!/usr/bin/env python3
"""
Add email to socialplatform enum
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("No DATABASE_URL found in environment")
    sys.exit(1)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        logger.info("Adding 'email' to socialplatform enum...")
        
        # PostgreSQL requires this to add a value to an existing enum
        conn.execute(text("""
            ALTER TYPE socialplatform ADD VALUE IF NOT EXISTS 'email';
        """))
        
        conn.commit()
        logger.info("Successfully added 'email' to socialplatform enum!")
        
except Exception as e:
    logger.error(f"Error updating enum: {e}")
    # If the value already exists, that's fine
    if "already exists" in str(e):
        logger.info("'email' already exists in socialplatform enum")
    else:
        raise
finally:
    engine.dispose() 