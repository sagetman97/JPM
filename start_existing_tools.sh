#!/bin/bash

echo "🚀 Starting Existing Portfolio Tools (Port 8000)..."
echo "================================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Please create one with your API keys."
    echo "Required variables:"
    echo "  - OPENAI_API_KEY"
    echo "  - QDRANT_HOST"
    echo "  - QDRANT_PORT"
    exit 1
fi

# Load environment variables
source .env

echo "✅ Environment variables loaded"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install existing backend dependencies
echo "📦 Installing existing backend dependencies..."
pip install -r backend/requirements.txt

# Start existing portfolio tools
echo "🚀 Starting portfolio tools on Port 8000..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 