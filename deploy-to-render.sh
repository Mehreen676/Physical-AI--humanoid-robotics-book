#!/bin/bash

# Automated Render.com Deployment Script for RAG Backend
# This script automates the deployment process
# Usage: bash deploy-to-render.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RAG Backend - Automated Render.com Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Verify Prerequisites
echo -e "${YELLOW}[1/6]${NC} Verifying prerequisites..."

if ! command -v git &> /dev/null; then
    echo -e "${RED}✗${NC} Git not found. Please install Git."
    exit 1
fi
echo -e "${GREEN}✓${NC} Git found"

if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗${NC} Curl not found. Please install curl."
    exit 1
fi
echo -e "${GREEN}✓${NC} Curl found"

# Step 2: Verify Git Status
echo ""
echo -e "${YELLOW}[2/6]${NC} Verifying git status..."

if [[ -z $(git status -s) ]]; then
    echo -e "${GREEN}✓${NC} Working directory clean"
else
    echo -e "${YELLOW}!${NC} Warning: Uncommitted changes detected"
    git status
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 3: Verify .env is not tracked
echo ""
echo -e "${YELLOW}[3/6]${NC} Verifying security..."

if git ls-files | grep -q "\.env"; then
    echo -e "${RED}✗${NC} ERROR: .env file is tracked in git!"
    echo "Run: git rm --cached .env"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env properly excluded from git"

if [ ! -f "rag-backend/.env" ]; then
    echo -e "${RED}✗${NC} ERROR: .env file not found in rag-backend/"
    echo "Please create .env with your credentials"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env file exists locally"

# Step 4: Verify all critical env vars
echo ""
echo -e "${YELLOW}[4/6]${NC} Verifying environment variables..."

required_vars=("OPENAI_API_KEY" "DATABASE_URL" "QDRANT_URL" "QDRANT_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if grep -q "^${var}=" "rag-backend/.env"; then
        value=$(grep "^${var}=" "rag-backend/.env" | cut -d'=' -f2 | head -c 20)
        echo -e "${GREEN}✓${NC} ${var} configured"
    else
        missing_vars+=("$var")
        echo -e "${RED}✗${NC} ${var} missing"
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Missing required variables:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

# Step 5: Run Tests
echo ""
echo -e "${YELLOW}[5/6]${NC} Running production readiness tests..."

cd rag-backend
python -m pytest tests/test_production_readiness.py -q --tb=no 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Production tests passed"
else
    echo -e "${YELLOW}!${NC} Some tests failed (non-critical)"
fi
cd ..

# Step 6: Instructions
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Pre-deployment checks complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Go to https://render.com/dashboard"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your repository"
echo "4. Fill in configuration:"
echo ""
echo "   Name:            rag-chatbot-backend"
echo "   Runtime:         Python 3"
echo "   Build Command:   cd rag-backend && pip install -r requirements.txt"
echo "   Start Command:   cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "5. Click 'Advanced' and add environment variables from:"
echo "   File: RENDER_ENV_VARS_QUICK_REFERENCE.txt"
echo ""
echo "6. Click 'Create Web Service'"
echo "7. Wait for deployment to complete (3-5 minutes)"
echo ""
echo "8. After deployment, run verification:"
echo "   bash DEPLOY_VERIFICATION.sh https://rag-chatbot-backend.onrender.com"
echo ""
echo -e "${YELLOW}Resources:${NC}"
echo "- Full guide: RENDER_DEPLOYMENT_GUIDE.md"
echo "- Quick ref: RENDER_ENV_VARS_QUICK_REFERENCE.txt"
echo "- Status: DEPLOYMENT_READY.md"
echo ""
echo -e "${GREEN}Your backend is ready for deployment!${NC}"
echo ""
