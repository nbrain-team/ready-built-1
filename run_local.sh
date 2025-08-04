#!/bin/bash

echo "🚀 Starting nBrain Backend Locally (with Render Database)"
echo "=================================================="

# Navigate to backend directory
cd nbrain-2025/backend

# Load environment variables
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
    echo "✓ Loaded environment variables from .env.local"
else
    echo "❌ .env.local not found! Please create it first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the backend
echo ""
echo "🎯 Starting backend on http://localhost:8000"
echo "📊 Using Render database (same data as production)"
echo ""
echo "You can now:"
echo "1. Open another terminal for the frontend"
echo "2. Make changes to the backend code"
echo "3. The server will auto-reload on changes"
echo ""

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000 