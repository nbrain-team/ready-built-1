#!/bin/bash

# Script to upload salon data to deployed application

# Configuration
API_URL="${API_URL:-https://your-backend.onrender.com}"
TOKEN="${AUTH_TOKEN:-}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📊 Salon Data Upload Script"
echo "=========================="

# Check if API URL is set
if [ "$API_URL" == "https://your-backend.onrender.com" ]; then
    echo -e "${YELLOW}Please set your API URL:${NC}"
    echo "export API_URL=https://your-actual-backend.onrender.com"
    exit 1
fi

# Check if token is provided
if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}Please set your auth token:${NC}"
    echo "export AUTH_TOKEN=your_jwt_token_here"
    echo ""
    echo "To get a token:"
    echo "1. Login via the web app"
    echo "2. Check browser DevTools > Application > Local Storage > token"
    exit 1
fi

# Function to upload a file
upload_file() {
    local endpoint=$1
    local file=$2
    local description=$3
    
    echo -e "${YELLOW}Uploading ${description}...${NC}"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ File not found: $file${NC}"
        return 1
    fi
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "${API_URL}/api/salon/upload/${endpoint}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -F "file=@${file}")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Successfully uploaded ${description}${NC}"
        echo "Response: $body"
    else
        echo -e "${RED}❌ Failed to upload ${description}${NC}"
        echo "HTTP Code: $http_code"
        echo "Response: $body"
        return 1
    fi
    
    echo ""
}

# Upload staff data
echo "Step 1: Uploading Staff Data"
echo "----------------------------"
upload_file "staff" "blazer/Emp List Active as of 1.1.24-7.31.25.csv" "Employee List"

# Upload performance data
echo "Step 2: Uploading Performance Data"
echo "---------------------------------"
upload_file "performance" "blazer/Staff Performance_Utilization - All Salons 2025 072725.csv" "2025 Performance Data"
upload_file "performance" "blazer/Staff Performance_Utilization - All Salons 2024.csv" "2024 Performance Data"

echo -e "${GREEN}🎉 Data upload complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Visit ${API_URL/api/}/salon to see the dashboard"
echo "2. Use the AI chat to ask questions about your data"
echo "3. Check capacity utilization and staff predictions" 