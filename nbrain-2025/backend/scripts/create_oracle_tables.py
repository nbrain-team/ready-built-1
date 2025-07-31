#!/usr/bin/env python3
"""
Create Oracle tables in the database
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from core.database import Base
from core.oracle_handler import OracleDataSource, OracleActionItem, OracleInsight

def create_oracle_tables():
    """Create the Oracle-related tables in the database"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Create tables
        print("Creating Oracle tables...")
        
        # Import the models to ensure they're registered with Base
        from core.oracle_handler import OracleDataSource, OracleActionItem, OracleInsight
        
        # Create only the Oracle tables
        Base.metadata.create_all(engine, tables=[
            OracleDataSource.__table__,
            OracleActionItem.__table__,
            OracleInsight.__table__
        ])
        
        print("✅ Oracle tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('oracle_data_sources', 'oracle_action_items', 'oracle_insights')
                ORDER BY table_name;
            """))
            
            print("\nCreated tables:")
            for row in result:
                print(f"  - {row[0]}")
                
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_oracle_tables() 