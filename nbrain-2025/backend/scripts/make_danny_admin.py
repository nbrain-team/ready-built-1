import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, User, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_danny_admin():
    """Make danny@nbrain.ai an admin user."""
    
    # Create a new session directly
    db = SessionLocal()
    
    try:
        # Set timeout
        db.execute(text("SET statement_timeout = '10s';"))
        
        # Check if user exists
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        
        if user:
            # Update existing user to admin
            user.role = "admin"
            user.permissions = {
                "chat": True,
                "history": True,
                "email-personalizer": True,
                "agent-ideas": True,
                "knowledge": True,
                "crm": True,
                "clients": True,
                "oracle": True,
                "admin": True
            }
            db.commit()
            logger.info(f"✓ Successfully updated danny@nbrain.ai to admin role!")
            logger.info(f"  User ID: {user.id}")
            logger.info(f"  Status: {'Active' if user.is_active else 'Inactive'}")
        else:
            logger.warning("User danny@nbrain.ai not found in the database.")
            logger.info("User will need to sign up first.")
            
            # Don't list all users in production (privacy)
            user_count = db.query(User).count()
            logger.info(f"Total users in database: {user_count}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting admin: {str(e)}")
        # Don't raise - let the build continue
        logger.info("Continuing build despite error")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Setting danny@nbrain.ai as admin...")
    make_danny_admin()
    logger.info("Admin setup completed!") 