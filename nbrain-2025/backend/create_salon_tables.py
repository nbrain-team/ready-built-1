#!/usr/bin/env python3
"""
Create salon analytics tables in the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import engine, Base
from core.salon_models import (
    SalonLocation, SalonStaff, StaffPerformance, SalonClient,
    SalonAppointment, StaffPrediction, SalonAnalytics,
    SalonTransaction, SalonTimeClockEntry, SalonScheduleRecord
)

def create_tables():
    """Create all salon-related tables"""
    print("Creating salon analytics tables...")
    
    # Import all models to ensure they're registered with Base
    tables_to_create = [
        SalonLocation.__table__,
        SalonStaff.__table__,
        StaffPerformance.__table__,
        SalonClient.__table__,
        SalonAppointment.__table__,
        StaffPrediction.__table__,
        SalonAnalytics.__table__,
        SalonTransaction.__table__,
        SalonTimeClockEntry.__table__,
        SalonScheduleRecord.__table__
    ]
    
    # Create tables
    Base.metadata.create_all(bind=engine, tables=[table for table in tables_to_create])
    
    print("✓ Salon analytics tables created successfully!")
    print("\nCreated tables:")
    for table in tables_to_create:
        print(f"  - {table.name}")

if __name__ == "__main__":
    create_tables() 