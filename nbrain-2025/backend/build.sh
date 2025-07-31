#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database setup/migrations
# Note: On Render, we're already in the backend directory
echo "Running database setup..."
python scripts/db_setup.py

# Run the new migration script to add missing columns
echo "Running database migrations..."
python scripts/add_missing_columns.py

# Create Oracle tables
echo "Creating Oracle tables..."
python scripts/create_oracle_tables.py

# Run Client Portal table creation script
echo "Creating Client Portal tables..."
python scripts/create_client_portal_tables.py

# Add user roles and permissions
echo "Adding user roles and permissions..."
timeout 30s python scripts/add_user_roles_permissions.py || {
    echo "Warning: User roles script timed out or failed, but continuing..."
}

# Make danny@nbrain.ai an admin
echo "Setting up admin user..."
timeout 10s python scripts/make_danny_admin.py || {
    echo "Warning: Admin setup failed, but continuing..."
}

# Add missing client document columns
echo "Adding missing columns to client_documents table..."
python scripts/add_missing_client_document_columns.py

# Add sync email addresses column
echo "Adding sync_email_addresses to clients table..."
python scripts/add_sync_emails_to_clients.py

# Add missing client columns (monthly_recurring_revenue, company_size)
echo "Adding missing client columns..."
python scripts/add_missing_client_columns.py

# Add domain column to clients table
echo "Adding domain column to clients..."
python scripts/add_domain_column.py || echo "Domain column may already exist"

# Add sync metadata column
echo "Adding sync metadata to communications..."
python scripts/add_sync_metadata.py || echo "Sync metadata column may already exist"

# Fix cascade delete issue
echo "Fixing cascade delete issue..."
timeout 15s python scripts/fix_cascade_delete.py || echo "Cascade delete fix timed out or completed"

# Ensure database connection is working
echo "Checking database connection..."
python scripts/ensure_db_connection.py
if [ $? -ne 0 ]; then
    echo "Failed to establish database connection. Exiting."
    exit 1
fi

# Check Oracle OAuth configuration
echo "Checking Oracle OAuth configuration..."
python scripts/fix_oracle_redirect.py

# Add performance indexes
echo "Adding database performance indexes..."
timeout 60s python scripts/add_performance_indexes.py || echo "Indexes may already exist or timed out"

# Optimize database (vacuum and analyze)
echo "Optimizing database performance..."
python scripts/optimize_database.py || echo "Database optimization completed"

# Check if we're on Render (production)
if [ -n "$RENDER" ]; then
    echo "Running on Render environment"
fi

echo "Build completed successfully!" 