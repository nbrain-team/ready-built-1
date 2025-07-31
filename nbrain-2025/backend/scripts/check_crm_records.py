#!/usr/bin/env python3
"""
Check CRM records in the database
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("No DATABASE_URL found in environment")
    sys.exit(1)

# Convert postgresql:// to postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    if "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

def main():
    """Check CRM records"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("Connected to database successfully\n")
            
            # Count total records
            result = conn.execute(text("SELECT COUNT(*) FROM crm_opportunities"))
            count = result.scalar()
            print(f"Total CRM opportunities in database: {count}")
            
            if count > 0:
                # Show sample records
                print("\nSample records:")
                result = conn.execute(text("""
                    SELECT id, client_opportunity, lead_status, deal_status, 
                           contact_name, created_at, status
                    FROM crm_opportunities 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                
                for row in result:
                    print(f"\nID: {row[0]}")
                    print(f"Company: {row[1]}")
                    print(f"Lead Status: {row[2]}")
                    print(f"Deal Status: {row[3]}")
                    print(f"Contact: {row[4]}")
                    print(f"Created: {row[5]}")
                    print(f"Status: {row[6]}")
                
                # Check for any records with missing required fields
                print("\n\nChecking for records with missing required fields...")
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM crm_opportunities 
                    WHERE status IS NULL OR client_opportunity IS NULL
                """))
                missing_count = result.scalar()
                
                if missing_count > 0:
                    print(f"WARNING: Found {missing_count} records with missing required fields!")
                    
                    # Fix missing status field
                    print("\nFixing missing status fields...")
                    conn.execute(text("""
                        UPDATE crm_opportunities 
                        SET status = 'Active' 
                        WHERE status IS NULL
                    """))
                    conn.commit()
                    print("Fixed missing status fields")
                else:
                    print("All records have required fields ✓")
                    
                # Check column existence
                print("\n\nChecking database schema...")
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'crm_opportunities'
                    ORDER BY ordinal_position
                """))
                
                columns = [row[0] for row in result]
                print(f"Total columns: {len(columns)}")
                print("Columns:", ', '.join(columns))
                
            else:
                print("\nNo CRM records found in database.")
                print("This could mean:")
                print("1. The records were deleted")
                print("2. You're connected to a different database")
                print("3. The table was recreated")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 