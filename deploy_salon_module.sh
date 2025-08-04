#!/bin/bash

# Salon Analytics Module - Render Deployment Script

echo "🚀 Deploying Salon Analytics Module to Render..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo "❌ render.yaml not found. Please run from project root."
    exit 1
fi

echo -e "${YELLOW}Step 1: Database Migration${NC}"
echo "Run this SQL in your Render PostgreSQL dashboard or via psql:"
echo "----------------------------------------"
cat nbrain-2025/database/migrations/add_salon_tables.sql
echo "----------------------------------------"
echo ""

echo -e "${YELLOW}Step 2: Update Backend Service${NC}"
echo "In Render Dashboard, update your backend service with:"
echo ""
echo "Build Command:"
echo "cd nbrain-2025/backend && pip install -r requirements.txt && python -m scripts.run_migrations"
echo ""
echo "Start Command:"
echo "cd nbrain-2025/backend && uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo ""

echo -e "${YELLOW}Step 3: Update Frontend Service${NC}"
echo "In Render Dashboard, update your frontend service with:"
echo ""
echo "Build Command:"
echo "cd nbrain-2025/frontend && npm install && npm run build"
echo ""
echo "Publish Directory:"
echo "nbrain-2025/frontend/dist"
echo ""

echo -e "${YELLOW}Step 4: Environment Variables${NC}"
echo "Add these to your backend service environment:"
echo "SALON_DATA_PATH=/opt/render/project/src/blazer"
echo "ENABLE_SALON_MODULE=true"
echo ""

echo -e "${YELLOW}Step 5: Manual Deploy${NC}"
echo "1. Go to https://dashboard.render.com"
echo "2. Navigate to your backend service"
echo "3. Click 'Manual Deploy' > 'Deploy latest commit'"
echo "4. Repeat for frontend service"
echo ""

echo -e "${GREEN}✅ Configuration complete!${NC}"
echo ""
echo "After deployment, upload your data using:"
echo "1. Login to get your auth token"
echo "2. Upload staff data: POST /api/salon/upload/staff"
echo "3. Upload performance data: POST /api/salon/upload/performance" 