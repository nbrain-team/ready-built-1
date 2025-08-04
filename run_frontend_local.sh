#!/bin/bash

echo "🎨 Starting nBrain Frontend Locally"
echo "==================================="

# Navigate to frontend directory
cd nbrain-2025/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "🌐 Starting frontend on http://localhost:5173"
echo "🔗 Connecting to backend at http://localhost:8000"
echo ""
echo "Make sure the backend is running in another terminal!"
echo ""

# Run the development server
npm run dev 