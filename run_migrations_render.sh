#!/bin/bash

# Script to run database migrations on Render
# This creates the new salon tables

echo "=== Running Salon Table Migrations on Render ==="
echo

# You'll need to run this in the Render shell
# Steps:
# 1. Go to your Render dashboard
# 2. Click on your backend service
# 3. Go to the "Shell" tab
# 4. Run these commands:

cat << 'EOF'

# First, navigate to the backend directory
cd /opt/render/project/src/nbrain-2025/backend

# Run the table creation script
python create_salon_tables.py

# Verify tables were created
python -c "
from core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
salon_tables = [t for t in tables if 'salon' in t]
print('Salon tables in database:')
for table in sorted(salon_tables):
    print(f'  ✓ {table}')
"

EOF

echo
echo "Copy and paste the commands above into your Render shell."
echo "This will create all the necessary tables for the complete salon data." 