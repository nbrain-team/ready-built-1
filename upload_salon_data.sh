#!/bin/bash

# Salon Data Upload Script for nBrain Platform
# This script uploads Blazer salon data files to populate the database

echo "=== Salon Data Upload Script ==="
echo

# Configuration
API_URL="${API_URL:-https://nbrain-backend.onrender.com}"
API_TOKEN="${API_TOKEN:-}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}✗ File not found: $1${NC}"
        return 1
    fi
    return 0
}

# Function to upload a file
upload_file() {
    local file_path=$1
    local endpoint=$2
    local description=$3
    
    echo "Uploading $description..."
    
    if ! check_file "$file_path"; then
        return 1
    fi
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: Bearer $API_TOKEN" \
        -F "file=@$file_path" \
        "$API_URL/api/salon$endpoint")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Successfully uploaded $description${NC}"
        echo "  Response: $body"
        return 0
    else
        echo -e "${RED}✗ Failed to upload $description${NC}"
        echo "  HTTP Status: $http_code"
        echo "  Response: $body"
        return 1
    fi
}

# Check if we have an API token
if [ -z "$API_TOKEN" ]; then
    echo "No API_TOKEN found. Please set it first:"
    echo "export API_TOKEN='your-token-here'"
    echo
    echo "To get a token, you can use the login endpoint:"
    echo "curl -X POST $API_URL/login -d 'username=YOUR_EMAIL&password=YOUR_PASSWORD'"
    exit 1
fi

echo "API URL: $API_URL"
echo "Starting upload process..."
echo "----------------------------------------"

# Upload staff data
echo
echo "1. Staff Data Upload:"
upload_file "blazer/Emp List Active as of 1.1.24-7.31.25.csv" "/upload/staff" "Employee List"

# Upload performance data
echo
echo "2. Performance Data 2024:"
upload_file "blazer/Staff Performance_Utilization - All Salons 2024.csv" "/upload/performance" "2024 Performance Data"

echo
echo "3. Performance Data 2025:"
upload_file "blazer/Staff Performance_Utilization - All Salons 2025 072725.csv" "/upload/performance" "2025 Performance Data"

echo
echo "========================================"
echo "Upload process completed!"
echo
echo "Next steps:"
echo "1. Visit the dashboard: https://nbrain-frontend.onrender.com"
echo "2. Navigate to the Salon Analytics section"
echo "3. Use the AI Assistant to analyze your data"
echo
echo "Available analytics:"
echo "- Capacity utilization analysis"
echo "- Staff performance metrics"
echo "- Prebooking impact analysis"
echo "- Optimal scheduling recommendations" 