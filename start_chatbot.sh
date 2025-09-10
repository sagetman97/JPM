#!/bin/bash

echo "🚀 Starting Chatbot Service (Port 8001)..."
echo "=========================================="

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Start chatbot service
echo "🚀 Starting chatbot service on Port 8001..."
cd chatbot
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001 