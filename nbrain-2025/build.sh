#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database setup
echo "Setting up database..."
cd backend
python -c "from core.database import init_db; init_db()"

# Run Oracle migrations
echo "Running Oracle migrations..."
python ../database/migrations/create_oracle_tables.py
python ../database/migrations/fix_oracle_tables.py
psql $DATABASE_URL -f ../database/migrations/add_oracle_emails_deleted_flag.sql
psql $DATABASE_URL -f ../database/migrations/add_oracle_emails_unique_constraint.sql
cd ..

# Collect static files if needed (for future use)
# python manage.py collectstatic --no-input 