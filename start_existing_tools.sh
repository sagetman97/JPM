#!/bin/bash

echo "🚀 Starting Portfolio Tools (Port 8000)..."
echo "=========================================="

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Start portfolio tools
echo "🚀 Starting portfolio tools on Port 8000..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 