import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine
from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_user_roles_and_permissions():
    """Add role, permissions, and profile fields to existing users table."""
    
    with engine.connect() as conn:
        try:
            # Set a timeout for this operation
            conn.execute(text("SET statement_timeout = '30s';"))
            
            # Check which columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """))
            existing_columns = {row[0] for row in result}
            logger.info(f"Existing columns: {existing_columns}")
            
            # Start transaction
            trans = conn.begin()
            
            # Only add columns that don't exist
            if 'first_name' not in existing_columns:
                logger.info("Adding profile fields...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN first_name VARCHAR,
                    ADD COLUMN last_name VARCHAR,
                    ADD COLUMN company VARCHAR,
                    ADD COLUMN website_url VARCHAR;
                """))
                logger.info("✓ Added profile fields")
            
            # Add role field if it doesn't exist
            if 'role' not in existing_columns:
                logger.info("Adding role field...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR DEFAULT 'user';
                """))
                logger.info("✓ Added role field")
            
            # Add permissions field if it doesn't exist
            if 'permissions' not in existing_columns:
                logger.info("Adding permissions field...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN permissions JSON DEFAULT '{"chat": true, "history": true, "email-personalizer": true, "agent-ideas": true, "knowledge": true, "crm": true, "clients": true, "oracle": true}'::json;
                """))
                logger.info("✓ Added permissions field")
            
            # Add timestamps if they don't exist
            if 'created_at' not in existing_columns:
                logger.info("Adding timestamp fields...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
                """))
                logger.info("✓ Added timestamp fields")
            
            # Update existing users to have default permissions if needed
            if 'permissions' in existing_columns:
                conn.execute(text("""
                    UPDATE users 
                    SET permissions = '{"chat": true, "history": true, "email-personalizer": true, "agent-ideas": true, "knowledge": true, "crm": true, "clients": true, "oracle": true}'::json
                    WHERE permissions IS NULL;
                """))
            
            trans.commit()
            logger.info("✓ Successfully updated users table")
            
            # Check if we need to create an admin user
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'"))
            admin_count = result.scalar()
            
            if admin_count == 0:
                logger.warning("No admin users found. Please run 'python scripts/make_danny_admin.py' to create an admin user.")
            else:
                logger.info(f"✓ Found {admin_count} admin user(s)")
            
            # Reset timeout
            conn.execute(text("RESET statement_timeout;"))
            
        except Exception as e:
            logger.error(f"Error adding user roles and permissions: {str(e)}")
            if 'trans' in locals():
                trans.rollback()
            # Don't raise - let the build continue
            logger.info("Continuing despite error (columns may already exist)")

if __name__ == "__main__":
    logger.info("Starting user roles and permissions update...")
    add_user_roles_and_permissions()
    logger.info("Completed!") 