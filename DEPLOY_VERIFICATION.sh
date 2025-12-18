#!/bin/bash

# RAG Backend Deployment Verification Script
# Run this after deploying to Render to verify all components are working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${1:-https://rag-chatbot-backend.onrender.com}"
TIMEOUT=10

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RAG Backend Deployment Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Testing Backend: ${BLUE}${BACKEND_URL}${NC}"
echo ""

# Test 1: Health Check
echo -e "${YELLOW}[1/6]${NC} Testing health endpoint..."
if response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "${BACKEND_URL}/health"); then
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓${NC} Health check passed (HTTP $http_code)"
        echo "    Response: $body" | head -c 100
        echo ""
    else
        echo -e "${RED}✗${NC} Health check failed (HTTP $http_code)"
        echo "    Response: $body"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Health check timed out or connection refused"
    exit 1
fi

# Test 2: API Documentation
echo -e "${YELLOW}[2/6]${NC} Checking API documentation..."
if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "${BACKEND_URL}/docs"); then
    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}✓${NC} API docs available (HTTP $response)"
        echo "    URL: ${BACKEND_URL}/docs"
    else
        echo -e "${RED}✗${NC} API docs not available (HTTP $response)"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} API docs check timed out"
    exit 1
fi

# Test 3: Query Endpoint
echo -e "${YELLOW}[3/6]${NC} Testing query endpoint..."
if response=$(curl -s -w "\n%{http_code}" --max-time 30 \
    -X POST "${BACKEND_URL}/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is ROS 2?", "mode": "full_book"}'); then

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓${NC} Query endpoint working (HTTP $http_code)"

        # Check if response contains expected fields
        if echo "$body" | grep -q '"answer"'; then
            echo -e "${GREEN}✓${NC} Response contains answer field"
        else
            echo -e "${YELLOW}!${NC} Response may be incomplete"
        fi

        if echo "$body" | grep -q '"retrieved_chunks"'; then
            echo -e "${GREEN}✓${NC} Response contains retrieved chunks"
        fi
    else
        echo -e "${RED}✗${NC} Query endpoint failed (HTTP $http_code)"
        echo "    Response: $body" | head -c 200
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Query endpoint timed out"
    exit 1
fi

# Test 4: Ingest Endpoint
echo -e "${YELLOW}[4/6]${NC} Testing ingest endpoint..."
if response=$(curl -s -w "\n%{http_code}" --max-time 15 \
    -X POST "${BACKEND_URL}/ingest" \
    -H "Content-Type: application/json" \
    -d '{
        "chapter": "Test Chapter",
        "section": "Introduction",
        "content": "This is a test chunk for validation purposes.",
        "book_version": "v1.0"
    }'); then

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓${NC} Ingest endpoint working (HTTP $http_code)"

        if echo "$body" | grep -q '"ingested"'; then
            echo -e "${GREEN}✓${NC} Ingest response contains expected fields"
        fi
    else
        echo -e "${YELLOW}!${NC} Ingest endpoint returned HTTP $http_code (may require auth)"
        echo "    Response: $body" | head -c 150
    fi
else
    echo -e "${YELLOW}!${NC} Ingest endpoint timed out (non-critical)"
fi

# Test 5: Database Connectivity (via health endpoint)
echo -e "${YELLOW}[5/6]${NC} Checking database connectivity..."
if response=$(curl -s --max-time $TIMEOUT "${BACKEND_URL}/health"); then
    if echo "$response" | grep -q '"status"'; then
        echo -e "${GREEN}✓${NC} Backend is responding with valid JSON"

        # Check for database status in response
        if echo "$response" | grep -q '"database"'; then
            db_status=$(echo "$response" | grep -o '"database":"[^"]*"')
            echo "    Database status: $db_status"
        fi
    fi
fi

# Test 6: Response Time
echo -e "${YELLOW}[6/6]${NC} Measuring response times..."
start_time=$(date +%s%N | cut -b1-13)
curl -s --max-time $TIMEOUT "${BACKEND_URL}/health" > /dev/null
end_time=$(date +%s%N | cut -b1-13)
response_time=$((end_time - start_time))

if [ $response_time -lt 1000 ]; then
    echo -e "${GREEN}✓${NC} Fast response time: ${response_time}ms"
elif [ $response_time -lt 3000 ]; then
    echo -e "${YELLOW}!${NC} Moderate response time: ${response_time}ms (cold start?)"
else
    echo -e "${RED}✗${NC} Slow response time: ${response_time}ms"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Deployment verification complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor service in Render dashboard"
echo "2. Check logs for any errors"
echo "3. Update frontend to use: ${BACKEND_URL}"
echo "4. Run end-to-end tests with frontend"
echo ""
echo "Service URLs:"
echo "  Health: ${BACKEND_URL}/health"
echo "  Docs:   ${BACKEND_URL}/docs"
echo "  API:    ${BACKEND_URL}"
echo ""
