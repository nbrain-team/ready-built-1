#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade || echo "No migrations to run"

# Create initial database tables if needed
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
" || echo "Database tables already exist" 